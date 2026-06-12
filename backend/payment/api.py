from uuid import UUID
from ninja import Query
from django.http import HttpRequest, JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
import json
from django.utils import timezone
from django.contrib.auth import get_user_model
from utils.enums import UserTypeEnum, PaymentStatus
from exceptions.users import UserNotFound
from utils.permissions.decorators import require_group
from utils.router.authenticate import AuthBear
from utils.router.controller import Controller, api, get, post
from utils.types import AuthenticatedRequest
from payment.services import PaymentService
from payment.schemas.responses import (
    PaymentStatusResponse, 
    PaymentCallbackResponse,
    PaymentInfoResponse,
    CancelPaymentResponse,
    PaymentInvoicesResponse,
    CreatePaymentResponse,
    PaymentData
)
from payment.schemas.requests import CancelPaymentRequest, CreatePaymentRequest
from payment.schemas.responses import (
    PaymentStatusResponse, 
    PaymentCallbackResponse,
    PaymentInfoResponse,
    CancelPaymentResponse,
    PaymentInvoicesResponse,
    CreatePaymentResponse,
    PaymentData,
    CustomerPaymentInfoResponse,
    InternalWalletSummaryResponse,
    WalletWithdrawResponse,
    ChefBalanceSummaryResponse,
    SettlementReportResponse,
    CODSettlementResponse,
    PaymentOtpSessionResponse,
)
from payment.schemas.requests import (
    CustomerPaymentInfoRequest,
    WalletWithdrawRequest,
    PaymentOtpVerifyRequest,
    WithdrawConfirmRequest,
)


