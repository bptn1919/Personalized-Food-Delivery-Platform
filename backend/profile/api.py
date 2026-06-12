from profile.models import ChefProfile
from ninja.pagination import paginate, PageNumberPagination
from utils.router.authenticate import AuthBear
from utils.router.controller import Controller, api, delete, get, patch, post, put
from utils.types import AuthenticatedRequest

from .schemas.requests import (
    ChefProfileDetailSchema,
    ChefProfileUpdateSchema,
    CustomerAddressRequest,
    CustomerOnboardingSchema,
    CustomerProfileUpdateSchema,
)
from dish.schemas.responses import DishResponse
from .schemas.responses import ChefProfileDetailResponeSchema, CustomerAddressResponse, CustomerAddressDetailResponse, CustomerFullProfileSchema, ChefProfilePublicResponseSchema
from .schemas.chef_payment import ChefPaymentInfoRequest, ChefPaymentInfoResponse
from .services import ProfileService, CustomerService, ChefPaymentService
from ninja import Schema
from typing import List, Optional
from utils.permissions.decorators import require_group
from utils.exceptions import PermissionDeniedError
from utils.enums import UserTypeEnum
from profile.models import CustomerProfile, CustomerFavoriteDish, CustomerAddress, ChefPaymentInfo


@api(prefix_or_class="chef-profiles", tags=["ChefProfile"], auth=AuthBear())
class ChefProfileController(Controller):
    def __init__(self, service: ProfileService) -> None:
        self.service = service
    @post("/", response=ChefProfileDetailResponeSchema)
    @require_group(UserTypeEnum.CHEF) 
    def create_chef_profile(
        self,
        request: AuthenticatedRequest,
        payload: ChefProfileDetailSchema
    ):

        return self.service.create_chef_profile(
            user=request.user, 
            payload=payload,
        )

    @patch("/me", response=ChefProfileDetailResponeSchema)
    def update_chef_profile(
        self,
        request: AuthenticatedRequest,
        payload: ChefProfileUpdateSchema
    ):
        return self.service.update_chef_profile(user=request.user, payload=payload)
        
    class CheckChefResponse(Schema):
        is_chef: bool
        chef_id: Optional[int] = None
        
    @get("/is-chef-id", auth = True, response = CheckChefResponse)
    def check_is_chef(self, request: AuthenticatedRequest):
        chef_profile = ChefProfile.objects.filter(user=request.user).first()
        
        if chef_profile:
            return {
                "is_chef": True,
                "chef_id": chef_profile.id
            }
            
        return {"is_chef": False, "chef_id": None}
    
    @get("/popular", response=List[ChefProfileDetailResponeSchema])
    # 👇 Không dùng @paginate ở đây, trả về List thẳng luôn
    def get_popular_chefs(self):
        """        
        [CUSTOMER] Dùng trong trang Home, Lấy top 5 Chef được yêu thích nhất (Kéo ngang)
        """
        return self.service.get_popular_chefs()
        
    #customer API----
    @get("/{chef_id}", response=ChefProfilePublicResponseSchema)
    #@require_group(UserTypeEnum.CUSTOMER)
    def get_chef_profile(self, chef_id: int):
        """        
        [CUSTOMER] Lấy profile của chef theo chef_id
        """
        return self.service.get_chef_public_profile(chef_id=chef_id)
    
    @get("/me", response=ChefProfileDetailResponeSchema)
    @require_group(UserTypeEnum.CHEF)
    def get_chef_profile_detail(self, request: AuthenticatedRequest):
        """        
        [CHEF] Lấy profile của chef theo chef_id
        """
        return self.service.get_chef_profile(user=request.user, chef_id=request.user.id)
    
    @get("/", response=List[ChefProfilePublicResponseSchema])
    @paginate(PageNumberPagination, page_size=20)
    def get_all_chef_profiles(self, sort_by: str = "rating_desc"):
        """        
        [CUSTOMER] Dùng trong trang home, Lấy profile của tất cả các chef
        """
        return self.service.get_all_chef_profiles(sort_by=sort_by)
    
    
    
