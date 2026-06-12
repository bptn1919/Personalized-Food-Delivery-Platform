from typing import Literal, Optional
from uuid import UUID

from django.db.models import Q
from ninja import FilterSchema, ModelSchema, Schema

from ingredient.models import Ingredient
from utils.enums import IngredientCategoryEnum
from utils.functions.remove_accents import remove_accents
from utils.schemas.fields import FilterField, OrderBySchema


class IngredientSchema(ModelSchema):
    category: IngredientCategoryEnum

    class Meta:
        model = Ingredient
        exclude = [
            "attachment",
            "created_at",
            "deleted",
            "name_no_accent",
            "owner",
            "uid",
            "updated_at",
            "updater",
        ]


class FilterCategoryIngredientSchema(FilterSchema):
    categories: Optional[str] = FilterField(
        default=None,
        description="Comma-separated list of categories",
        json_schema_extra={"enum": [value for value, _ in getattr(IngredientCategoryEnum, "choices")]},
    )

    def filter_categories(self, value: Optional[str]):
        if value is None:
            return Q()
        return Q(category__in=value.split(","))
    
class FilterIngredientSchema(FilterSchema):
    search: Optional[str] = FilterField(default=None)
    categories: Optional[str] = FilterField(
        default=None,
        description="Comma-separated list of categories",
        json_schema_extra={"enum": [value for value, _ in getattr(IngredientCategoryEnum, "choices")]},
    )

    def filter_search(self, value: Optional[str]):
        if value is None:
            return Q()
        return Q(name_no_accent__icontains=remove_accents(value))

    def filter_categories(self, value: Optional[str]):
        if value is None:
            return Q()
        return Q(category__in=value.split(","))

class OrderByIngredientSchema(OrderBySchema):
    order_by: Literal["energy", "updated_at"] = "updated_at"


class IngredientSearchSchema(FilterSchema):
    query: Optional[str] = FilterField(default=None)
    # Legacy hard-cap for search result count. Prefer page/page_size via @paginate.
    limit: int = FilterField(default=100)


class IngredientAliasCreateSchema(Schema):
    ingredient_uid: UUID
    alias: str

class IngredientSuggestionResolveSchema(Schema):
    ingredient_uid: Optional[UUID] = None
    suggested_category: Optional[IngredientCategoryEnum] = None
    resolution_note: Optional[str] = None


class IngredientSuggestionApproveNewSchema(Schema):
    resolution_note: Optional[str] = None


class IngredientSuggestionApproveAliasSchema(Schema):
    ingredient_uid: UUID
    resolution_note: Optional[str] = None


class IngredientSuggestionRejectSchema(Schema):
    rejection_reason: str


class IngredientSuggestionFilterSchema(FilterSchema):
    search: Optional[str] = FilterField(default=None)
    status: Optional[str] = FilterField(default=None)
    category: Optional[IngredientCategoryEnum] = FilterField(default=None)


class IngredientSuggestionOrderBySchema(OrderBySchema):
    order_by: Literal["created_at", "updated_at", "verified_at"] = "created_at"


class UserIngredientPreferenceSchema(Schema):
    ingredient_uid: UUID