@api(prefix_or_class="payment", tags=["Payment"])
class PaymentController(Controller):
    def __init__(self, service: PaymentService) -> None:
        self.service = service
    
    @post("/create", response=CreatePaymentResponse, auth=AuthBear())
    def create_payment(self, request: AuthenticatedRequest, payload: CreatePaymentRequest):
        """
        Create payment transaction for checkout
        Endpoint: POST /api/payment/create
        
        Body:
        {
            "checkout_uid": "uuid",
            "payment_method": "PAYOS",
            "buyer_name": "...",
            "buyer_email": "...",
            "buyer_phone": "...",
            "items": [...]
        }
        """
        try:
            # Create payment transaction
            payment = self.service.create_payment(
                checkout_uid=payload.checkout_uid,
                payment_method=payload.payment_method,
                bank_code=payload.bank_code,
                language=payload.language or "vn"
            )
            
            # Prepare response data
            state = getattr(payment, "state", None)
            payment_data = PaymentData(
                payment_uid=payment.uid,
                checkout_uid=payment.checkout.uid,
                payment_method=payment.payment_method,
                amount=payment.amount,
                status=state.status if state else PaymentStatus.PENDING,
                payment_url=state.payment_url if state else None,
                qr_code=state.gateway_response.get('qr_code') if state and state.gateway_response else None,
                payment_link_id=state.payos_payment_link_id if state else None,
                order_code=payment.payos_order_code,
                account_number=state.gateway_response.get('account_number') if state and state.gateway_response else None,
                account_name=state.gateway_response.get('account_name') if state and state.gateway_response else None,
                transaction_id=(state.transaction_id if state else None) or (state.payos_payment_link_id if state else None),
                settlement=state.gateway_response.get('settlement') if state and state.gateway_response else None
            )
            
            return CreatePaymentResponse(
                success=True,
                message="Payment created successfully",
                data=payment_data
            )
        except ValueError as e:
            return CreatePaymentResponse(
                success=False,
                message=str(e),
                data=None
            )
        except Exception as e:
            return CreatePaymentResponse(
                success=False,
                message=f"Internal error: {str(e)}",
                data=None
            )
    
    @get("/{payment_uid}/status", response=PaymentStatusResponse, auth=AuthBear())
    def get_payment_status(self, request: AuthenticatedRequest, payment_uid: UUID):
        """Get payment transaction status"""
        payment = self.service.get_payment_status(payment_uid)
        state = getattr(payment, "state", None)
        return PaymentStatusResponse(
            payment_uid=payment.uid,
            transaction_id=(state.transaction_id if state else None) or (state.payos_payment_link_id if state else None) or str(payment.uid),
            status=state.status if state else PaymentStatus.PENDING,
            amount=payment.amount,
            payment_method=payment.payment_method,
            created_at=payment.created_at,
            paid_at=state.paid_at if state else None,
            settlement=state.gateway_response.get('settlement') if state and state.gateway_response else None
        )
    
    @get("/order/{order_code}/info", response=PaymentInfoResponse, auth=AuthBear())
    def get_payment_info(self, request: AuthenticatedRequest, order_code: int):
        """
        Get payment information by order code (PayOS)
        Endpoint: GET /api/payment/order/{order_code}/info
        """
        result = self.service.get_payment_info_by_order_code(order_code)
        return PaymentInfoResponse(**result)
    
    @post("/{payment_uid}/cancel", response=CancelPaymentResponse, auth=AuthBear())
    def cancel_payment(
        self, 
        request: AuthenticatedRequest, 
        payment_uid: UUID,
        payload: CancelPaymentRequest
    ):
        """
        Cancel payment transaction
        Endpoint: POST /api/payment/{payment_uid}/cancel
        Body: {"cancellation_reason": "..."}
        """
        result = self.service.cancel_payment(
            payment_uid=payment_uid,
            reason=payload.cancellation_reason
        )
        return CancelPaymentResponse(**result)
    
    @get("/{payment_uid}/invoices", response=PaymentInvoicesResponse, auth=AuthBear())
    def get_payment_invoices(self, request: AuthenticatedRequest, payment_uid: UUID):
        """
        Get payment invoices (PayOS)
        Endpoint: GET /api/payment/{payment_uid}/invoices
        """
        result = self.service.get_payment_invoices(payment_uid)
        return PaymentInvoicesResponse(**result)

    @post('/customer/bank-info', response=PaymentOtpSessionResponse, auth=AuthBear())
    # @require_group(UserTypeEnum.CUSTOMER)
    def upsert_customer_bank_info(self, request: AuthenticatedRequest, payload: CustomerPaymentInfoRequest):
        """Save bank info and send OTP to email for verification."""
        result = self.service.request_bank_verify_otp(request.user, payload)
        return PaymentOtpSessionResponse(
            reset_session_token=result["reset_session_token"],
            message="OTP sent to your email. Please verify to activate bank account.",
        )

    @post('/customer/bank-info/verify-otp', response=CustomerPaymentInfoResponse, auth=AuthBear())
    # @require_group(UserTypeEnum.CUSTOMER)
    def verify_bank_info_otp(self, request: AuthenticatedRequest, payload: PaymentOtpVerifyRequest):
        """Verify OTP to confirm bank account ownership (sets is_verified=True)."""
        payment_info = self.service.verify_bank_info_otp(
            user=request.user,
            reset_session_token=payload.reset_session_token,
            otp=payload.otp,
        )
        return CustomerPaymentInfoResponse(
            bank_name=payment_info.bank_name,
            bank_code=payment_info.bank_code,
            bank_account_number=payment_info.bank_account_number,
            bank_account_name=payment_info.bank_account_name,
            bank_branch=payment_info.bank_branch,
            is_verified=payment_info.is_verified,
            verified_at=payment_info.verified_at.isoformat() if payment_info.verified_at else None,
            created_at=payment_info.created_at.isoformat(),
            updated_at=payment_info.updated_at.isoformat(),
        )

    @get('/customer/bank-info', response=CustomerPaymentInfoResponse, auth=AuthBear())
    # @require_group(UserTypeEnum.CUSTOMER)
    def get_customer_bank_info(self, request: AuthenticatedRequest):
        payment_info = self.service.get_customer_payment_info(request.user)
        return CustomerPaymentInfoResponse(
            bank_name=payment_info.bank_name,
            bank_code=payment_info.bank_code,
            bank_account_number=payment_info.bank_account_number,
            bank_account_name=payment_info.bank_account_name,
            bank_branch=payment_info.bank_branch,
            is_verified=payment_info.is_verified,
            verified_at=payment_info.verified_at.isoformat() if payment_info.verified_at else None,
            created_at=payment_info.created_at.isoformat(),
            updated_at=payment_info.updated_at.isoformat(),
        )

    @get('/wallet/me', response=InternalWalletSummaryResponse, auth=AuthBear())
    def get_my_wallet(self, request: AuthenticatedRequest):
        summary = self.service.get_internal_wallet_summary(request.user)
        return InternalWalletSummaryResponse(**summary)

    @post('/wallet/me/withdraw', response=PaymentOtpSessionResponse, auth=AuthBear())
    def withdraw_my_wallet(self, request: AuthenticatedRequest, payload: WalletWithdrawRequest):
        """Validate withdrawal request and send OTP to email."""
        result = self.service.request_withdraw_otp(request.user, payload.amount)
        return PaymentOtpSessionResponse(
            reset_session_token=result["reset_session_token"],
            message="OTP sent to your email. Please confirm the withdrawal.",
        )

    @post('/wallet/me/withdraw/confirm', response=WalletWithdrawResponse, auth=AuthBear())
    def confirm_withdraw(self, request: AuthenticatedRequest, payload: WithdrawConfirmRequest):
        """Verify OTP then execute the wallet withdrawal."""
        result = self.service.confirm_withdraw_with_otp(
            user=request.user,
            reset_session_token=payload.reset_session_token,
            otp=payload.otp,
        )
        return WalletWithdrawResponse(
            success=result.get('success', False),
            message=result.get('message', result.get('error', '')),
            amount=result.get('amount'),
            status=result.get('status', 'FAILED'),
            payout_id=result.get('payout_id'),
            reference_id=result.get('reference_id'),
            bank_account=result.get('bank_account'),
            error=result.get('error'),
        )

    @get('/chef/{chef_id}/balance', response=ChefBalanceSummaryResponse, auth=AuthBear())
    def get_chef_balance(self, request: AuthenticatedRequest, chef_id: int):
        """Return chef balance summary (COD and PayOS pending)"""
        user_model = get_user_model()
        #print user groups
        print("User groups:", user_model.objects.filter(id=chef_id).values_list('groups__name', flat=True))
        try:
            chef = user_model.objects.get(
                id=chef_id,
                groups__name=UserTypeEnum.CHEF  # hoặc "CHEF"
            )
        except user_model.DoesNotExist:
            from ninja.errors import HttpError
            raise HttpError(404, 'Chef not found or not a chef')

        summary = self.service.get_chef_balance_summary(chef)
        return ChefBalanceSummaryResponse(**summary)

    @post('/chef/{chef_id}/cod/settle', response=CODSettlementResponse, auth=AuthBear())
    def settle_chef_cod(self, request: AuthenticatedRequest, chef_id: int):
        """Trigger COD settlement for a chef (batch payout)"""
        user_model = get_user_model()
        #print user groups
        print("User groups:", user_model.objects.filter(id=chef_id).values_list('groups__name', flat=True))
        try:
            chef = user_model.objects.get(
                id=chef_id,
                groups__name=UserTypeEnum.CHEF  # hoặc "CHEF"
            )
        except user_model.DoesNotExist:
            from ninja.errors import HttpError
            raise HttpError(404, 'Chef not found or not a chef')
        result = self.service.settle_cod_balance_for_chef(chef)
        if not result.get('success'):
            return CODSettlementResponse(
                success=False,
                chef_id=chef.id,
                chef_email=chef.email,
                settled_amount=0,
                order_count=0,
                settled_at=timezone.now().isoformat(),
                message=result.get('error')
            )

        return CODSettlementResponse(
            success=True,
            chef_id=result.get('chef_id'),
            chef_email=result.get('chef_email'),
            settled_amount=result.get('settled_amount'),
            order_count=result.get('order_count'),
            settled_at=result.get('settled_at')
        )

