from uuid import UUID

from pydantic_core import ValidationError

from attachment.services import AttachmentService
from utils.permissions.decorators import sync_user_feature
from utils.enums import DietLevelEnum, DietModeEnum
from profile.orm.profile import ProfileORM, CustomerORM
from profile.orm.chef_payment import ChefPaymentInfoORM
from profile.schemas.requests import (
    ChefProfileDetailSchema,
    ChefProfileUpdateSchema,
    CustomerAddressRequest,
    CustomerOnboardingSchema,
    CustomerProfileUpdateSchema,
)
from profile.schemas.chef_payment import ChefPaymentInfoRequest
from utils.types import TUser
from exceptions.profiles import FavouriteDishDoesNotExist, ProfileDoesNotExist
from exceptions.dishes import DishNotFoundException
from attachment.queries import Query as AttachmentQuery      
from exceptions.attachments import AttachmentNotFound
from ninja.errors import HttpError
from utils.exceptions import PermissionDeniedError
from utils.enums import UserTypeEnum
from django.db import transaction
from django.utils import timezone

class ProfileService:
    def __init__(self):
        self.orm = ProfileORM()
        self.attachment_service = AttachmentService()

    def create_chef_profile(self, user, payload):
        attachment = None

        avatar_uid = getattr(payload, "avatar", None)

        if avatar_uid is not None:
            try:
                avatar_uuid = UUID(str(avatar_uid))
            except ValueError:
                raise AttachmentNotFound

            attachment = self.attachment_service.handle_attachment(uid=avatar_uuid)

        chef_data = payload.dict(exclude={"avatar"}, exclude_none=True)

        return self.orm.create_chef_profile(
            user=user,
            chef_data=chef_data,
            attachment=attachment
        )

    def get_chef_public_profile(self, chef_id: int):
        profile = self.orm.get_chef_profile_public(chef_id=chef_id)
        if not profile:
            raise ProfileDoesNotExist
        return profile

    def get_chef_profile(self, user: TUser, chef_id: int):
        profile = self.orm.get_chef_profile(chef_id=chef_id)
        if not profile:
            raise ProfileDoesNotExist

        is_admin = user.groups.filter(name=UserTypeEnum.ADMIN).exists()
        is_owner = user.id == profile.user.id

        # ✔ Nếu admin hoặc chính chef → trả full
        if is_admin or is_owner:
            return profile
        # Nếu không thì raise PermissionDenied
        raise PermissionDeniedError
    
    def get_all_chef_profiles(self, sort_by: str = "rating_desc"):
        profile = self.orm.get_all_chef_profiles(sort_by=sort_by)
        if not profile:
            raise ProfileDoesNotExist
        return profile
    
    def get_popular_chefs(self):
        profiles = self.orm.get_popular_chefs(limit=5) # Giới hạn 5 thẻ trên Home
        if not profiles:
            return [] # Trả về mảng rỗng nếu chưa có data, không nên raise Error ở Home
        return profiles

    def update_chef_profile(self, user: TUser, payload: ChefProfileUpdateSchema):
        attachment = None

        if payload.attachment_uid is not None:
            try:
                avatar_uuid = UUID(str(payload.attachment_uid))
            except ValueError:
                raise AttachmentNotFound

            attachment = self.attachment_service.handle_attachment(uid=avatar_uuid)
        # attachment = None
        # if payload.attachment_uid is not None:
        #     try:
        #         avatar_uuid = UUID(str(payload.attachment_uid))
        #     except ValueError:
        #         raise AttachmentNotFound
        #     self.attachment_service.handle_attachment(uid=avatar_uuid)

        chef_data = payload.dict(exclude={"attachment_uid"}, exclude_none=True)
        profile = self.orm.update_chef_profile(user=user, chef_data=chef_data, attachment=attachment)
        if not profile:
            raise ProfileDoesNotExist
        return profile
    
