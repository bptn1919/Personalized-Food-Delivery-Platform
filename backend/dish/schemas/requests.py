from typing import Literal, Optional

from django.db.models import Q
from ninja import Field, FilterSchema, ModelSchema

from dish.models import Dish, DishAvailability, DishIngredient
from utils.enums import DishCategoryEnum, DishLocationTypeEnum, IngredientCategoryEnum, IngredientSourceEnum
from utils.functions.remove_accents import remove_accents
from utils.schemas.fields import FilterField
from uuid import UUID
from ninja import Schema
from decimal import Decimal

class DishSchema(ModelSchema):
    category: DishCategoryEnum

    class Meta:
        model = Dish
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


class DishWithAttachmentSchema(Schema):
    """Schema cho tạo dish với attachment_uid (sau khi upload qua presigned URL)"""
    name: str
    category: DishCategoryEnum
    description: Optional[str] = None
    price: Decimal = Field(gt=0, max_digits=12, decimal_places=2)
    status: str = "AVAILABLE"
    attachment_uid: UUID
    location_id: Optional[int] = None


class DishUpdateSchema(Schema):
    name: Optional[str] = None
    category: Optional[DishCategoryEnum] = None
    description: Optional[str] = None
    price: Optional[Decimal] = Field(None, gt=0, max_digits=12, decimal_places=2)
    status: Optional[str] = None
    attachment_uid: Optional[UUID] = None
    location_id: Optional[int] = None


class DishLocationCreateSchema(Schema):
    name: str
    type: DishLocationTypeEnum
    parent_id: Optional[int] = None


class DishLocationUpdateSchema(Schema):
    name: Optional[str] = None
    type: Optional[DishLocationTypeEnum] = None
    parent_id: Optional[int] = None

class FilterDishSchema(FilterSchema):
    chef_id: Optional[int] = FilterField(default=None, description="Filter by chef id")
    location_id: Optional[int] = FilterField(default=None, description="Filter by location id")
    search: Optional[str] = FilterField(default=None)
    categories: Optional[str] = FilterField(
        default=None,
        description="Comma-separated list of categories",
        json_schema_extra={"enum": [value for value, _ in getattr(DishCategoryEnum, "choices")]},
    )

    def filter_chef_id(self, value: Optional[int]):
        if value is None:
            return Q()
        return Q(owner_id=value)

    def filter_location_id(self, value: Optional[int]):
        if value is None:
            return Q()

        return (
            Q(location_id=value) |
            Q(location__parent_id=value) |
            Q(location__parent__parent_id=value)
        )

    def filter_search(self, value: Optional[str]):
        if value is None:
            return Q()
        return Q(name_no_accent__icontains=remove_accents(value))

    def filter_categories(self, value: Optional[str]):
        if value is None:
            return Q()
        return Q(category__in=value.split(","))

class DishIngredientSchema(Schema):
    ingredient_uid: Optional[UUID] = None
    custom_name: Optional[str] = None
    source: Optional[IngredientSourceEnum] = None
    weight: float
    energy: Optional[float] = None
    protein: Optional[float] = None
    lipid: Optional[float] = None
    carbohydrate: Optional[float] = None
    fiber: Optional[float] = None
    natri: Optional[float] = None
    kali: Optional[float] = None
    cholesterol: Optional[float] = None
    retinol: Optional[float] = None
    caroten: Optional[float] = None
    vitamin_b_1: Optional[float] = None
    vitamin_b_2: Optional[float] = None
    vitamin_pp: Optional[float] = None
    vitamin_c: Optional[float] = None
    calcium: Optional[float] = None
    phosphorus: Optional[float] = None
    fe: Optional[float] = None
    mg: Optional[float] = None
    zn: Optional[float] = None


class DishIngredientCreateSchema(Schema):
    ingredient_uid: Optional[UUID] = None
    weight: float
    energy: Optional[float] = None
    protein: Optional[float] = None
    lipid: Optional[float] = None
    carbohydrate: Optional[float] = None
    fiber: Optional[float] = None
    natri: Optional[float] = None
    kali: Optional[float] = None
    vitamin_b_2: Optional[float] = None
    vitamin_pp: Optional[float] = None
    vitamin_c: Optional[float] = None
    calcium: Optional[float] = None
    phosphorus: Optional[float] = None
    fe: Optional[float] = None
    mg: Optional[float] = None
    zn: Optional[float] = None

class DishIngredientCreateBySuggestionSchema(Schema):
    suggestion_uid: UUID
    weight: float

class DishAvailabilitySchema(ModelSchema):

    class Meta:
        model = DishAvailability
        exclude = [
            "id",
            "dish",
        ]

class DishIngredientSuggestionSchema(Schema):
    custom_name: str
    category: IngredientCategoryEnum
    attachment_uid: Optional[UUID] = None
    weight: float
    energy: Optional[float] = None
    protein: Optional[float] = None
    lipid: Optional[float] = None
    carbohydrate: Optional[float] = None
    fiber: Optional[float] = None
    natri: Optional[float] = None
    kali: Optional[float] = None
    vitamin_b_2: Optional[float] = None
    vitamin_pp: Optional[float] = None
    vitamin_c: Optional[float] = None
    calcium: Optional[float] = None
    phosphorus: Optional[float] = None
    fe: Optional[float] = None
    mg: Optional[float] = None
    zn: Optional[float] = None
    limit: Optional[int] = 10