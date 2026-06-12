from typing import Tuple

from django.contrib import auth as django_auth
from django.http import HttpRequest

from users.schemas import PasswordChangeRequest, PasswordNewRequest, SignUpSchema, CustomerToChefSchema
from exceptions.auth import InvalidOrExpiredToken, InvalidOtp, ConfirmPasswordNotMatch
from exceptions.users import PasswordIncorrect, UserNotFound, EmailAlreadyInUse, BankAccountNameRequired, BankAccountNumberRequired, BankNameRequired, BankAccountNameRequired
from utils.services.base import BaseService
from utils.services.email.client import EmailClient
from utils.services.email.template import EmailTemplate
from utils.types import AuthenticatedRequest, TUser
from django.contrib.auth.models import Group
from django.db import transaction
from profile.services import ChefPaymentService, ProfileService
from profile.models import CustomerProfile
from profile.schemas.requests import ChefProfileDetailSchema
from profile.schemas.chef_payment import ChefPaymentInfoRequest
from utils.enums import UserTypeEnum
from .queries import Query


class Service(BaseService):
    auth = django_auth

    def __init__(self):
        self.query = Query()
        self.email_template = EmailTemplate()
        self.email_client = EmailClient()
        self.profile_service = ProfileService()
        self.chef_payment_service = ChefPaymentService()
        
    def signup(self, data: SignUpSchema):
        user = self._get_or_create_inactive_user(data)
        otp_record = self._send_signup_otp(user)
        return otp_record

    def _get_or_create_inactive_user(self, data: SignUpSchema) -> TUser:
        existing_user = self.query.get_user_by_email(email=data.email, only_active=True)
        if existing_user:
            raise EmailAlreadyInUse

        user = self.query.get_user_by_email(email=data.email, only_active=False)
        if not user:
            user = self.query.create_user(
                email=data.email,
                password=data.password,
                firstname=data.firstname,
                lastname=data.lastname,
                phone_number=data.phone_number,
            )
            user.is_active = False
            user.save()
        return user

    def _send_signup_otp(self, user: TUser):
        self.query.inactive_otp_token(user=user)
        otp_record, plain_otp = self.query.create_otp(user=user, purpose="SIGNUP")
        template = self.email_template.send_verification_email(
            user=user, otp=plain_otp, purpose="SIGNUP"
        )
        self.email_client.send(messages=[template])
        return otp_record

    def login(
        self, request: HttpRequest, email: str, password: str
    ) -> Tuple[TUser, str, str]:
        user = self.query.get_user_by_email_and_password(
            email=email,
            password=password,
        ) 
        self.auth.login(request=request, user=user)
        access_token, refresh_token = self.query.generate_tokens(user_id=user.id)
        return user, access_token, refresh_token

    def get_me(self, user: TUser) -> TUser:
        return user

    def logout(self, request: AuthenticatedRequest, refresh_token: str | None = None) -> bool:
        self.query.logout(user_id=request.user.id, refresh_token=refresh_token)
        self.auth.logout(request=request)
        return True

    def update_me(self, user: TUser, full_name: str) -> TUser:
        return self.query.update_me(user=user, full_name=full_name)

    def refresh(self, refresh_token: str) -> tuple[str, str]:
        return self.query.refresh_tokens(refresh_token=refresh_token)

    def change_password(self, user: TUser, payload: PasswordChangeRequest):
        is_password_correct = self.query.check_password(
            user=user, password=payload.old_password
        )
        if not is_password_correct:
            raise PasswordIncorrect
        user = self.query.change_password(user=user, password=payload.new_password)

        template = self.email_template.change_password(user=user)
        self.email_client.send(messages=[template])

    #otp
    def forget_password(self, email: str):
        user = self.query.get_user_by_email(email=email)
        if not user:
            raise UserNotFound

        # Hủy OTP cũ
        self.query.inactive_otp_token(user=user)

        otp_record, plain_otp = self.query.create_otp(user=user, purpose="RESET_PASSWORD")

        template = self.email_template.send_verification_email(user=user, otp=plain_otp, purpose="RESET_PASSWORD")
        self.email_client.send(messages=[template])

        return otp_record

    def request_email_change(self, user: TUser, new_email: str):
        existing_user = self.query.get_user_by_email(email=new_email, only_active=True)
        if existing_user and existing_user != user:
            raise EmailAlreadyInUse

        self.query.inactive_otp_token(user=user)
        otp_record, plain_otp = self.query.create_otp(
            user=user,
            purpose="EMAIL_CHANGE",
            target_email=new_email,
        )

        template = self.email_template.send_verification_email(
            user=user,
            otp=plain_otp,
            purpose="EMAIL_CHANGE",
            to_email=new_email,
        )
        self.email_client.send(messages=[template])
        return otp_record

    def verify_email_change(self, user: TUser, reset_session_token: str, otp: str) -> bool:
        record = self.query.get_otp_record(reset_session_token)

        if not record or not record.active or record.user != user:
            raise InvalidOrExpiredToken
        if record.purpose != "EMAIL_CHANGE":
            raise InvalidOrExpiredToken
        if record.otp != otp:
            raise InvalidOtp
        if not record.target_email:
            raise InvalidOrExpiredToken

        existing_user = self.query.get_user_by_email(email=record.target_email, only_active=True)
        if existing_user and existing_user != user:
            raise EmailAlreadyInUse

        user.email = record.target_email
        user.save(update_fields=["email"])

        record.active = False
        record.otp_verified = True
        record.save(update_fields=["active", "otp_verified"])
        return True
        


    # người dùng nhập OTP để xác thực
    # def verify_otp(self, reset_session_token: str, otp: str) -> bool:
    #     record = self.query.get_otp_record(reset_session_token)

    #     if not record or not record.active:
    #         raise InvalidOrExpiredToken
    #     if record.otp != otp:
    #         raise InvalidOtp
    #     # Nếu là OTP cho signup thì active user, và unactive OTP
    #     if record.purpose == "SIGNUP":
    #         record.user.is_active = True
    #         record.active = False
    #         record.user.save()

    #         # Ensure every verified customer has a profile record.
    #         CustomerProfile.objects.get_or_create(user=record.user)
            
    #         # Đảm bảo user được gán vào group CUSTOMER
    #         self.query.assign_user_to_group(record.user, UserTypeEnum.CUSTOMER)

    #     # Nếu là OTP reset password thì chỉ đánh dấu verified, 
    #     # chờ API reset_password mới xử lý tiếp
    #     self.query.mark_otp_verified(record)

    #     return True

    def verify_otp(self, reset_session_token: str, otp: str):
        from users.models import OTP_MAX_ATTEMPTS

        record = self.query.get_otp_record(reset_session_token)

        if not record:
            raise InvalidOrExpiredToken

        if record.otp_verified:
            raise InvalidOtp("OTP already used")

        if record.is_expired():
            record.active = False
            record.save(update_fields=["active"])
            raise InvalidOrExpiredToken

        if record.attempts >= OTP_MAX_ATTEMPTS:
            record.active = False
            record.save(update_fields=["active"])
            raise InvalidOtp("Max OTP attempts exceeded")

        if not record.verify(otp):
            raise InvalidOtp

        record.otp_verified = True
        record.active = False
        record.save(update_fields=["otp_verified", "active"])

        if record.purpose == "SIGNUP":
            user = record.user
            user.is_active = True
            user.save()

            CustomerProfile.objects.get_or_create(user=user)
            self.query.assign_user_to_group(user, UserTypeEnum.CUSTOMER)

        return True
    
