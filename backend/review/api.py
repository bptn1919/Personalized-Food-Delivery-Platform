from uuid import UUID
from datetime import date

from ninja import Query

from utils.router.authenticate import AuthBear
from utils.router.controller import Controller, api, get, patch, post, delete
from utils.router.paginate import paginate
from utils.types import AuthenticatedRequest
from utils.exceptions import PermissionDeniedError
from exceptions.reviews import ReviewNotFoundException, ReviewReplyNotFoundException
from exceptions.dishes import DishNotFoundException
from exceptions.menus import MenuDoesNotExist
from review.models import Review
from exceptions.reviews import AIModelUnavailableException, AIModelInvalidResponseException
from typing import List
from .schemas.requests import CreateReviewSchema, UpdateReviewSchema, FilterIssueReviewSchema, CreateReviewReplySchema, UpdateReviewReplySchema
from .schemas.responses import (
    IssueReviewsResponse,
    ReviewResponse,
    DishRatingStatsSchema,
    ReviewReplyResponse,
    ChefIssueReportResponse,
    IssueTrendResponse,
    TopComplainedDishesResponse,
    IssueHeatmapResponse,
    ReviewDetailResponse,
    ReviewOfDishRespone,
)
from .services import ReviewService, AnalyticsService


@api(prefix_or_class="reviews", tags=["Review"], auth=AuthBear())
class ReviewController(Controller):
    def __init__(self, service: ReviewService) -> None:
        self.service: ReviewService = service

    @post("/", response=ReviewResponse, exceptions=(PermissionDeniedError, AIModelUnavailableException, AIModelInvalidResponseException))
    def create_review(self, request: AuthenticatedRequest, payload: CreateReviewSchema):
        """Customer tạo review cho dish sau khi đã order và order đã completed
        
        Business rules:
        - User phải đã order dish này
        - Order phải ở trạng thái COMPLETED
        - Mỗi user chỉ được review 1 lần cho mỗi dish trong 1 order
        - Rating từ 1-5 sao
        - Có thể đính kèm attachment (upload qua presigned URL trước)
        """
        return self.service.create_review(user=request.user, payload=payload)
    
    @get("/my-reviews", auth=True, response=ReviewResponse, paginate=True)
    @paginate
    def get_my_reviews(self, request: AuthenticatedRequest):
        """Lấy tất cả reviews của user hiện đang login"""
        return self.service.get_reviews_by_user(user=request.user)

    @get("/chef/issue-report", auth=True, response=ChefIssueReportResponse)
    def get_chef_issue_report(self, request: AuthenticatedRequest):
        """Tổng hợp issue 14 ngày gần nhất của các món thuộc chef hiện tại, chia 2 tuần."""
        return self.service.get_chef_issue_report(user=request.user)
    from utils.router.paginate import PaginatedResponseSchema
    @get(
        "/dish/{dish_uid}",
        auth=False,
        response=PaginatedResponseSchema[ReviewDetailResponse])
    @paginate
    def get_reviews_by_dish(
        self,
        dish_uid: UUID,
        rating: int | None = Query(None, ge=1, le=5),
        sort: str = Query("desc", enum=["asc", "desc"]),
    ):
        return self.service.get_reviews_by_dish(
            dish_uid=dish_uid,
            rating=rating,
            sort=sort,
        )
    
    @get("/dish/{dish_uid}/stats", auth=False, response=DishRatingStatsSchema)
    def get_dish_rating_stats(self, dish_uid: UUID):
        """Lấy thống kê rating của dish - PUBLIC"""
        return self.service.get_dish_rating_stats(dish_uid=dish_uid)

    # ==================== Review Reply Endpoints ====================
    
    @post("/{review_uid}/reply", response=ReviewReplyResponse, exceptions=(PermissionDeniedError, ReviewNotFoundException))
    def create_review_reply(self, request: AuthenticatedRequest, review_uid: UUID, payload: CreateReviewReplySchema):
        """Chef tạo reply cho review của customer
        
        Business rules:
        - Chỉ chef owner của dish mới có quyền reply
        - Mỗi review chỉ có thể có 1 reply
        """
        return self.service.create_review_reply(review_uid=review_uid, user=request.user, payload=payload)
    
    @get("/{review_uid}/reply", response=ReviewReplyResponse, exceptions=(ReviewReplyNotFoundException,))
    def get_review_reply(self, review_uid: UUID):
        """Lấy reply của một review"""
        return self.service.get_review_reply_by_review_uid(review_uid=review_uid)
    
    @patch("/reply/{reply_uid}", response=ReviewReplyResponse, exceptions=(PermissionDeniedError, ReviewReplyNotFoundException))
    def update_review_reply(self, request: AuthenticatedRequest, reply_uid: UUID, payload: UpdateReviewReplySchema):
        """Update reply - chỉ chef owner có quyền update"""
        return self.service.update_review_reply(reply_uid=reply_uid, user=request.user, payload=payload)
    
    @delete("/reply/{reply_uid}", response=dict, exceptions=(PermissionDeniedError, ReviewReplyNotFoundException))
    def delete_review_reply(self, request: AuthenticatedRequest, reply_uid: UUID):
        """Xóa reply - chỉ chef owner có quyền xóa"""
        result = self.service.delete_review_reply(reply_uid=reply_uid, user=request.user)
        return {"success": result, "message": "Reply đã được xóa thành công"}

    @get("/{uid}", response=ReviewResponse, exceptions=(ReviewNotFoundException,))
    def get_review_by_uid(self, request: AuthenticatedRequest, uid: UUID):
        """Lấy thông tin chi tiết một review"""
        return self.service.get_review_by_uid(uid=uid)
    
    @patch("/{uid}", response=ReviewResponse, exceptions=(PermissionDeniedError, ReviewNotFoundException, AIModelUnavailableException, AIModelInvalidResponseException))
    def update_review(self, request: AuthenticatedRequest, uid: UUID, payload: UpdateReviewSchema):
        """Update review của mình - chỉ owner có quyền update
        
        Có thể update:
        - rating
        - comment
        - attachment (upload mới qua presigned URL)
        """
        return self.service.update_review(uid=uid, user=request.user, payload=payload)
    
    @delete("/{uid}", response=dict, exceptions=(PermissionDeniedError, ReviewNotFoundException))
    def delete_review(self, request: AuthenticatedRequest, uid: UUID):
        """Soft delete review của mình - chỉ owner có quyền xóa"""
        result = self.service.delete_review(uid=uid, user=request.user)
        return {"success": result, "message": "Review đã được xóa thành công"}


