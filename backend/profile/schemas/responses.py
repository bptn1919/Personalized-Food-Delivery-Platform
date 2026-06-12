from typing import Optional
from ninja import ModelSchema, Schema
from typing import List
from profile.models import ChefProfile, CustomerAddress, CustomerProfile, ChefPaymentInfo
from ninja import Field

class ProfileResponeSchema(Schema):
    id: int
    fullname: str
    mail: str
    phone: str

class ChefPaymentInfoResponse(ModelSchema):
    class Meta:
        model = ChefPaymentInfo
        exclude = [ "id", "user" , "created_at", "updated_at"]

class ChefProfilePublicResponseSchema(ModelSchema):
    user_id: int
    fullname: str
    avatar: Optional[str] = None
    phone: Optional[str] = None
    mail: str
    is_food_safety_certified: bool = False

    class Meta:
        model = ChefProfile
        exclude = [
            "id",
            "user",
        ]

    @staticmethod
    def resolve_avatar(obj):
        return obj.avatar.public_url if obj.avatar else None

    @staticmethod
    def resolve_addresses(obj):
        return obj.user.customer_address_user_fk_user.all()

    @staticmethod
    def resolve_fullname(obj):
        return obj.user.get_full_name()

    @staticmethod
    def resolve_mail(obj):
        return obj.user.email
    
    @staticmethod
    def resolve_number_of_orders(obj):
        return getattr(obj, 'actual_orders', 0)
    
    @staticmethod
    def resolve_is_food_safety_certified(obj):
        # 1. KIỂM TRA ĐƯỜNG CAO TỐC (O(1)):
        # Nếu ORM đã tính sẵn bằng .annotate() và đính kèm vào 'has_safety_cert'
        if hasattr(obj, 'has_safety_cert'):
            return obj.has_safety_cert
        # 👇 TECH LEAD FIX: Đổi "type" thành "certificate_type" theo đúng thiết kế DB của bạn
        return obj.user.certificate_fk_owner.filter(
            certificate_type="FOOD_SAFETY", 
            status="APPROVED" 
        ).exists()

    @staticmethod
    def resolve_phone(obj):
        return obj.user.phone_number
    
class ChefProfileDetailResponeSchema(ModelSchema):
    user_id: int
    fullname: str
    phone: Optional[str] = None
    avatar: Optional[str] = None
    mail: str
    bank: Optional[ChefPaymentInfoResponse] = None
    is_food_safety_certified: bool = False

    class Meta:
        model = ChefProfile
        exclude = [
            "id",
            "user",
        ]
    @staticmethod
    def resolve_avatar(obj):
        return obj.avatar.public_url if obj.avatar else None

    @staticmethod
    def resolve_addresses(obj):
        return obj.user.customer_address_user_fk_user.all()

    @staticmethod
    def resolve_fullname(obj):
        return obj.user.get_full_name()

    @staticmethod
    def resolve_mail(obj):
        return obj.user.email
    
    @staticmethod
    def resolve_number_of_orders(obj):
        return getattr(obj, 'actual_orders', 0)
    
    @staticmethod
    def resolve_is_food_safety_certified(obj):
        # 1. KIỂM TRA ĐƯỜNG CAO TỐC (O(1)):
        # Nếu ORM đã tính sẵn bằng .annotate() và đính kèm vào 'has_safety_cert'
        if hasattr(obj, 'has_safety_cert'):
            return obj.has_safety_cert
        # 👇 TECH LEAD FIX: Đổi "type" thành "certificate_type" theo đúng thiết kế DB của bạn
        return obj.user.certificate_fk_owner.filter(
            certificate_type="FOOD_SAFETY", 
            status="APPROVED" 
        ).exists()

    @staticmethod
    def resolve_phone(obj):
        return obj.user.phone_number
    
    @staticmethod
    def resolve_bank(obj):
        # Bước 1: Lấy data ra một biến riêng
        bank_info = getattr(obj.user, "chef_payment_info", None)
        
        # Bước 2: Debug an toàn bằng f-string (f-string sẽ tự động biến None thành chữ "None" mà không bị crash)
        print(f"DEBUG: Checking bank info for user {obj.user.id} -> {bank_info}")
        
        # Bước 3: Kiểm tra sâu hơn nếu bank_info tồn tại, để xem các trường bên trong có bị None không
        if bank_info:
            print(f"DEBUG: Bank info dict/object: {vars(bank_info) if hasattr(bank_info, '__dict__') else bank_info}")
            
        return bank_info
        
class CustomerAddressDetailResponse(ModelSchema):
    full_address:str
    class Meta:
        model = CustomerAddress
        exclude = [
            "user",
        ]   
    @staticmethod
    def resolve_full_address(obj: CustomerAddress):
        return obj.full_address()

    
class CustomerFullProfileSchema(ModelSchema):
    avatar: Optional[str] = None
    addresses: List[CustomerAddressDetailResponse] = Field(default_factory=list)
    fullname: str
    mail: str
    phone: str
    is_onboarded: bool

    class Meta:
        model = CustomerProfile
        exclude = ["id", "user"]

    @staticmethod
    def resolve_avatar(obj):
        return obj.avatar.public_url if obj.avatar else None

    @staticmethod
    def resolve_addresses(obj):
        return obj.user.customer_address_user_fk_user.all()

    @staticmethod
    def resolve_fullname(obj):
        return obj.user.get_full_name()

    @staticmethod
    def resolve_mail(obj):
        return obj.user.email

    @staticmethod
    def resolve_phone(obj):
        return obj.user.phone_number
class CustomerAddressResponse(ModelSchema):
    full_address:str
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    class Meta:
        model = CustomerAddress
        exclude = [
            "user",
            "address",
            "street",
            "ward",
            "district",
            "city",
        ]   

    @staticmethod
    def resolve_full_address(obj):
        return obj.full_address()