class CustomerService:
    def __init__(self):
        self.orm = CustomerORM()
        self.attachment_service = AttachmentService()

    def rebuild_user_feature(self, user_id: int):
        from profile.models import CustomerProfile
        from recommendation.models import UserFoodPreferenceFeature

        profile = CustomerProfile.objects.get(user_id=user_id)

        UserFoodPreferenceFeature.objects.update_or_create(
            user_id=user_id,
            defaults={
                "diet_mode": profile.diet_mode,
                "diet_level": profile.diet_level,
                "allergy_mode": profile.allergy_mode,
            },
        )

    def get_customer_profile(self, user: TUser):
        profile = self.orm.get_customer_profile(user=user)
        if not profile:
            raise ProfileDoesNotExist
        return profile
    
    def get_customer_address(self, user: TUser):
        address = self.orm.get_customer_address(user=user)
        if not address:
            raise ProfileDoesNotExist
        return address
    
    def get_one_customer_address(self, user: TUser):
        address = self.orm.get_one_customer_address(user=user)
        if not address:
            raise ProfileDoesNotExist
        return address
    
    def get_one_customer_address_by_id(self, user: TUser, address_id: int):
        address = self.orm.get_one_customer_address_by_id(user=user, address_id=address_id)
        if not address:
            raise ProfileDoesNotExist
        return address
    
    def set_default_customer_address(self, user: TUser, address_id: int):
        # Gọi ORM xử lý
        success = self.orm.set_default_customer_address(user=user, address_id=address_id)
        
        if not success:
            # Nếu không tìm thấy địa chỉ đó để update, ném lỗi
            raise ProfileDoesNotExist # Hoặc dùng ProfileDoesNotExist như bạn đã định nghĩa
            
        return {"message": "Set default address successfully"}
    
    def create_new_customer_address(self, user: TUser, payload: CustomerAddressRequest):
        return self.orm.create_new_customer_address(user=user, payload=payload)
    
    def get_favorite_dish(self, user: TUser, dish_uid: str):
        return self.orm.get_favorite_dish(user=user, dish_uid=dish_uid)

    @sync_user_feature("user", update_fields=["fav_dish"])
    def add_favorite_dish(self, user: TUser, dish_uid: str):
        # check dish existence
        from dish.services import DishService
        dish_service = DishService()
        dish = dish_service.get_dish_by_uid(uid=dish_uid)
        self.orm.add_favorite_dish(user=user, dish=dish)
        return dish_service.get_dish_by_uid(uid=dish_uid, user=user)
    
    @sync_user_feature("user", update_fields=["fav_dish"])
    def remove_favorite_dish(self, user: TUser, dish_uid: str):
        fav_dish =self.get_favorite_dish(user=user, dish_uid=dish_uid)  # check existence
        if not fav_dish:
            raise FavouriteDishDoesNotExist
        return self.orm.remove_favorite_dish(fav_dish=fav_dish)
    
    def get_favorite_dishes(self, user: TUser):
        from dish.services import DishService

        dish_service = DishService()
        dishes = self.orm.get_favorite_dishes(user=user)
        results = []
        for dish in dishes:
            try:
                results.append(dish_service.get_dish_by_uid(uid=dish.uid, user=user))
            except DishNotFoundException:
                continue
        return results

    @transaction.atomic
    def onboard_customer_profile(self, user: TUser, payload: CustomerOnboardingSchema):
        from ingredient.models import AllergicIngredient, FavouriteIngredient, Ingredient
        from recommendation.models import UserDailyNutrition
        from recommendation.services.recommendation import RecommendationService
        from recommendation.services.daily_nutrition import DailyNutritionService

        customer_profile = self.orm.get_customer_profile(user=user)
        if not customer_profile:
            raise ProfileDoesNotExist

        allergic_uids = list(dict.fromkeys(payload.allergic_ingredient_uids))
        favorite_uids = list(dict.fromkeys(payload.favorite_ingredient_uids))
        required_uids = set(allergic_uids + favorite_uids)

        ingredients_by_uid = {
            ingredient.uid: ingredient
            for ingredient in Ingredient.objects.filter(uid__in=required_uids, deleted=False)
        }
        missing_uids = required_uids - set(ingredients_by_uid.keys())
        if missing_uids:
            raise HttpError(400, "One or more ingredient_uids are invalid")

        today = timezone.localdate()
        daily, _ = UserDailyNutrition.objects.get_or_create(
            user=user,
            date=today,
            defaults={
                "height_cm": max(float(payload.height_cm), 1.0),
                "weight_kg": max(float(payload.weight_kg), 1.0),
            },
        )
        daily.height_cm = max(float(payload.height_cm), 1.0)
        daily.weight_kg = max(float(payload.weight_kg), 1.0)
        DailyNutritionService()._compute_daily_targets(daily)
        daily.save()

        AllergicIngredient.objects.filter(user=user).update(deleted=True)
        FavouriteIngredient.objects.filter(user=user).update(deleted=True)

        for ingredient_uid in allergic_uids:
            AllergicIngredient.objects.update_or_create(
                user=user,
                ingredient=ingredients_by_uid[ingredient_uid],
                defaults={"deleted": False},
            )

        for ingredient_uid in favorite_uids:
            FavouriteIngredient.objects.update_or_create(
                user=user,
                ingredient=ingredients_by_uid[ingredient_uid],
                defaults={"deleted": False},
            )

        RecommendationService().rebuild_user_feature(
            user.id,
            update_fields=["allergy", "fav_ingredient"],
        )

        customer_profile.is_onboarded = True
        customer_profile.save(update_fields=["is_onboarded"])
        return self.orm.get_customer_profile(user=user)


    @sync_user_feature("user", update_fields=["diet"])
    def update_customer_profile(self, user: TUser, payload: CustomerProfileUpdateSchema):
        print("call update_customer_profile")
        attrs = payload.dict(exclude_none=True)
        customer_profile = self.orm.get_customer_profile(user=user)
        if not customer_profile:
            raise ProfileDoesNotExist

        if payload.diet_mode is not None and payload.diet_level is None and customer_profile.diet_mode == DietModeEnum.NONE:
            raise HttpError(400, "diet_level must be provided when diet_mode is not NONE")
        # trường hợp nếu diet_mode được update thành NONE thì diet_level cũng phải được update thành NONE
        if payload.diet_mode == DietModeEnum.NONE and payload.diet_level is not None and payload.diet_level != DietLevelEnum.NONE:
            raise HttpError(400, "diet_level must be NONE when diet_mode is NONE")

        attachment = None
        if payload.attachment_uid is not None:
            attachment = self.attachment_service.handle_attachment(
                uid=payload.attachment_uid
            )

        customer_data = payload.dict(exclude_none=True)
        customer_data.pop("attachment_uid", None)

        updated_profile = self.orm.update_customer_profile(
            user=user,
            customer_data=customer_data,
            attachment=attachment
        )
        # self.rebuild_user_feature(user.id)
        return updated_profile
    
    def soft_delete_customer_address(self, user: TUser, address_id: int):
        # Gọi ORM xử lý soft delete
        success = self.orm.soft_delete_customer_address(user=user, address_id=address_id)
        
        if not success:
            # Nếu không tìm thấy địa chỉ đó để soft delete, ném lỗi
            raise ProfileDoesNotExist
            
        return True