@api(prefix_or_class="reviews", tags=["Review Analytics"], auth=AuthBear())
class ReviewAnalyticsController(Controller):
    def __init__(self, service: AnalyticsService) -> None:
        self.analytics_service: AnalyticsService = service

    @get("/chef/analytics/issue-trend", auth=True, response=IssueTrendResponse)
    def issue_trend(
        self,
        request: AuthenticatedRequest,
        range_start: date | None = Query(None),
        range_end: date | None = Query(None),
    ):
        """Biểu đồ issue theo thời gian cho chef."""
        return self.analytics_service.issue_trend(user=request.user, range_start=range_start, range_end=range_end)

    @get("/chef/analytics/top-complained-dishes", auth=True, response=TopComplainedDishesResponse)
    def top_complained_dishes(
        self,
        request: AuthenticatedRequest,
        range_start: date | None = Query(None),
        range_end: date | None = Query(None),
        limit: int | None = Query(None, ge=1, le=50),
    ):
        """Top món bị complain nhiều nhất cho chef."""
        return self.analytics_service.top_complained_dishes(
            user=request.user,
            range_start=range_start,
            range_end=range_end,
            limit=limit,
        )

    @get("/chef/analytics/issue-heatmap", auth=True, response=IssueHeatmapResponse)
    def issue_heatmap(
        self,
        request: AuthenticatedRequest,
        range_start: date | None = Query(None),
        range_end: date | None = Query(None),
    ):
        """Heatmap vấn đề theo món và issue cho chef."""
        return self.analytics_service.issue_heatmap(user=request.user, range_start=range_start, range_end=range_end)

    @get("/chef/issue-reviews", response=IssueReviewsResponse, auth=True)
    def chef_issue_reviews(
        self,
        request: AuthenticatedRequest,
        issue: str,
        filter: FilterIssueReviewSchema = Query(...),
        range_start: date | None = Query(None),
        range_end: date | None = Query(None),
    ):
        return self.analytics_service.get_reviews_by_issue_for_chef(
            user=request.user,
            issue=issue,
            filter=filter,
            range_start=range_start,
            range_end=range_end,
        )
    
