from typing import Optional
from uuid import UUID
from datetime import timedelta
import logging
import requests  # type: ignore
from django.db import transaction
from django.conf import settings
from django.utils import timezone

from attachment.services import AttachmentService
from order.models import OrderItem
from dish.services import DishService
from order.services import OrderService
from review.schemas.requests import CreateReviewSchema, UpdateReviewSchema, CreateReviewReplySchema, UpdateReviewReplySchema
from review.orm.review import ReviewORM
from dish.orm.dish import DishORM
from utils.types import TUser
from attachment.queries import Query as AttachmentQuery
from exceptions.attachments import AttachmentNotFound
from exceptions.reviews import (
    ReviewNotFoundException,
    DishNotOrderedException,
    DuplicateReviewException,
    OrderNotCompletedException,
    InvalidRatingException,
    ReviewReplyNotFoundException,
    ReviewReplyAlreadyExistsException,
    NotDishOwnerException,
    AIModelInvalidResponseException,
    AIModelUnavailableException,
)
from exceptions.dishes import DishNotFoundException
from exceptions.orders import OrderNotFoundException
from utils.enums import OrderStatusEnum

from .analytics import AnalyticsService


class ReviewService:
    def __init__(self):
        self.orm = ReviewORM()
        self.dish_orm = DishORM()  # Inject DishORM vào ReviewORM để reuse method get_dish_by_uid
        self.order_service = OrderService()
        self.dish_service = DishService()
        self.attachment_service = AttachmentService()
        self.logger = logging.getLogger(__name__)
    
    def create_review(self, user: TUser, payload: CreateReviewSchema):
        """Tạo review cho dish - user phải đã order dish đó và order đã completed"""
        
        # 1. Validate rating
        if payload.rating < 1 or payload.rating > 5:
            raise InvalidRatingException
        
        # 2. Check dish exists (using ORM)
        dish = self.dish_service.get_dish_by_uid(payload.dish_uid)
        
        # 3. Check order exists và thuộc về user (using OrderService)
        order = self.order_service.get_order_by_uid_not_transfer(payload.order_uid)
        
        # 4. Check order status = COMPLETED
        if order.status != OrderStatusEnum.COMPLETED:
            raise OrderNotCompletedException
        print("INPUT dish.uid:", dish.uid)

        print("order.uid:", order.uid)

        print(
            "All order_uids in DB:",
            list(
                OrderItem.objects
                .values_list("order_id", flat=True)
                .distinct()
            )
        )

        print(
            "DB dish_uids:",
            list(
                OrderItem.objects
                .filter(order_id=order.uid)
                .values_list("dish_id", flat=True)
            )
        )
        # 5. Check user đã order dish này trong order đó chưa (using ORM)
        self.order_service.check_dish_in_order(order=order, dish=dish)
        # 6. Check đã review chưa (using ORM)
        if self.orm.check_existing_review(user, payload.dish_uid, payload.order_uid):
            raise DuplicateReviewException
        
        # 7. Handle attachment nếu có
        attachment = None
        if payload.attachment_uid:
            self.attachment_service.handle_attachment(uid=payload.attachment_uid)
        
        user_id = user.id if hasattr(user, "id") else user.pk

        # 8. Create review
        ai_weight, ai_issue = self._predict_review_label(
            rating=payload.rating,
            comment=payload.comment,
            owner_id=user_id,
            dish_uid=payload.dish_uid,
            order_uid=payload.order_uid,
            created_at=timezone.now().isoformat(),
            updated_at=timezone.now().isoformat(),
            attachment_uid=payload.attachment_uid,
            deleted=False,
        )

        review_data = {
            'rating': payload.rating,
            'comment': payload.comment,
            'weight': ai_weight,
            'issue': ai_issue,
            'dish': dish,
            'order': order,
        }
        
        with transaction.atomic():
            review = self.orm.create_review(user=user, review_data=review_data, attachment=attachment)
            # Update dish avg_rating
            self._update_dish_avg_rating(payload.dish_uid)
            # Update chef rating from all rated dishes
            if dish.owner_id:
                self._update_chef_avg_rating(dish.owner_id)
        
        return review
    
    def get_review_by_uid(self, uid: UUID):
        """Lấy review theo uid"""
        review = self.orm.get_review_by_uid(uid=uid)
        if not review:
            raise ReviewNotFoundException
        return review
    
    def get_reviews_by_dish(
        self,
        *,
        dish_uid: UUID,
        rating: int | None = None,
        sort: str = "desc",
    ):
        # check dish tồn tại
        from dish.services import DishService
        DishService().get_dish_by_uid(dish_uid)

        return self.orm.get_reviews_by_dish(
            dish_uid=dish_uid,
            rating=rating,
            sort=sort,
        )
    def get_reviews_by_dish(
        self,
        *,
        dish_uid: UUID,
        rating: int | None = None,
        sort: str = "desc",
    ):
        from dish.services import DishService
        DishService().get_dish_by_uid(dish_uid)

        return self.orm.get_reviews_by_dish(
            dish_uid=dish_uid,
            rating=rating,
            sort=sort,
        )
    def get_reviews_by_user(self, user: TUser):
        """Lấy tất cả reviews của user"""
        return self.orm.get_reviews_by_user(user)
    
    def update_review(self, uid: UUID, user: TUser, payload: UpdateReviewSchema):
        """Update review - chỉ owner mới được update"""
        # Get review
        review = self.get_review_by_uid(uid)
        
        # Check ownership (using ORM)
        if not self.orm.check_review_ownership(review, user):
            from utils.exceptions import PermissionDeniedError
            raise PermissionDeniedError("Bạn chỉ có thể update review của mình")
        
        # Validate rating nếu có update
        if payload.rating is not None and (payload.rating < 1 or payload.rating > 5):
            raise InvalidRatingException
        
        # Handle attachment nếu có
        attachment = None
        if payload.attachment_uid:
            self.attachment_service.handle_attachment(uid=payload.attachment_uid)
        
        user_id = user.id if hasattr(user, "id") else user.pk
        current_rating = payload.rating if payload.rating is not None else review.rating
        current_comment = payload.comment if payload.comment is not None else review.comment
        ai_weight, ai_issue = self._predict_review_label(
            rating=current_rating,
            comment=current_comment,
            owner_id=user_id,
            dish_uid=review.dish.uid,
            order_uid=review.order.uid if review.order else None,
            review_uid=review.uid,
            created_at=review.created_at.isoformat() if review.created_at else timezone.now().isoformat(),
            updated_at=timezone.now().isoformat(),
            attachment_uid=payload.attachment_uid if payload.attachment_uid is not None else (review.attachment.uid if review.attachment else None),
            deleted=review.deleted,
        )

        with transaction.atomic():
            updated_review = self.orm.update_review(
                review=review,
                rating=payload.rating,
                comment=payload.comment,
                attachment=attachment,
                weight=ai_weight,
                issue=ai_issue,
            )

            # Luôn cập nhật weighted score vì weight có thể thay đổi khi comment đổi.
            self._update_dish_avg_rating(review.dish.uid)
            if review.dish.owner_id:
                self._update_chef_avg_rating(review.dish.owner_id)
        
        return updated_review
    
    def delete_review(self, uid: UUID, user: TUser):
        """Soft delete review - chỉ owner mới được xóa"""
        # Get review
        review = self.get_review_by_uid(uid)
        
        # Check ownership (using ORM)
        if not self.orm.check_review_ownership(review, user):
            from utils.exceptions import PermissionDeniedError
            raise PermissionDeniedError("Bạn chỉ có thể xóa review của mình")
        
        with transaction.atomic():
            result = self.orm.soft_delete_review(uid)
            # Update dish avg_rating
            self._update_dish_avg_rating(review.dish.uid)
            if review.dish.owner_id:
                self._update_chef_avg_rating(review.dish.owner_id)
        
        return result
    
    def get_dish_rating_stats(self, dish_uid: UUID):
        """Lấy thống kê rating của dish"""
        # Check dish exists (using ORM)
        dish = self.dish_orm.get_dish_by_uid(dish_uid)
        if not dish:
            raise DishNotFoundException
        
        return self.orm.get_dish_rating_stats(dish_uid)
    
    def _update_dish_avg_rating(self, dish_uid: UUID):
        """Internal method để update public avg và private final score của dish."""
        stats = self.orm.get_dish_rating_stats(dish_uid)
        self.orm.update_dish_scores(
            dish_uid,
            stats['avg_rating'],
            stats['final_score'],
        )

    def _update_chef_avg_rating(self, chef_id: int):
        """Internal method để update rating của chef từ các dish đã có review"""
        chef_avg_rating = self.orm.get_chef_avg_rating_from_dishes(chef_id)
        self.orm.update_chef_profile_rating(chef_id, chef_avg_rating)

    def _predict_review_label(
        self,
        rating: int,
        comment: Optional[str],
        owner_id: Optional[int],
        dish_uid: UUID,
        order_uid: Optional[UUID],
        review_uid: Optional[UUID] = None,
        created_at: Optional[str] = None,
        updated_at: Optional[str] = None,
        attachment_uid: Optional[UUID] = None,
        deleted: bool = False,
    ) -> tuple[float, Optional[str]]:
        """Gọi AI model để suy luận weight/issue cho review."""
        if not comment:
            return 0.0, None

        endpoint = f"{settings.AI_MODEL_BASE_URL.rstrip('/')}/predict"
        request_payload = {
            "uid": str(review_uid or UUID(int=0)),
            "created_at": created_at,
            "updated_at": updated_at,
            "rating": rating,
            "comment": comment,
            "deleted": deleted,
            "attachment_uid": str(attachment_uid) if attachment_uid else "",
            "weight": 0,
            "issue": None,
            "dish_uid": str(dish_uid),
            "order_uid": str(order_uid) if order_uid else "",
            "owner_id": owner_id,
        }

        try:
            response = requests.post(
                endpoint,
                json=request_payload,
                timeout=settings.AI_MODEL_TIMEOUT_SECONDS,
            )
            response.raise_for_status()
            data = response.json()
        except requests.RequestException as exc:
            self.logger.warning(
                "AI model unavailable, fallback to default label. endpoint=%s error=%s",
                endpoint,
                exc,
            )
            print(f"[AI] AI khong chay hoac timeout. Fallback weight=0.0, issue=None. endpoint={endpoint} error={exc}")
            return 0.0, None
        except ValueError as exc:
            self.logger.warning(
                "AI model returned non-JSON response, fallback to default label. endpoint=%s error=%s",
                endpoint,
                exc,
            )
            print(f"[AI] AI tra ve JSON khong hop le. Fallback weight=0.0, issue=None. endpoint={endpoint} error={exc}")
            return 0.0, None

        if not isinstance(data, dict):
            self.logger.warning("AI model returned invalid payload type=%s, fallback to default label.", type(data))
            print(f"[AI] AI tra ve payload khong hop le ({type(data)}). Fallback weight=0.0, issue=None.")
            return 0.0, None

        weight = data.get("weight", 0)
        issue = data.get("issue")
        try:
            normalized_weight = float(weight)
        except (TypeError, ValueError):
            self.logger.warning("AI model returned invalid weight=%s, fallback to default label.", weight)
            print(f"[AI] AI tra ve weight khong hop le ({weight}). Fallback weight=0.0, issue=None.")
            return 0.0, None

        if not isinstance(issue, (str, type(None))):
            self.logger.warning("AI model returned invalid issue type=%s, fallback to null issue.", type(issue))
            issue = None

        return normalized_weight, issue

    def get_chef_issue_report(self, user: TUser):
        """Report issue theo từng món cho 14 ngày gần nhất, chia 2 tuần."""
        user_id = user.id if hasattr(user, "id") else user.pk
        now = timezone.now()
        this_week_start = now - timedelta(days=7)
        previous_week_start = now - timedelta(days=14)

        this_week_rows = self.orm.get_chef_issue_stats(
            chef_id=user_id,
            start_at=this_week_start,
            end_at=now,
        )
        previous_week_rows = self.orm.get_chef_issue_stats(
            chef_id=user_id,
            start_at=previous_week_start,
            end_at=this_week_start,
        )

        reports_map: dict[str, dict] = {}

        def ensure_dish(dish_uid, dish_name):
            key = str(dish_uid)
            if key not in reports_map:
                reports_map[key] = {
                    "dish_uid": dish_uid,
                    "dish_name": dish_name,
                    "this_week": {},
                    "last_week": {},
                }
            return reports_map[key]

        for row in this_week_rows:
            dish_item = ensure_dish(row["dish__uid"], row["dish__name"])
            dish_item["this_week"][row["issue"]] = row["count"]

        for row in previous_week_rows:
            dish_item = ensure_dish(row["dish__uid"], row["dish__name"])
            dish_item["last_week"][row["issue"]] = row["count"]

        reports = []
        for item in sorted(reports_map.values(), key=lambda x: x["dish_name"].lower()):
            this_week_issues = item["this_week"]
            last_week_issues = item["last_week"]
            reports.append(
                {
                    "dish_uid": item["dish_uid"],
                    "dish_name": item["dish_name"],
                    "this_week": {
                        "has_issue": bool(this_week_issues),
                        "total_issues": int(sum(this_week_issues.values())),
                        "issues": this_week_issues,
                    },
                    "last_week": {
                        "has_issue": bool(last_week_issues),
                        "total_issues": int(sum(last_week_issues.values())),
                        "issues": last_week_issues,
                    },
                }
            )

        return {
            "range_start": previous_week_start,
            "range_end": now,
            "week_split_at": this_week_start,
            "reports": reports,
        }



    # ==================== Review Reply Methods ====================
    
    def create_review_reply(self, review_uid: UUID, user: TUser, payload: CreateReviewReplySchema):
        """Tạo reply cho review - chỉ chef owner của dish mới được reply"""
        
        # 1. Get review
        review = self.get_review_by_uid(review_uid)
        
        # 2. Check chef là owner của dish (using ORM)
        if not self.orm.check_dish_ownership(review.dish, user):
            raise NotDishOwnerException
        
        # 3. Check review đã có reply chưa (using ORM)
        if self.orm.check_reply_exists(review):
            raise ReviewReplyAlreadyExistsException
        
        # 4. Create reply (using ORM)
        return self.orm.create_review_reply(review=review, user=user, content=payload.content)
    
    def get_review_reply_by_review_uid(self, review_uid: UUID):
        """Lấy reply của một review"""
        reply = self.orm.get_review_reply_by_review_uid(review_uid)
        if not reply:
            raise ReviewReplyNotFoundException
        return reply
    
    def update_review_reply(self, reply_uid: UUID, user: TUser, payload: UpdateReviewReplySchema):
        """Update reply - chỉ owner của reply (chef) mới được update"""
        
        # 1. Get reply (using ORM)
        reply = self.orm.get_review_reply_by_uid(reply_uid)
        if not reply:
            raise ReviewReplyNotFoundException
        
        # 2. Check ownership (using ORM)
        if not self.orm.check_dish_ownership(reply.review.dish, user):
            from utils.exceptions import PermissionDeniedError
            raise PermissionDeniedError("Bạn chỉ có thể update reply của mình")
        
        # 3. Update reply (using ORM)
        return self.orm.update_review_reply(reply=reply, content=payload.content)
    
    def delete_review_reply(self, reply_uid: UUID, user: TUser):
        """Xóa reply - chỉ owner của reply (chef) mới được xóa"""
        
        # 1. Get reply (using ORM)
        reply = self.orm.get_review_reply_by_uid(reply_uid)
        if not reply:
            raise ReviewReplyNotFoundException
        
        # 2. Check ownership (using ORM)
        if not self.orm.check_dish_ownership(reply.review.dish, user):
            from utils.exceptions import PermissionDeniedError
            raise PermissionDeniedError("Bạn chỉ có thể xóa reply của mình")
        
        # 3. Delete reply (using ORM)
        return self.orm.soft_delete_review_reply(reply_uid)


    __all__ = ["ReviewService", "AnalyticsService"]