class ChefPaymentService:
    """Service layer for chef payment information management"""

    def __init__(self):
        from utils.services.email.client import EmailClient
        from utils.services.email.template import EmailTemplate
        self.email_client = EmailClient()
        self.email_template = EmailTemplate()

    def request_bank_verify_otp(self, user: TUser, payload: ChefPaymentInfoRequest) -> dict:
        """Save/update chef payment info (unverified) then send OTP to email."""
        from users.queries import Query as UserQuery

        payment_info = ChefPaymentInfoORM.get_by_user(user)
        if payment_info:
            ChefPaymentInfoORM.update(
                payment_info=payment_info,
                bank_name=payload.bank_name,
                bank_code=payload.bank_code,
                bank_account_number=payload.bank_account_number,
                bank_account_name=payload.bank_account_name,
                bank_branch=payload.bank_branch,
                citizen_id=getattr(payload, 'citizen_id', None),
                tax_code=getattr(payload, 'tax_code', None),
                is_verified=False,
            )
            payment_info.verified_at = None
            payment_info.save(update_fields=["verified_at"])
        else:
            ChefPaymentInfoORM.create(
                user=user,
                bank_name=payload.bank_name,
                bank_code=payload.bank_code,
                bank_account_number=payload.bank_account_number,
                bank_account_name=payload.bank_account_name,
                bank_branch=payload.bank_branch,
                citizen_id=getattr(payload, 'citizen_id', None),
                tax_code=getattr(payload, 'tax_code', None),
                is_verified=False,
            )

        UserQuery.inactive_otp_token(user)
        otp_record, plain_otp = UserQuery.create_otp(user=user, purpose="BANK_VERIFY")

        template = self.email_template.send_verification_email(
            user=user, otp=plain_otp, purpose="BANK_VERIFY"
        )
        self.email_client.send(messages=[template])

        return {"reset_session_token": otp_record.reset_session_token}

    def verify_chef_bank_info_otp(self, user: TUser, reset_session_token: str, otp: str):
        """Verify OTP then mark chef bank info as verified."""
        from users.queries import Query as UserQuery
        from exceptions.auth import InvalidOrExpiredToken, InvalidOtp
        from django.utils import timezone

        record = UserQuery.get_otp_record(reset_session_token)

        if not record:
            raise InvalidOrExpiredToken
        if record.otp_verified:
            raise InvalidOtp("OTP already used")
        if record.purpose != "BANK_VERIFY":
            raise InvalidOrExpiredToken
        if record.user_id != user.id:
            raise InvalidOrExpiredToken
        if record.is_expired():
            record.active = False
            record.save(update_fields=["active"])
            raise InvalidOrExpiredToken
        if not record.verify(otp):
            raise InvalidOtp

        record.otp_verified = True
        record.active = False
        record.save(update_fields=["otp_verified", "active"])

        payment_info = ChefPaymentInfoORM.get_by_user(user)
        if not payment_info:
            raise HttpError(400, "Payment info not found. Please submit bank info first.")

        payment_info.is_verified = True
        payment_info.verified_at = timezone.now()
        payment_info.save(update_fields=["is_verified", "verified_at", "updated_at"])
        return payment_info

    def create_or_update_payment_info(self, user: TUser, payload: ChefPaymentInfoRequest):
        """
        Create or update chef payment information.
        Returns payment info with masked account number.
        """
        payment_info = ChefPaymentInfoORM.get_by_user(user)
        
        if payment_info:
            # Update existing
            payment_info = ChefPaymentInfoORM.update(
                payment_info=payment_info,
                bank_name=payload.bank_name,
                bank_code=payload.bank_code,
                bank_account_number=payload.bank_account_number,
                bank_account_name=payload.bank_account_name,
                bank_branch=payload.bank_branch,
                citizen_id=payload.citizen_id,
                tax_code=payload.tax_code,
                is_verified=False  # Reset verification on update
            )
        else:
            # Create new
            payment_info = ChefPaymentInfoORM.create(
                user=user,
                bank_name=payload.bank_name,
                bank_code=payload.bank_code,
                bank_account_number=payload.bank_account_number,
                bank_account_name=payload.bank_account_name,
                bank_branch=payload.bank_branch,
                citizen_id=payload.citizen_id,
                tax_code=payload.tax_code,
                is_verified=False
            )
        
        return payment_info
    
    def get_payment_info(self, user: TUser):
        """
        Get chef's payment information.
        Returns None if not found.
        """
        payment_info = ChefPaymentInfoORM.get_by_user(user)
        if not payment_info:
            raise ProfileDoesNotExist
        return payment_info
    
    def delete_payment_info(self, user: TUser):
        """
        Delete chef's payment information.
        Raises ProfileDoesNotExist if not found.
        """
        payment_info = ChefPaymentInfoORM.get_by_user(user)
        if not payment_info:
            raise ProfileDoesNotExist
        
        # soft delete, chỉ đánh dấu deleted=True
        payment_info.deleted = True
        payment_info.save()
        return True
        

    
    @staticmethod
    def mask_account_number(account_number: str) -> str:
        """Mask account number - show only last 4 digits"""
        if len(account_number) <= 4:
            return account_number
        return '*' * (len(account_number) - 4) + account_number[-4:]