@api(prefix_or_class="customer-profiles", tags=["CustomerProfile"], auth=AuthBear())
class CustomerProfileController(Controller):
    def __init__(self, service: CustomerService) -> None:
        self.service = service

    @get("/", response=CustomerFullProfileSchema)
    def get_customer_profile(self, request: AuthenticatedRequest):
        """        
        [CUSTOMER] Lấy thông tin profile của customer
        """
        return self.service.get_customer_profile(user=request.user)

    @patch("/", response=CustomerFullProfileSchema)
    # @require_group(UserTypeEnum.CUSTOMER)
    def update_customer_profile(
        self,
        request: AuthenticatedRequest,
        payload: CustomerProfileUpdateSchema
    ):
        return self.service.update_customer_profile(user=request.user, payload=payload)

    @post("/onboard", response=CustomerFullProfileSchema)
    def onboard_customer_profile(
        self,
        request: AuthenticatedRequest,
        payload: CustomerOnboardingSchema,
    ):
        return self.service.onboard_customer_profile(user=request.user, payload=payload)
    
    #soft delete địa chỉ của customer, không xóa hẳn trong db, chỉ đánh dấu deleted=True
    @patch("/addresses/{address_id}/delete", response=bool)
    # @require_group(UserTypeEnum.CUSTOMER)
    def soft_delete_customer_address(self, request: AuthenticatedRequest, address_id: int):
        """        
        [CUSTOMER] Xóa địa chỉ của customer (soft delete)
        """
        return self.service.soft_delete_customer_address(user=request.user, address_id=address_id)
        
    @get("/addresses",response=List[CustomerAddressResponse])
    def get_customer_address(self, request: AuthenticatedRequest):
        """        
        [CUSTOMER] Lấy địa chỉ của customer
        """
        return self.service.get_customer_address(user=request.user)
    
    @get("/addresses/get-one", response=CustomerAddressResponse)
    def get_one_customer_address(self, request: AuthenticatedRequest):
        """        
        [CUSTOMER] Lấy một địa chỉ của customer
        """
        return self.service.get_one_customer_address(user=request.user)
    
    @post("/addresses", response=CustomerAddressDetailResponse)
    def create_new_customer_address(self, request: AuthenticatedRequest, payload: CustomerAddressRequest):
        """        
        [CUSTOMER] Tạo địa chỉ của customer
        """
        return self.service.create_new_customer_address(user=request.user, payload=payload)
    
    @get("/favorite-dishes", response=List[DishResponse])
    def get_favorite_dishes(self, request: AuthenticatedRequest):
        """        
        [CUSTOMER] Lấy danh sách món ăn yêu thích
        """
        return self.service.get_favorite_dishes(user=request.user)
    # @get("/favorite-dish/{dish_uid}", response=DishResponse)
    # def get_favorite_dish(self, request: AuthenticatedRequest, dish_uid: str):
    #     """        
    #     [CUSTOMER] Lấy một món ăn yêu thích theo dish_uid
    #     """
    #     return self.service.get_favorite_dish(user=request.user, dish_uid=dish_uid)
    # thêm món ăn yêu thích
    @post("/favorite-dish/{dish_uid}", response=DishResponse)
    def add_favorite_dish(self, request: AuthenticatedRequest, dish_uid: str):
        """        
        [CUSTOMER] Thêm món ăn yêu thích
        """
        return self.service.add_favorite_dish(user=request.user, dish_uid=dish_uid)
    
    @patch("/favorite-dish/{dish_uid}", response=bool)
    def remove_favorite_dish(self, request: AuthenticatedRequest, dish_uid: str):
        """        
        [CUSTOMER] Xóa món ăn yêu thích
        """
        return self.service.remove_favorite_dish(user=request.user, dish_uid=dish_uid)

    @get("/addresses/{address_id}", response=CustomerAddressDetailResponse)
    def get_one_customer_address_by_id(self, request: AuthenticatedRequest, address_id: int):
        """        
        [CUSTOMER] Lấy một địa chỉ của customer theo address_id
        """
        return self.service.get_one_customer_address_by_id(user=request.user, address_id=address_id)
    
    @put("/addresses/{address_id}/set-default")
    def set_default_address(self, request: AuthenticatedRequest, address_id: int):
        """
        [CUSTOMER] Thiết lập một địa chỉ làm địa chỉ mặc định
        """
        return self.service.set_default_customer_address(
            user=request.user, 
            address_id=address_id
        )

