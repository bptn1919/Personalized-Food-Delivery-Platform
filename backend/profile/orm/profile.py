from dish.models import Dish
from profile.models import ChefProfile, CustomerAddress, CustomerFavoriteDish, CustomerProfile
from profile.schemas.requests import ChefProfileDetailSchema, CustomerAddressRequest
from profile.schemas.responses import ChefProfileDetailResponeSchema, CustomerAddressDetailResponse, CustomerFullProfileSchema
from attachment.models import Attachment
from django.db import transaction
from utils.types import TUser
from typing import Optional
from django.db.models import Count, Exists, OuterRef
from certificate.models import Certificate

class ProfileORM:
    @staticmethod
    def create_chef_profile(user: TUser, chef_data: dict, attachment: Optional[Attachment] = None):
        """Tạo chef profile với S3 attachment (presigned URL flow)"""

        profile, created = ChefProfile.objects.get_or_create(
            user=user,
            defaults={
                "avatar": attachment,
                **chef_data,
            },
        )

        # Idempotent behavior for upgrade flow: if profile already exists, update it.
        if not created:
            for field, value in chef_data.items():
                setattr(profile, field, value)
            if attachment is not None:
                profile.avatar = attachment
            profile.save()

        return (
            ChefProfile.objects
            .select_related("user", "avatar", "user__chef_payment_info")
            .get(pk=profile.pk)
        )
        
    @staticmethod
    def get_chef_profile_public(chef_id: int):
        # không lấy thông tin private như bank, chỉ lấy user_id, fullname, avatar, phone, bio, specialty, rating, number_of_orders
        try:
            cert_subquery = Certificate.objects.filter(
                owner=OuterRef('user'), # Kết nối 'owner' của Certificate với 'user' của ChefProfile
                certificate_type="SAFETY_TYPE",
                status="APPROVED"
            )
            profile = (
                ChefProfile.objects
                .select_related("user", "avatar")
                .annotate(
                    actual_orders=Count('user__order_fk_chef'), 
                    
                    has_safety_cert=Exists(cert_subquery) 
                )
                .get(user_id=chef_id)
            )
            return profile
        except ChefProfile.DoesNotExist:
            return None
        
    @staticmethod
    def get_chef_profile(chef_id: int):
        try:
            cert_subquery = Certificate.objects.filter(
                owner=OuterRef('user'), # Kết nối 'owner' của Certificate với 'user' của ChefProfile
                certificate_type="SAFETY_TYPE",
                status="APPROVED"
            )
            profile = (
                ChefProfile.objects
                .select_related("user", "avatar", "user__chef_payment_info")
                .annotate(actual_orders=Count('user__order_fk_chef'))
                .annotate(
                    actual_orders=Count('user__order_fk_chef'), 
                    
                    has_safety_cert=Exists(cert_subquery) 
                )
                .get(user_id=chef_id)
            )
            return profile
        except ChefProfile.DoesNotExist:
            return None
        
    @staticmethod
    def get_all_chef_profiles(sort_by: str = "rating_desc"):
        cert_subquery = Certificate.objects.filter(
            owner=OuterRef('user'), # Kết nối 'owner' của Certificate với 'user' của ChefProfile
            certificate_type="SAFETY_TYPE",
            status="APPROVED"
        )
        qs = (
            ChefProfile.objects
            .select_related("user", "avatar", "user__chef_payment_info")
            .annotate(actual_orders=Count('user__order_fk_chef'))
            .annotate(
                # Đếm số lượng order (như chúng ta đã làm ở task trước)
                actual_orders=Count('user__order_fk_chef'), 
                
                # 👇 TECH LEAD FIX: Kẹp thẳng cờ boolean vào biến 'has_safety_cert'
                has_safety_cert=Exists(cert_subquery) 
            )
            .all()
        )
        
        if sort_by == "orders_desc":
            qs = qs.order_by("-number_of_orders") 
        elif sort_by == "orders_asc":
            qs = qs.order_by("number_of_orders") # Mới thêm: Không có dấu trừ là tăng dần
        elif sort_by == "name_desc":
            qs = qs.order_by("-user__first_name")  # Mới thêm: Tên Z -> A
        elif sort_by == "name_asc":
            qs = qs.order_by("user__first_name") 
        elif sort_by == "rating_asc":
            qs = qs.order_by("rating")           # Mới thêm: Rating Thấp -> Cao
        else:
            qs = qs.order_by("-rating")
            
        return qs
    
    @staticmethod
    def get_popular_chefs(limit: int = 5):
        # Sắp xếp theo rating giảm dần và lấy đúng số lượng limit (VD: 5 người)
        return (
            ChefProfile.objects
            .select_related("user", "avatar", "user__chef_payment_info")
            # 👇 TECH LEAD FIX: Thêm đếm số lượng đơn hàng (Dùng distinct=True để chống lỗi đếm khống)
            .annotate(actual_orders=Count('user__order_fk_chef', distinct=True)) 
            .order_by("-rating")[:limit]
        )

    @staticmethod
    def update_chef_profile(user: TUser, chef_data: dict, attachment: Optional[Attachment] = None):
        profile = ChefProfile.objects.filter(user=user).select_related("user", "avatar").first()
        if not profile:
            return None

        for field, value in chef_data.items():
            setattr(profile, field, value)
            
        print("Updating chef profile with data:", chef_data)

        if attachment is not None:
            print("Updating chef avatar with new attachment:", attachment)
            profile.avatar = attachment

        profile.save()

        return (
            ChefProfile.objects
            .select_related("user", "avatar", "user__chef_payment_info")
            .get(pk=profile.pk)
        )
        