@csrf_exempt
def payos_webhook(request: HttpRequest):
    """
    PayOS Webhook endpoint
    This is called by PayOS server after payment
    """
    # import time
    # from datetime import datetime
    
    # t2_start = time.time()
    # t2_start_utc = datetime.utcnow().isoformat()
    
    if request.method != "POST":
        return HttpResponse(status=200)

    # PayOS test webhook (body rỗng)
    if not request.body:
        return HttpResponse(status=200)

    try:
        data = json.loads(request.body)
        
        # 📊 [PERFORMANCE MEASUREMENT] T2 = Backend receives webhook
        # print("\n" + "="*80)
        # print("🕐 [PAYOS WEBHOOK] ===== PERFORMANCE MEASUREMENT START =====")
        # print(f"T2 (Backend receives webhook): {t2_start_utc}")
        # print(f"Webhook data: {data}")
        # print("="*80)

        payment_service = PaymentService()
        payment_service.handle_payos_webhook(data)
        # payment_service.handle_payos_webhook(data, t2_webhook_received=t2_start)

    except Exception as e:
        # LOG nhưng KHÔNG FAIL
        print("Webhook error:", e)

    # 🚨 LUÔN TRẢ 200
    return HttpResponse(status=200)


@csrf_exempt
def payos_return(request: HttpRequest):
    """
    PayOS return URL endpoint
    This is where user is redirected after payment
    """
    if request.method != 'GET':
        return JsonResponse({'success': False, 'message': 'Invalid request method'})
    
    # Get query parameters
    return_data = dict(request.GET.items())
    
    # Extract payment info from query params
    code = return_data.get('code')
    order_code = return_data.get('orderCode')
    
    if code == '00':
        sync_result = None
        if order_code:
            try:
                normalized_order_code = str(order_code[0]) if isinstance(order_code, list) else str(order_code)
                sync_result = PaymentService().sync_payment_by_order_code(int(normalized_order_code))
            except (TypeError, ValueError):
                sync_result = {
                    'success': False,
                    'error': 'Invalid order_code returned from PayOS'
                }

        return JsonResponse({
            'success': True,
            'message': 'Payment successful',
            'order_code': order_code,
            'sync_result': sync_result,
        })
    elif code == '01':
        return JsonResponse({
            'success': False,
            'message': 'Payment cancelled',
            'order_code': order_code
        })
    else:
        return JsonResponse({
            'success': False,
            'message': 'Payment failed',
            'code': code,
            'order_code': order_code
        })
