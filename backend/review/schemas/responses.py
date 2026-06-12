from typing import Optional
from uuid import UUID
from datetime import date, datetime
from ninja import ModelSchema, Schema
from review.models import Review, ReviewReply


class ReviewOwnerSchema(Schema):
    """Schema cho owner info trong review response"""
    id: int
    email: str
    username: Optional[str] = None
    full_name: Optional[str] = None


class ReviewDishSchema(Schema):
    """Schema cho dish info trong review response"""
    uid: UUID
    name: str
    category: str
    price: float


class ReviewReplyResponse(ModelSchema):
    owner_info: Optional[ReviewOwnerSchema] = None

    class Meta:
        model = ReviewReply
        fields = [
            "uid",
            "content",
            "created_at",
            "updated_at",
        ]

    @staticmethod
    def resolve_owner_info(obj):
        if obj.owner:
            user = obj.owner
            return {
                "id": user.id if hasattr(user, "id") else user.pk,
                "email": user.email,
                "username": getattr(user, "username", None),
                "full_name": (
                    getattr(user, "display_name", None)
                    or user.get_full_name()
                    or user.email
                ),
            }
        return None
    
    @staticmethod
    def resolve_owner_info(obj):
        if obj.owner:
            return {
                "id": obj.owner.id if hasattr(obj.owner, 'id') else obj.owner.pk,
                "email": obj.owner.email,
                "username": getattr(obj.owner, 'username', None),
                "full_name": obj.owner.get_full_name(),
            }
        return None

class ReviewDetailResponse(ModelSchema):
    owner_info: Optional[ReviewOwnerSchema] = None
    attachment_url: Optional[str] = None
    reply: Optional[ReviewReplyResponse] = None
    
    class Meta:
        model = Review
        fields = [
            "uid",
            "rating",
            "comment",
            "issue",
            "created_at",
            "updated_at",
        ]
    
    @staticmethod
    def resolve_owner_info(obj):
        if obj.owner:
            return {
                "id": obj.owner.id if hasattr(obj.owner, 'id') else obj.owner.pk,
                "email": obj.owner.email,
                "username": getattr(obj.owner, 'username', None),
                "full_name": obj.owner.get_full_name(),
            }
        return None
    
    @staticmethod
    def resolve_attachment_url(obj):
        return obj.attachment.public_url if obj.attachment else None
    
    @staticmethod
    def resolve_reply(obj):
        """Get reply if exists"""
        try:
            if hasattr(obj, 'reply') and obj.reply and not obj.reply.deleted:
                return ReviewReplyResponse.from_orm(obj.reply)
        except:
            pass
        return None
    
class ReviewOfDishRespone(Schema):
    dish_info: ReviewDishSchema
    reviews: list[ReviewDetailResponse]

class ReviewResponse(ModelSchema):
    """Response schema for review với thông tin owner và dish"""
    owner_info: Optional[ReviewOwnerSchema] = None
    dish_info: Optional[ReviewDishSchema] = None
    attachment_url: Optional[str] = None
    reply: Optional[ReviewReplyResponse] = None
    
    class Meta:
        model = Review
        fields = [
            "uid",
            "rating",
            "comment",
            "issue",
            "created_at",
            "updated_at",
        ]
    
    @staticmethod
    def resolve_owner_info(obj):
        if obj.owner:
            return {
                "id": obj.owner.id if hasattr(obj.owner, 'id') else obj.owner.pk,
                "email": obj.owner.email,
                "username": getattr(obj.owner, 'username', None),
                "full_name": obj.owner.get_full_name() if obj.owner.get_full_name() else None,
            }
        return None
    
    @staticmethod
    def resolve_dish_info(obj):
        if obj.dish:
            return {
                "uid": obj.dish.uid,
                "name": obj.dish.name,
                "category": obj.dish.category,
                "price": float(obj.dish.price),
            }
        return None
    
    @staticmethod
    def resolve_attachment_url(obj):
        return obj.attachment.public_url if obj.attachment else None
    
    @staticmethod
    def resolve_reply(obj):
        """Get reply if exists"""
        try:
            if hasattr(obj, 'reply') and obj.reply and not obj.reply.deleted:
                return ReviewReplyResponse.from_orm(obj.reply)
        except:
            pass
        return None


class DishRatingStatsSchema(Schema):
    """Statistics về rating của một dish"""
    avg_rating: float
    total_reviews: int
    rating_distribution: dict  # {1: count, 2: count, ...}


class DishIssueWindowSchema(Schema):
    has_issue: bool
    total_issues: int
    issues: dict[str, int]


class ChefDishIssueReportSchema(Schema):
    dish_uid: UUID
    dish_name: str
    this_week: DishIssueWindowSchema
    last_week: DishIssueWindowSchema


class ChefIssueReportResponse(Schema):
    range_start: datetime
    range_end: datetime
    week_split_at: datetime
    reports: list[ChefDishIssueReportSchema]


class IssueTrendPointSchema(Schema):
    date: date
    count: int


class IssueTrendResponse(Schema):
    range_start: date
    range_end: date
    issues: dict[str, list[IssueTrendPointSchema]]


class TopComplainedDishSchema(Schema):
    dish_uid: UUID
    dish_name: str
    count: int


class TopComplainedDishesResponse(Schema):
    range_start: date
    range_end: date
    limit: int
    items: list[TopComplainedDishSchema]


class IssueHeatmapResponse(Schema):
    range_start: date
    range_end: date
    heatmap: dict[str, dict[str, int]]

class IssueReviewsResponse(Schema):
    range_start: date
    range_end: date
    issue: str
    total_reviews: int
    reviews: list[ReviewOfDishRespone]