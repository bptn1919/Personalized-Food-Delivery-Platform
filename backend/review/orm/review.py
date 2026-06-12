from datetime import timedelta
from typing import Optional
from uuid import UUID
from django.db.models import Count, Avg, Q, Sum, F, FloatField, ExpressionWrapper
from django.utils import timezone as dj_timezone
from review.models import Review, ReviewReply
from utils.types import TUser
from dish.models import Dish
from order.models import Order, OrderItem
from profile.models import ChefProfile
from review.schemas.requests import FilterIssueReviewSchema

class ReviewORM:       
    @staticmethod
    def create_review(user: TUser, review_data: dict, attachment=None) -> Review:
        """Tạo review cho dish"""
        return Review.objects.create(
            **review_data, 
            owner=user,
            attachment=attachment
        )

    @staticmethod
    def get_review_by_uid(uid: UUID) -> Optional[Review]:
        """Lấy review theo uid"""
        try:
            return Review.objects.select_related(
                'owner', 'dish', 'attachment', 'order', 'reply'
            ).get(uid=uid, deleted=False)
        except Review.DoesNotExist:
            return None

    @staticmethod
    def get_reviews_by_dish(
        *,
        dish_uid: UUID,
        rating: int | None = None,
        sort: str = "desc",
    ):
        qs = (
            Review.objects.filter(
                dish__uid=dish_uid,
                deleted=False,
            )
            .select_related("owner", "dish", "attachment", "reply__owner")
        )

        if rating is not None:
            qs = qs.filter(rating=rating)

        if sort == "asc":
            qs = qs.order_by("created_at")
        else:
            qs = qs.order_by("-created_at")

        return qs

    @staticmethod
    def get_reviews_by_user(user: TUser):
        """Lấy tất cả reviews của user"""
        return Review.objects.filter(
            owner=user, 
            deleted=False
        ).select_related('owner', 'dish', 'attachment', 'reply').order_by('-created_at')
    
    @staticmethod
    def get_user_issue_rows(user_id: int, days: int | None = None):
        """
        Lấy các review có issue của user (optimized cho recommendation)
        """
        query = Review.objects.filter(
            owner_id=user_id,
            deleted=False,
            issue__isnull=False
        ).exclude(issue="")

        if days:
            cutoff = dj_timezone.now() - timedelta(days=days)
            query = query.filter(created_at__gte=cutoff)

        return list(
            query.values("issue", "weight", "created_at")
        )

    @staticmethod
    def check_existing_review(user: TUser, dish_uid: UUID, order_uid: UUID) -> bool:
        """Kiểm tra user đã review dish trong order này chưa"""
        return Review.objects.filter(
            owner=user,
            dish__uid=dish_uid,
            order__uid=order_uid,
            deleted=False
        ).exists()

    @staticmethod
    def update_review(review: Review, rating: Optional[int] = None, 
                     comment: Optional[str] = None, attachment=None,
                     weight: Optional[float] = None, issue: Optional[str] = None):
        """Update review"""
        if rating is not None:
            review.rating = rating
        if comment is not None:
            review.comment = comment
        if attachment is not None:
            review.attachment = attachment
        if weight is not None:
            review.weight = weight
        if issue is not None:
            review.issue = issue
        
        update_fields = ['updated_at']
        if rating is not None:
            update_fields.append('rating')
        if comment is not None:
            update_fields.append('comment')
        if attachment is not None:
            update_fields.append('attachment')
        if weight is not None:
            update_fields.append('weight')
        if issue is not None:
            update_fields.append('issue')
        
        review.save(update_fields=update_fields)
        review.refresh_from_db()
        return review

    @staticmethod
    def soft_delete_review(uid: UUID) -> bool:
        """Soft delete review"""
        review = Review.objects.get(uid=uid, deleted=False)
        review.deleted = True
        review.save(update_fields=['deleted', 'updated_at'])
        return True

    @staticmethod
    def get_dish_rating_stats(dish_uid: UUID) -> dict:
        """Lấy thống kê rating của dish"""
        reviews = Review.objects.filter(dish__uid=dish_uid, deleted=False)
        weighted_score_expr = ExpressionWrapper(F('rating') * F('weight'), output_field=FloatField())
        
        # Calculate stats
        stats = reviews.aggregate(
            avg_rating=Avg('rating'),
            weighted_score_sum=Sum(weighted_score_expr),
            total_weight=Sum('weight'),
            total_reviews=Count('uid'),
        )
        total_weight = float(stats['total_weight'] or 0)
        weighted_score_sum = float(stats['weighted_score_sum'] or 0)
        final_score = round((weighted_score_sum / total_weight), 2) if total_weight > 0 else 0
        avg_rating = round(float(stats['avg_rating'] or 0), 2)
        
        # Rating distribution
        rating_dist = {}
        for i in range(1, 6):
            rating_dist[i] = reviews.filter(rating=i).count()
        
        return {
            'avg_rating': avg_rating,
            'final_score': final_score,
            'total_weight': total_weight,
            'total_reviews': stats['total_reviews'],
            'rating_distribution': rating_dist
        }

    @staticmethod
    def get_bulk_dish_rating_stats(dish_uids: list[str]) -> list[dict]:
        """Batch stats for many dishes (avg_rating, total_reviews)."""
        if not dish_uids:
            return []

        stats = (
            Review.objects.filter(dish__uid__in=dish_uids, deleted=False)
            .values("dish__uid")
            .annotate(
                avg_rating=Avg("rating"),
                total_reviews=Count("uid"),
            )
        )

        return [
            {
                "dish_uid": str(row["dish__uid"]),
                "avg_rating": float(row.get("avg_rating") or 0.0),
                "total_reviews": int(row.get("total_reviews") or 0),
            }
            for row in stats
        ]

    @staticmethod
    def check_dish_in_order(order, dish) -> bool:
        """Kiểm tra dish có trong order không"""
        return OrderItem.objects.filter(order=order, dish=dish).exists()

    @staticmethod
    def update_dish_scores(dish_uid: UUID, avg_rating: float, final_score: float):
        """Update avg_rating (trung bình sao) và final_score (weighted score) của dish."""
        dish = Dish.objects.get(uid=dish_uid)
        dish.avg_rating = avg_rating
        dish.final_score = final_score
        dish.save(update_fields=['avg_rating', 'final_score'])

    @staticmethod
    def get_chef_avg_rating_from_dishes(chef_id: int) -> float:
        """Tính rating chef dựa trên avg_rating của các dish có review"""
        stats = (
            Dish.objects
            .filter(owner_id=chef_id, deleted=False)
            .annotate(
                active_review_count=Count(
                    'review_fk_dish',
                    filter=Q(review_fk_dish__deleted=False),
                )
            )
            .filter(active_review_count__gt=0)
            .aggregate(chef_avg_rating=Avg('avg_rating'))
        )
        return float(stats['chef_avg_rating'] or 0)

    @staticmethod
    def update_chef_profile_rating(chef_id: int, rating: float) -> None:
        """Lưu rating đã tổng hợp cho chef profile"""
        ChefProfile.objects.filter(user_id=chef_id).update(rating=rating)

    @staticmethod
    def check_review_ownership(review, user: TUser) -> bool:
        """Kiểm tra review có thuộc về user không"""
        if not review.owner:
            return False
        owner_id = review.owner.id if hasattr(review.owner, 'id') else review.owner.pk
        user_id = user.id if hasattr(user, 'id') else user.pk
        return owner_id == user_id

    # ==================== Review Reply Operations ====================
    
    @staticmethod
    def create_review_reply(review, user: TUser, content: str) -> ReviewReply:
        """Tạo reply cho review"""
        return ReviewReply.objects.create(
            review=review,
            owner=user,
            content=content
        )

    @staticmethod
    def get_review_reply_by_review_uid(review_uid: UUID) -> Optional[ReviewReply]:
        """Lấy reply theo review uid"""
        try:
            return ReviewReply.objects.select_related('owner', 'review').get(
                review__uid=review_uid,
                deleted=False
            )
        except ReviewReply.DoesNotExist:
            return None

    @staticmethod
    def get_review_reply_by_uid(uid: UUID) -> Optional[ReviewReply]:
        """Lấy reply theo uid"""
        try:
            return ReviewReply.objects.select_related('owner', 'review').get(
                uid=uid,
                deleted=False
            )
        except ReviewReply.DoesNotExist:
            return None

    @staticmethod
    def check_reply_exists(review) -> bool:
        """Kiểm tra review đã có reply chưa"""
        return ReviewReply.objects.filter(review=review, deleted=False).exists()

    @staticmethod
    def update_review_reply(reply: ReviewReply, content: str) -> ReviewReply:
        """Update reply content"""
        reply.content = content
        reply.save(update_fields=['content', 'updated_at'])
        reply.refresh_from_db()
        return reply

    @staticmethod
    def soft_delete_review_reply(uid: UUID) -> bool:
        """Soft delete reply"""
        reply = ReviewReply.objects.get(uid=uid, deleted=False)
        reply.deleted = True
        reply.save(update_fields=['deleted', 'updated_at'])
        return True

    @staticmethod
    def check_dish_ownership(dish, user: TUser) -> bool:
        """Kiểm tra dish có thuộc về user (chef) không"""
        if not dish.owner:
            return False
        owner_id = dish.owner.id if hasattr(dish.owner, 'id') else dish.owner.pk
        user_id = user.id if hasattr(user, 'id') else user.pk
        return owner_id == user_id

    @staticmethod
    def get_chef_issue_stats(chef_id: int, start_at, end_at):
        """Lấy thống kê issue theo món của chef trong khoảng thời gian."""
        return (
            Review.objects.filter(
                dish__owner_id=chef_id,
                deleted=False,
                weight__gt=0,
                issue__isnull=False,
                created_at__gte=start_at,
                created_at__lt=end_at,
            )
            .exclude(issue="")
            .values('dish__uid', 'dish__name', 'issue')
            .annotate(count=Count('uid'))
            .order_by('dish__name', 'issue')
        )
    
    @staticmethod
    def get_reviews_from_issue(
        *,
        chef_id: int,
        issue: str,
        start_at,
        end_at,
        filter: Optional[FilterIssueReviewSchema] = None,
    ):
        qs = (
            Review.objects.filter(
                dish__owner_id=chef_id,
                deleted=False,
                weight__gt=0,
                issue__isnull=False,
                created_at__gte=start_at,
                created_at__lt=end_at,
            )
            .exclude(issue="")
            .filter(issue__icontains=issue)
            # 🚀 cực kỳ quan trọng để tránh N+1
            .select_related("dish", "owner", "attachment", "reply__owner")
            .order_by("dish__uid", "-created_at")
        )

        if filter:
            qs = qs.filter(filter.get_filter_expression())

        return qs