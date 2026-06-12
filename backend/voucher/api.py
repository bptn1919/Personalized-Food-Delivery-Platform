from uuid import UUID
from ninja import Query
from utils.router.authenticate import AuthBear
from utils.router.controller import Controller, api, get, post, patch, delete
from utils.types import AuthenticatedRequest
from voucher.schemas import (
    CreateVoucherSchema,
    UpdateVoucherSchema,
    ValidateVoucherSchema,
    VoucherDetailSchema,
    VoucherListSchema,
)
from voucher.schemas.response import ValidateVoucherResponseSchema
from voucher.services import VoucherService
from typing import List


@api(prefix_or_class="vouchers", tags=["Voucher"], auth=AuthBear())
class VoucherController(Controller):
    """Controller quản lý Voucher - Chef tạo và quản lý voucher của mình"""
    
    def __init__(self, service: VoucherService) -> None:
        self.service = service
    
    @post("", response=VoucherDetailSchema)
    def create_voucher(self, request: AuthenticatedRequest, payload: CreateVoucherSchema):
        """
        Tạo voucher mới (Chef only)
        
        Chef tạo voucher áp dụng cho các món ăn của mình.
        Voucher chỉ giảm giá trị món ăn, không áp dụng cho phí vận chuyển.
        """
        return self.service.create_voucher(chef=request.user, payload=payload)

    
    @get("", response=List[VoucherListSchema])
    def list_my_vouchers(self, request: AuthenticatedRequest):
        """
        Lấy danh sách voucher của chef hiện tại
        """
        return self.service.get_my_vouchers(chef=request.user)
    
    @post("/validate", response=ValidateVoucherResponseSchema)
    def validate_voucher(self, request: AuthenticatedRequest, payload: ValidateVoucherSchema):
        """
        Validate voucher và tính số tiền giảm
        
        Body:
            code: Mã voucher
            order_amount: Giá trị đơn hàng (sub_total)
            chef_id: ID của chef (order)
        """
        is_valid, message, discount_amount = self.service.validate_voucher_for_order(
            code=payload.code,
            order_amount=payload.order_amount,
            chef_id=payload.chef_id,
            user=request.user,
        )
        
        final_amount = None
        if is_valid:
            final_amount = payload.order_amount - discount_amount
        
        return {
            "is_valid": is_valid,
            "message": message,
            "discount_amount": discount_amount if is_valid else None,
            "final_amount": final_amount,
        }
    
    @get("/chef/{chef_id}", response=List[VoucherListSchema])
    def list_vouchers_by_chef(
        self, 
        request: AuthenticatedRequest, 
        chef_id: int, 
        available_only: bool = Query(True)
    ):
        """
        Lấy danh sách voucher của một chef (cho customer xem)
        
        Params:
            chef_id: ID của chef
            available_only: Chỉ lấy voucher còn hiệu lực (default: True)
        """
        return self.service.get_vouchers_by_chef(
            chef_id=chef_id,
            available_only=available_only,
            user=request.user
        )
    
    @get("/{voucher_uid}", response=VoucherDetailSchema)
    def get_voucher(self, request: AuthenticatedRequest, voucher_uid: UUID):
        """Lấy chi tiết voucher"""
        return self.service.get_voucher_by_uid(voucher_uid)
    
    @patch("/{voucher_uid}", response=VoucherDetailSchema)
    def update_voucher(
        self, 
        request: AuthenticatedRequest, 
        voucher_uid: UUID, 
        payload: UpdateVoucherSchema
    ):
        """
        Cập nhật voucher (Chỉ chef sở hữu)
        """
        voucher = self.service.update_voucher(
            voucher_uid=voucher_uid,
            chef=request.user,
            **payload.dict(exclude_unset=True)
        )
        return voucher
    
    @delete("/{voucher_uid}", response=bool)
    def delete_voucher(self, request: AuthenticatedRequest, voucher_uid: UUID):
        """Xóa voucher (Chỉ chef sở hữu)"""
        return self.service.delete_voucher(voucher_uid=voucher_uid, chef=request.user)
        
    
    
    
    @get("/code/{code}", response=VoucherDetailSchema)
    def get_voucher_by_code(self, request: AuthenticatedRequest, code: str):
        """Lấy thông tin voucher theo mã"""
        voucher = self.service.get_voucher_by_code(code)
        return voucher
