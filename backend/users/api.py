from typing import Optional

from ninja import Schema
from exceptions.auth import InvalidOrExpiredToken
from exceptions.users import PasswordIncorrect, UserNotFound
from profile.models import ChefProfile
from exceptions.users import PasswordIncorrect, UserNotFound, AccountDeactivated
from utils.router.controller import Controller, api, get, post, put
from utils.types import AuthenticatedRequest, UnauthenticatedRequest

from .schemas import (
    LoginResponseSchema,
    LoginSchema,
    LogoutRequest,
    SignUpSchema,
    EmailChangeRequest,
    PasswordChangeRequest,
    PasswordForgetRequest,
    OtpSessionResponse,
    PasswordVerifyOtpRequest,
    PasswordNewRequest,
    UpdateMeSchema,
    UserSchema,
    CustomerToChefSchema,
    RefreshTokenRequest,
    TokenPairResponse,
)
from profile.schemas.responses import ChefProfileDetailResponeSchema
from .services import Service

from ninja.responses import Response
@api(prefix_or_class="auth", tags=["Authenticate"], auth=None)
class AuthenticateAPI(Controller):
    def __init__(self, service: Service):
        self.service = service

    @post("/login", response=LoginResponseSchema, exceptions=(AccountDeactivated,))
    def login(self, request: UnauthenticatedRequest, data: LoginSchema):
        user, access_token, refresh_token = self.service.login(
            request=request, email=data.email, password=data.password
        )
        self.logger.info(f"> [LOGIN] {user}")
        return LoginResponseSchema(
            access_token=access_token,
            refresh_token=refresh_token,
            user=UserSchema.from_orm(user),
        )

    @post("/signup", response=OtpSessionResponse)
    def signup(self, request: UnauthenticatedRequest, data: SignUpSchema):
        otp_record = self.service.signup(data)
        self.logger.info(f"> [SIGNUP] {data.email}")
        return otp_record

    @get("/me", auth=True, response=UserSchema)
    def get_me(self, request: AuthenticatedRequest):
        return self.service.get_me(user=request.user)

    # @put("/logout", auth=True)
    # def logout(self, request: AuthenticatedRequest):
    #     return self.service.logout(request=request)


    @put("/logout", auth=True)
    def logout(self, request, payload: LogoutRequest | None = None):
        refresh_token = payload.refresh_token if payload else None
        self.service.logout(request=request, refresh_token=refresh_token)

        return Response({
            "data": True,
            "message_code": "SUCCESS",
            "message": "Logout success"
        })

    @post("/refresh", response=TokenPairResponse, auth=None)
    def refresh(self, request: UnauthenticatedRequest, payload: RefreshTokenRequest):
        access_token, refresh_token = self.service.refresh(refresh_token=payload.refresh_token)
        return TokenPairResponse(access_token=access_token, refresh_token=refresh_token)
    @put("/me", auth=True, response=UserSchema)
    def update_me(self, request: AuthenticatedRequest, data: UpdateMeSchema):
        return self.service.update_me(user=request.user, full_name=data.full_name)

    @put("password/change", auth=True, response=bool, exceptions=(PasswordIncorrect,))
    def change_password(
        self, request: AuthenticatedRequest, payload: PasswordChangeRequest
    ):
        self.service.change_password(user=request.user, payload=payload)
        return True

    @post("password/forget", response=OtpSessionResponse, exceptions=(UserNotFound,))
    def forget_password(self, payload: PasswordForgetRequest):
        return self.service.forget_password(email=payload.email)
    
    #bước 2 của signup, forget password
    @post("/verify-otp", response=bool,exceptions=(InvalidOrExpiredToken,))
    def verify_otp(self, payload: PasswordVerifyOtpRequest):
        self.service.verify_otp(
            reset_session_token=payload.reset_session_token,
            otp=payload.otp
        )
        return True

    @post("/email-change/request", auth=True, response=OtpSessionResponse)
    def request_email_change(self, request: AuthenticatedRequest, payload: EmailChangeRequest):
        return self.service.request_email_change(user=request.user, new_email=payload.new_email)

    @post("/email-change/verify", auth=True, response=bool, exceptions=(InvalidOrExpiredToken,))
    def verify_email_change(self, request: AuthenticatedRequest, payload: PasswordVerifyOtpRequest):
        return self.service.verify_email_change(
            user=request.user,
            reset_session_token=payload.reset_session_token,
            otp=payload.otp,
        )

    @put("password/reset", response=bool, exceptions=(InvalidOrExpiredToken,))
    def reset_password(self, payload: PasswordNewRequest):
        return self.service.reset_password(payload=payload)
    
    @post("/upgrade-to-chef", auth=True, response=ChefProfileDetailResponeSchema)
    def upgrade_to_chef(self, request: AuthenticatedRequest, payload: CustomerToChefSchema):
        """API để customer chuyển thành chef (yêu cầu thông tin thanh toán)"""
        return self.service.upgrade_to_chef(user=request.user, payload=payload)
        
    class CheckChefResponse(Schema):
        is_chef: bool
        chef_id: Optional[int] = None
    
    @get("/is-chef", auth = True, response = CheckChefResponse)
    def check_is_chef(self, request: AuthenticatedRequest):
        is_chef = request.user.groups.filter(name = 'CHEF').exists() 
        chef_id = None
        if is_chef:
            # KỊCH BẢN A: Nếu bảng Chef là một bảng riêng biệt liên kết OneToOne với User
            # (Giả sử related_name của bạn là 'chef' hoặc 'chef_profile')
            if hasattr(request.user, 'chef'):
                chef_id = request.user.chef.id
            
            # ---------------------------------------------------------
            # KỊCH BẢN B: Nếu hệ thống của bạn không có bảng Chef riêng, 
            # mà chef_id thực chất chính là user_id
            # chef_id = request.user.id
            # ---------------------------------------------------------
            
        return {
            "is_chef": is_chef, 
            "chef_id": chef_id
        }