# Người dùng đặt lại mật khẩu mới
    def reset_password(self, payload: PasswordNewRequest):
        if payload.new_password != payload.confirm_password:
            raise ConfirmPasswordNotMatch

        # 2. Lấy record qua reset_session_token
        record = self.query.get_otp_record(payload.reset_session_token)
        if not record or not record.otp_verified or record.is_expired():
            if not record:
                print("not record")
            elif not record.otp_verified:
                print("not verified")
            elif record.is_expired():
                print("is expired")
            raise InvalidOrExpiredToken

        # 3. Update mật khẩu user
        self.query.reset_password(record=record, payload=payload)
        
        return True
    
    def upgrade_to_chef(self, user: TUser, payload: CustomerToChefSchema):
        """Upgrade customer thành chef với thông tin thanh toán"""

        # Kiểm tra user phải là CUSTOMER
        if not user.groups.filter(name=UserTypeEnum.CUSTOMER).exists():
            raise Exception("Only CUSTOMER can upgrade to CHEF")

        # Upgrade with transaction (ensure both upgrade and payment info creation succeed)
        with transaction.atomic():

            chef_profile = self.profile_service.create_chef_profile(
                user=user,
                payload=payload.chef_profile)
            self.chef_payment_service.create_or_update_payment_info(
                user=user,
            payload=payload.chef_payment
        )
            # Upgrade user to chef
            user = self.query.upgrade_customer_to_chef(user=user)

        
        return chef_profile