@api(prefix_or_class="chef-payment", tags=["Chef Payment"], auth=AuthBear())
class ChefPaymentController(Controller):
    def __init__(self, service: ChefPaymentService) -> None:
        self.service = service
    
    @post("/", response=ChefPaymentInfoResponse)
    @require_group(UserTypeEnum.CHEF)
    def create_or_update_payment_info(self, request: AuthenticatedRequest, payload: ChefPaymentInfoRequest):
        """
        [CHEF] Create or update chef payment information
        
        Chef must provide bank account details to receive payouts from orders.
        """
        payment_info = self.service.create_or_update_payment_info(
            user=request.user, 
            payload=payload
        )
        
        # Mask account number (show only last 4 digits)
        masked_account = self.service.mask_account_number(payment_info.bank_account_number)
        
        return ChefPaymentInfoResponse(
            bank_name=payment_info.bank_name,
            bank_code=payment_info.bank_code,
            bank_account_number=masked_account,
            bank_account_name=payment_info.bank_account_name,
            bank_branch=payment_info.bank_branch,
            is_verified=payment_info.is_verified,
            verified_at=payment_info.verified_at.isoformat() if payment_info.verified_at else None,
            created_at=payment_info.created_at.isoformat(),
            updated_at=payment_info.updated_at.isoformat()
        )

    @get("/", response=ChefPaymentInfoResponse)
    @require_group(UserTypeEnum.CHEF)
    def get_payment_info(self, request: AuthenticatedRequest):
        """
        [CHEF] Get chef's payment information
        """
        payment_info = self.service.get_payment_info(user=request.user)
        
        # Mask account number
        masked_account = self.service.mask_account_number(payment_info.bank_account_number)
        
        return ChefPaymentInfoResponse(
            bank_name=payment_info.bank_name,
            bank_code=payment_info.bank_code,
            bank_account_number=masked_account,
            bank_account_name=payment_info.bank_account_name,
            bank_branch=payment_info.bank_branch,
            is_verified=payment_info.is_verified,
            verified_at=payment_info.verified_at.isoformat() if payment_info.verified_at else None,
            created_at=payment_info.created_at.isoformat(),
            updated_at=payment_info.updated_at.isoformat()
        )

    @patch("/")
    @require_group(UserTypeEnum.CHEF)
    def delete_payment_info(self, request: AuthenticatedRequest):
        """
        [CHEF] Delete chef's payment information
        """
        self.service.delete_payment_info(user=request.user)
        return {"success": True, "message": "Payment information deleted"}



@api(prefix_or_class="chef-payment", tags=["Chef Payment"], auth=AuthBear())
class ChefPaymentController(Controller):
    def __init__(self, service: ChefPaymentService) -> None:
        self.service = service
    
    @post("/", response=ChefPaymentInfoResponse)
    @require_group(UserTypeEnum.CHEF)
    def create_or_update_payment_info(self, request: AuthenticatedRequest, payload: ChefPaymentInfoRequest):
        """
        [CHEF] Create or update chef payment information
        
        Chef must provide bank account details to receive payouts from orders.
        """
        payment_info = self.service.create_or_update_payment_info(
            user=request.user, 
            payload=payload
        )
        
        # Mask account number (show only last 4 digits)
        masked_account = self.service.mask_account_number(payment_info.bank_account_number)
        
        return ChefPaymentInfoResponse(
            bank_name=payment_info.bank_name,
            bank_code=payment_info.bank_code,
            bank_account_number=masked_account,
            bank_account_name=payment_info.bank_account_name,
            bank_branch=payment_info.bank_branch,
            is_verified=payment_info.is_verified,
            verified_at=payment_info.verified_at.isoformat() if payment_info.verified_at else None,
            created_at=payment_info.created_at.isoformat(),
            updated_at=payment_info.updated_at.isoformat()
        )

    @get("/", response=ChefPaymentInfoResponse)
    def get_payment_info(self, request: AuthenticatedRequest):
        """
        [CHEF] Get chef's payment information
        """
        payment_info = self.service.get_payment_info(user=request.user)
        
        # Mask account number
        masked_account = self.service.mask_account_number(payment_info.bank_account_number)
        
        return ChefPaymentInfoResponse(
            bank_name=payment_info.bank_name,
            bank_code=payment_info.bank_code,
            bank_account_number=masked_account,
            bank_account_name=payment_info.bank_account_name,
            bank_branch=payment_info.bank_branch,
            is_verified=payment_info.is_verified,
            verified_at=payment_info.verified_at.isoformat() if payment_info.verified_at else None,
            created_at=payment_info.created_at.isoformat(),
            updated_at=payment_info.updated_at.isoformat()
        )

    @delete("/")
    def delete_payment_info(self, request: AuthenticatedRequest):
        """
        [CHEF] Delete chef's payment information
        """
        self.service.delete_payment_info(user=request.user)
        return {"success": True, "message": "Payment information deleted"}
