from typing import Optional
from uuid import UUID

from ninja import ModelSchema, Schema

from attachment.schemas.responses import AttachmentResponse
from ingredient.models import Ingredient,FavouriteIngredient
from utils.enums import IngredientCategoryEnum, IngredientImportStatusEnum


class IngredientResponse(ModelSchema):
    attachment: Optional[AttachmentResponse] = None

    class Meta:
        model = Ingredient
        exclude = [
            "created_at",
            "deleted",
            "name_no_accent",
            "owner",
            "updated_at",
            "updater",
        ]


class ShortenIngredientResponse(Schema):
    uid: UUID
    name: str
    category: IngredientCategoryEnum
    attachment: Optional[AttachmentResponse] = None


class IngredientImportError(Schema):
    row: int
    message: str


class IngredientImportResult(Schema):
    total_rows: int
    created_count: int
    failed_count: int
    errors: list[IngredientImportError]


class IngredientSearchItem(Schema):
    ingredient_uid: Optional[UUID] = None
    suggestion_uid: Optional[UUID] = None

    name: str
    category: Optional[IngredientCategoryEnum] = None
    matched_alias: Optional[str] = None
    score: float

    source: str
    approval_status: str
    is_suggestion: bool


class IngredientAutocompleteItem(Schema):
    uid: UUID
    name: str
    category: IngredientCategoryEnum


class IngredientAliasResponse(Schema):
    uid: UUID
    ingredient_uid: UUID
    ingredient_name: str
    alias: str


class IngredientSuggestionCandidateResponse(Schema):
    uid: UUID
    name: str
    category: IngredientCategoryEnum
    matched_alias: Optional[str] = None
    match_type: str
    score: float

class IngredientSuggestionResponse(Schema):
    uid: UUID
    name: str
    category: Optional[IngredientCategoryEnum] = None
    status: IngredientImportStatusEnum

    created_by_id: Optional[int] = None
    verified_by_id: Optional[int] = None
    verified_at: Optional[str] = None

    resolution_note: Optional[str] = None
    
class IngredientSuggestionApproveNewResponse(Schema):
    suggestion_uid: UUID
    name: str
    category: IngredientCategoryEnum
    status: IngredientImportStatusEnum

    new_ingredient_uid: UUID

    created_by_id: Optional[int] = None
    verified_by_id: Optional[int] = None
    verified_at: Optional[str] = None

    resolution_note: Optional[str] = None

class IngredientSuggestionApproveAliasResponse(Schema):
    suggestion_uid: UUID
    name: str
    category: IngredientCategoryEnum
    status: IngredientImportStatusEnum

    resolved_ingredient_uid: UUID
    resolved_alias_uid: UUID

    created_by_id: Optional[int] = None
    verified_by_id: Optional[int] = None
    verified_at: Optional[str] = None

    resolution_note: Optional[str] = None

class IngredientSuggestionRejectResponse(Schema):
    suggestion_uid: UUID
    name: str
    category: IngredientCategoryEnum
    status: IngredientImportStatusEnum

    rejection_reason: str

    created_by_id: Optional[int] = None
    verified_by_id: Optional[int] = None
    verified_at: Optional[str] = None

class UserIngredientPreferenceResponse(Schema):
    ingredient_uid: UUID
    ingredient_name: str
    category: IngredientCategoryEnum
