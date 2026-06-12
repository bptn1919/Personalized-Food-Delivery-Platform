from ninja import Router
from utils.router.authenticate import AuthBear
from utils.types import AuthenticatedRequest
from profile.schemas.chef_payment import ChefPaymentInfoRequest, ChefPaymentInfoResponse
from profile.orm.chef_payment import ChefPaymentInfoORM
from profile.services import ChefPaymentService
from payment.schemas.responses import PaymentOtpSessionResponse
from payment.schemas.requests import PaymentOtpVerifyRequest

router = Router(tags=["Chef Payment"], auth=AuthBear())
_chef_payment_service = ChefPaymentService()


def _build_masked_response(payment_info) -> ChefPaymentInfoResponse:
    masked = '*' * (len(payment_info.bank_account_number) - 4) + payment_info.bank_account_number[-4:]
    return ChefPaymentInfoResponse(
        bank_name=payment_info.bank_name,
        bank_code=payment_info.bank_code,
        bank_account_number=masked,
        bank_account_name=payment_info.bank_account_name,
        bank_branch=payment_info.bank_branch,
        is_verified=payment_info.is_verified,
        verified_at=payment_info.verified_at.isoformat() if payment_info.verified_at else None,
        created_at=payment_info.created_at.isoformat(),
        updated_at=payment_info.updated_at.isoformat(),
    )


@router.post("/payment-info", response=PaymentOtpSessionResponse)
def create_or_update_payment_info(request: AuthenticatedRequest, payload: ChefPaymentInfoRequest):
    """Save/update bank info (unverified) and send OTP to email for verification."""
    result = _chef_payment_service.request_bank_verify_otp(request.user, payload)
    return PaymentOtpSessionResponse(
        reset_session_token=result["reset_session_token"],
        message="OTP sent to your email. Please verify to activate bank account.",
    )


@router.post("/payment-info/verify-otp", response=ChefPaymentInfoResponse)
def verify_payment_info_otp(request: AuthenticatedRequest, payload: PaymentOtpVerifyRequest):
    """Verify OTP to confirm bank account ownership (sets is_verified=True)."""
    payment_info = _chef_payment_service.verify_chef_bank_info_otp(
        user=request.user,
        reset_session_token=payload.reset_session_token,
        otp=payload.otp,
    )
    return _build_masked_response(payment_info)


@router.get("/payment-info", response=ChefPaymentInfoResponse)
def get_payment_info(request: AuthenticatedRequest):
    """
    Get chef's payment information
    """
    user = request.user
    payment_info = ChefPaymentInfoORM.get_by_user(user)
    
    if not payment_info:
        return {"error": "Payment information not found"}, 404
    
    # Mask account number
    masked_account = '*' * (len(payment_info.bank_account_number) - 4) + payment_info.bank_account_number[-4:]
    
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


@router.delete("/payment-info")
def delete_payment_info(request: AuthenticatedRequest):
    """
    Delete chef's payment information
    """
    user = request.user
    payment_info = ChefPaymentInfoORM.get_by_user(user)
    
    if not payment_info:
        return {"error": "Payment information not found"}, 404
    
    ChefPaymentInfoORM.delete(payment_info)
    return {"success": True, "message": "Payment information deleted"}
