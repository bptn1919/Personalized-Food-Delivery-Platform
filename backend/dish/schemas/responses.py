from typing import Optional
from uuid import UUID

from ninja import ModelSchema, Schema
from pydantic import BaseModel

from attachment.schemas.responses import AttachmentResponse
from dish.models import Dish, DishIngredient
from datetime import date
from typing import List
from utils.enums import DishCategoryEnum, IngredientImportStatusEnum, IngredientSourceEnum
from pydantic import Field


class DishResponse(ModelSchema):
    is_favorite: bool = False
    allergy_warning: bool = False
    allergen_ingredients: list[str] = []

    full_name_of_chef: Optional[str] = None
    public_url: Optional[str] = None
    location: Optional[str] = None
    location_id: Optional[int] = None
    sold_count: int = 0
    in_stock: int = 0
    class Meta:
        model = Dish
        exclude = [
            "attachment",
            "created_at",
            "deleted",
            "name_no_accent",
            "owner",
            "updated_at",
            "updater",
        ]
    
    @staticmethod
    def resolve_public_url(obj):
        return obj.attachment.public_url if obj.attachment else None

    @staticmethod
    def resolve_full_name_of_chef(obj):
        if not obj.owner:
            return None
        full_name = obj.owner.get_full_name()
        return full_name if full_name else obj.owner.username

    @staticmethod
    def resolve_location(obj):
        if not obj.location:
            return None

        names = []
        current = obj.location
        while current:
            names.append(current.name)
            current = current.parent

        return " - ".join(reversed(names))
    @staticmethod
    def resolve_location_id(obj):
        return obj.location.id if obj.location else None

class DishListResponse(ModelSchema):
    is_favorite: bool = False
    full_name_of_chef: Optional[str] = None
    public_url: Optional[str] = None
    location: Optional[str] = None
    location_id: Optional[int] = None
    sold_count: int = 0
    in_stock: int = 0

    class Meta:
        model = Dish
        exclude = [
            "attachment",
            "created_at",
            "deleted",
            "name_no_accent",
            "owner",
            "updated_at",
            "updater",
        ]

    @staticmethod
    def resolve_public_url(obj):
        return obj.attachment.public_url if obj.attachment else None

    @staticmethod
    def resolve_full_name_of_chef(obj):
        if not obj.owner:
            return None
        full_name = obj.owner.get_full_name()
        return full_name if full_name else obj.owner.username

    @staticmethod
    def resolve_location(obj):
        if not obj.location:
            return None

        names = []
        current = obj.location
        while current:
            names.append(current.name)
            current = current.parent

        return " - ".join(reversed(names))

    @staticmethod
    def resolve_location_id(obj):
        return obj.location.id if obj.location else None
    
class AllDishesInMenuResponse(ModelSchema):
    active: bool
    position: int
    public_url: Optional[str] = None  
    class Meta:
        model = Dish
        exclude = [
            "attachment",
            "created_at",
            "deleted",
            "name_no_accent",
            "owner",
            "updated_at",
            "updater",
        ]
    @staticmethod
    def resolve_public_url(obj):
        # Endpoint chef/menus/{uid}/all-dishes can return dict payloads from ORM.
        if isinstance(obj, dict):
            return obj.get("public_url")
        attachment = getattr(obj, "attachment", None)
        return attachment.public_url if attachment else None


class TopDishResponse(ModelSchema):
    chef_id: Optional[int] = None
    full_name_of_chef: Optional[str] = None
    public_url: Optional[str] = None
    sold_count: int = 0
    review_count: int = 0
    score: float = 0
    in_stock: int = 0

    class Meta:
        model = Dish
        exclude = [
            "attachment",
            "created_at",
            "deleted",
            "name_no_accent",
            "owner",
            "updated_at",
            "updater",
        ]

    @staticmethod
    def resolve_public_url(obj):
        return obj.attachment.public_url if obj.attachment else None

    @staticmethod
    def resolve_chef_id(obj):
        return obj.owner_id

    @staticmethod
    def resolve_full_name_of_chef(obj):
        if not obj.owner:
            return None
        full_name = obj.owner.get_full_name()
        return full_name if full_name else obj.owner.username

class ShortenDishResponse(Schema):
    uid: UUID
    name: str
    category: DishCategoryEnum
    attachment: Optional[AttachmentResponse] = None



class DishAvailabilityResponse(Schema):
    available_date: date
    available_quantity: int
    note: Optional[str] = None

class DishAvailabilityListResponse(Schema):
    dish_uid: str
    dish_name: str
    availabilities: List[DishAvailabilityResponse]


class DishLocationResponse(Schema):
    id: int
    name: str
    slug: str
    type: str
    parent_id: Optional[int] = None

class DishLocationShortResponse(Schema):
    id: int
    name: str


class DishLocationTreeResponse(Schema):
    id: int
    name: str
    slug: str
    type: str
    parent_id: Optional[int] = None
    children: List[dict] = []


