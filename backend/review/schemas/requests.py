from typing import Optional
from uuid import UUID
from ninja import Schema, FilterSchema
from django.db.models import Q
from utils.enums import DishCategoryEnum
from utils.schemas.fields import FilterField
from utils.functions.remove_accents import remove_accents

class CreateReviewSchema(Schema):
    """Schema tạo review cho dish"""
    dish_uid: UUID
    order_uid: UUID  # Order mà user đã mua dish này
    rating: int  # 1-5
    comment: Optional[str] = None
    attachment_uid: Optional[UUID] = None  # Hình ảnh đính kèm (optional)


class UpdateReviewSchema(Schema):
    """Schema update review - chỉ cho phép update rating và comment"""
    rating: Optional[int] = None
    comment: Optional[str] = None
    attachment_uid: Optional[UUID] = None


class CreateReviewReplySchema(Schema):
    """Schema tạo reply cho review - chỉ chef owner của dish"""
    content: str


class UpdateReviewReplySchema(Schema):
    """Schema update reply"""
    content: str

class FilterIssueReviewSchema(FilterSchema):
    dish_uid: Optional[UUID] = FilterField(default=None, description="Filter by dish uid")
    menu_uid: Optional[UUID] = FilterField(default=None, description="Filter by menu uid")
    search: Optional[str] = FilterField(default=None, description="Tìm kiếm theo tên món ăn")
    categories: Optional[str] = FilterField(
        default=None,
        description="Comma-separated list of categories",
        json_schema_extra={"enum": [value for value, _ in getattr(DishCategoryEnum, "choices")]},
    )

    def filter_dish_uid(self, value: Optional[UUID]):
        if value is None:
            return Q()
        return Q(dish__uid=value)

    def filter_menu_uid(self, value: Optional[UUID]):
        if value is None:
            return Q()
        return Q(dish__menudish_fk_dish__menu__uid=value)

    def filter_search(self, value: Optional[str]):
        if value is None:
            return Q()
        return Q(dish__name_no_accent__icontains=remove_accents(value))
    
    def filter_categories(self, value: Optional[str]):
        if value is None:
            return Q()
        return Q(dish__category__in=value.split(","))
    
class IssueReview(Schema):
    """Schema trả về review có issue để chef xem xét"""
    review_uid: UUID
    dish_name: str
    rating: int
    comment: Optional[str] = None
    issue: str