class CustomerORM:

    @staticmethod
    def get_customer_profile(user: TUser):
        profile, _ = CustomerProfile.objects.select_related(
            "user", "avatar"
        ).prefetch_related(
            "user__customer_address_user_fk_user"
        ).get_or_create(user=user)

        return profile
    @staticmethod
    def get_customer_address(user: TUser):
        return CustomerAddress.objects.filter(user=user)
        
    @staticmethod
    def get_one_customer_address(user: TUser):
        address = CustomerAddress.objects.filter(user=user, selected=True).first()
        
        # 2. Nếu không có cái nào mặc định, lấy địa chỉ mới được thêm gần đây nhất
        if not address:
            address = CustomerAddress.objects.filter(user=user).order_by('-id').first()
            
        return address
       # return CustomerAddress.objects.filter(user=user).first()
  
        
    @staticmethod
    def get_one_customer_address_by_id(user: TUser, address_id: int):
        # ưu tiên default dress trước, nếu có nhiều hơn 1 address thì lấy cái đầu tiên (theo id) trong số những address được chọn làm default
        default_address = CustomerAddress.objects.filter(user=user, selected=True).first()
        if default_address:
            return default_address
        return CustomerAddress.objects.get(user=user, id=address_id)
    
    @staticmethod
    def set_default_customer_address(user: TUser, address_id: int) -> bool:
        """
        Dùng transaction.atomic để đảm bảo nếu một bước lỗi, toàn bộ sẽ rollback.
        """
        with transaction.atomic():
            # 1. Chuyển tất cả địa chỉ của user này về False
            CustomerAddress.objects.filter(user=user, selected=True).update(selected=False)
            
            # 2. Bật selected=True cho địa chỉ mục tiêu
            # Trả về số lượng row được update (nên là 1 nếu tìm thấy)
            updated_count = CustomerAddress.objects.filter(user=user, id=address_id).update(selected=True)
            
            return updated_count > 0
        
    @staticmethod
    def get_one_customer_address_instance(user: TUser):
        return CustomerAddress.objects.filter(user=user).first()
    
    @staticmethod
    def get_one_customer_address_instance_by_id(user: TUser, address_id: int):
        return CustomerAddress.objects.get(user=user, id=address_id)
    
    @staticmethod
    def selected_address(user: TUser, address_id: int):
        addresses = CustomerAddress.objects.filter(user=user)
        for addr in addresses:
            if addr.id == address_id:
                addr.selected = True
            else:
                addr.selected = False
            addr.save()
            
    @staticmethod
    def create_new_customer_address(user: TUser, payload: CustomerAddressRequest):
        return CustomerAddress.objects.create(
            **payload.dict(), user=user
        )
    
    @staticmethod
    def get_favorite_dish(user: TUser, dish_uid: str):
        # chỉ lấy những món yêu thích chưa bị xóa (deleted=False)
        try:
            return CustomerFavoriteDish.objects.get(user=user, dish__uid=dish_uid, deleted=False)
        except CustomerFavoriteDish.DoesNotExist:
            return None

    @staticmethod
    def add_favorite_dish(user: TUser, dish: Dish):
        CustomerFavoriteDish.objects.update_or_create(
            user=user,
            dish=dish,
            defaults={"deleted": False},
        )
        dish.is_favorite = True
        return dish
    
    @staticmethod
    def remove_favorite_dish(fav_dish: CustomerFavoriteDish):
        if fav_dish:
            fav_dish.deleted = True
            fav_dish.save()
        return True

    @staticmethod
    def get_favorite_dishes(user: TUser):
        return Dish.objects.filter(customer_favorite_dish_fk_dish__user=user, customer_favorite_dish_fk_dish__deleted=False)
    
    @staticmethod
    def update_customer_profile(user: TUser, customer_data: dict, attachment: Optional[Attachment] = None):
        profile, _ = CustomerProfile.objects.select_related("user").get_or_create(user=user)

        for field, value in customer_data.items():
            setattr(profile, field, value)

        if attachment is not None:
            profile.avatar = attachment

        profile.save()

        return CustomerORM.get_customer_profile(user=user)
    
    @staticmethod
    def soft_delete_customer_address(user: TUser, address_id: int):
        try:
            address = CustomerAddress.objects.get(user=user, id=address_id)
            address.deleted = True
            address.save()
            return address
        except CustomerAddress.DoesNotExist:
            return None