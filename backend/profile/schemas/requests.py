from typing import Optional

from ninja import ModelSchema, Schema
from uuid import UUID

from utils.enums import AllergyModeEnum, DietLevelEnum, DietModeEnum
from profile.models import ChefProfile, CustomerAddress, CustomerProfile
    
class ChefProfileDetailSchema(ModelSchema):
    class Meta:
        model = ChefProfile
        exclude = [
            "id",
            "user",
            "rating",
            "number_of_orders",
        ]
class CustomerAddressRequest(ModelSchema):
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    class Meta:
        model = CustomerAddress
        exclude = [
            "user",
        ]   


class ChefProfileUpdateSchema(Schema):
    bio: Optional[str] = None
    specialty: Optional[str] = None
    attachment_uid: Optional[UUID] = None


class CustomerProfileUpdateSchema(Schema):
    bio: Optional[str] = None
    attachment_uid: Optional[UUID] = None
    phone: Optional[str] = None
    diet_mode: Optional[DietModeEnum] = None
    diet_level: Optional[DietLevelEnum] = None
    allergy_mode: Optional[AllergyModeEnum] = None


class CustomerOnboardingSchema(Schema):
    height_cm: float
    weight_kg: float
    allergic_ingredient_uids: list[UUID]
    favorite_ingredient_uids: list[UUID]