class DishIngredientResponse(Schema):
    dish_uid: UUID
    ingredient_uid: Optional[UUID] = None
    ingredient_name: Optional[str] = None
    custom_name: Optional[str] = None
    source: str
    suggestion_uid: Optional[UUID] = None
    approval_status: str
    created_by_id: Optional[int] = None
    updated_by_id: Optional[int] = None
    weight: Optional[float] = None
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


class IngredientOfDish(Schema):
    # 2. BẮT BUỘC chỉ khai báo thuộc tính, KHÔNG alias, KHÔNG có hàm resolve_ ở dưới
    ingredient_name: str
    weight: Optional[float] = None
    energy: Optional[float] = None
    protein: Optional[float] = None
    lipid: Optional[float] = None
    carbohydrate: Optional[float] = None
    fiber: Optional[float] = None
    natri: Optional[float] = None
    cholesterol: Optional[float] = None

class IngredientOfDishDetail(ModelSchema):
    ingredient_name: Optional[str] = None
    ingredient_uid: Optional[UUID] = None

    class Meta:
        model = DishIngredient
        fields = "__all__"
        exclude = ["dish", "ingredient", "updated_at", "updated_by", "created_at", "created_by", "deleted"]

class NutritionTotalDetail(Schema):
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

class NutritionTotal(Schema):
    energy: Optional[float] = None
    protein: Optional[float] = None
    lipid: Optional[float] = None
    carbohydrate: Optional[float] = None
    fiber: Optional[float] = None
    natri: Optional[float] = None
    cholesterol: Optional[float] = None

class DishIngredientPublicResponse(Schema):
    # thừa kế model dish ingredient, nhưng chỉ trả về một số trường public, không có trường nào liên quan đến nội bộ hay private
    confidence_of_dish: Optional[float] = None
    confidence_text: Optional[str] = None
    # note diễn tả nguyên nhân confidence thấp, ví dụ: "có nhiều nguyên liệu chưa được xác thực", hay nguyên liệu chuẩn đã được xác thực bởi admin
    note: Optional[str] = None
    ingredients: List[IngredientOfDish] = Field(default_factory=list)
    nutrition_total: Optional[NutritionTotal] = None 

# for chef
class DishIngredientPrivateResponse(Schema):
    confidence_of_dish: Optional[float] = None
    confidence_text: Optional[str] = None
    note: Optional[str] = None
    ingredients: List[IngredientOfDishDetail] = Field(default_factory=list)
    nutrition_total: Optional[NutritionTotalDetail] = None

class DishIngredientPreviewNutrition(Schema):
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
    
class WarningSchema(Schema):
    type: str
    severity: float
    message: str
    field: str | None = None

class DishIngredientPreviewResponse(Schema):
    ingredient_uid: Optional[UUID] = None
    ingredient_name: Optional[str] = None
    weight: float
    nutritions: DishIngredientPreviewNutrition
    warnings: list[WarningSchema]
    confidence: float


class DishIngredientSaveResponse(Schema):
    status: str
    dish_uid: UUID
    ingredient_uid: Optional[UUID] = None
    ingredient_name: Optional[str] = None
    custom_name: Optional[str] = None
    source: str
    suggestion_uid: Optional[UUID] = None
    approval_status: str
    created_by_id: Optional[int] = None
    updated_by_id: Optional[int] = None
    nutritions: DishIngredientPreviewNutrition
    warnings: list[WarningSchema]
    confidence: float

class DishIngredientBySuggestionResponse(Schema):
    status: str
    dish_uid: UUID
    ingredient_custom_name: Optional[str] = None
    source: str
    suggestion_uid: Optional[UUID] = None
    approval_status: str
    created_by_id: Optional[int] = None
    updated_by_id: Optional[int] = None
    confidence: float
    nutritions: DishIngredientPreviewNutrition   

class DishIngredientSuggestionResponse(Schema):
    dish_ingredient_uid: UUID
    dish_ingredient_source: IngredientSourceEnum
    custom_name: str
    category: DishCategoryEnum
    public_url: Optional[str] = None
    weight: float
    nutrition: DishIngredientPreviewNutrition

    dish_ingredient_suggestion_uid: UUID
    status: IngredientImportStatusEnum
    warnings: list[WarningSchema]
    confidence: float

class CandidateSchema(Schema):
    uid: UUID
    name: str
    score: float
    is_best: Optional[bool] = False

class DishIngredientSuggestionPreviewResponse(Schema):
    custom_name: str
    weight: float
    nutrition: DishIngredientPreviewNutrition
    # candidates: list[str]
    candidates: list[CandidateSchema]
    warnings: list[WarningSchema]
    confidence: float


class DishSearchResultSchema(Schema):
    """Một kết quả tìm kiếm dish"""
    uid: str
    name: str
    category: str
    price: float
    description: Optional[str] = None
    status: str
    rating: float
    popularity_score: float
    search_score: float  # Score từ search algorithm (0-2)
    image_url: Optional[str] = None
    location_id: Optional[int] = None
    is_favorite: bool = False


class DishSearchResponseSchema(Schema):
    """Response từ search API"""
    query: str
    total: int
    results: List[DishSearchResultSchema]