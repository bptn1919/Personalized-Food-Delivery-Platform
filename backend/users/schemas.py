from typing import Optional
from django.db.models import Q
from ninja import Schema, FilterSchema
from ninja import ModelSchema
from pydantic import Field
from .models import UserOTP
from profile.schemas.requests import ChefProfileDetailSchema
from profile.schemas.chef_payment import ChefPaymentInfoRequest
from profile.schemas.chef_payment import ChefPaymentInfoResponse
from utils.schemas.fields import FilterField
from utils.enums import UserTypeEnum

class UserSchema(Schema):
    username: str
    email: str
    is_onboarded: bool = False

class SignUpSchema(Schema):
    firstname: str
    lastname: str
    email: str
    password: str
    password_confirm: str
    phone_number: str | None = None

class SignUpResponseSchema(Schema):
    id: int
    email: str
    phone_number: str | None = None

class LoginSchema(Schema):
    email: str
    password: str


class UpdateMeSchema(Schema):
    full_name: str


class CustomerToChefSchema(Schema):
    chef_profile: ChefProfileDetailSchema
    chef_payment: ChefPaymentInfoRequest

class LoginResponseSchema(Schema):
    access_token: str
    refresh_token: str
    user: UserSchema


class RefreshTokenRequest(Schema):
    refresh_token: str


class TokenPairResponse(Schema):
    access_token: str
    refresh_token: str


class LogoutRequest(Schema):
    refresh_token: str | None = None


class PasswordChangeRequest(Schema):
    old_password: str
    new_password: str = Field(..., min_length=8)


class PasswordForgetRequest(Schema):
    email: str

# class PasswordForgetResponse(Schema):
#     reset_session_token: str
    
class OtpSessionResponse(ModelSchema):
    class Meta:
        model = UserOTP
        exclude = [
            "user",
            "otp_hash",
            "attempts",
            "otp_verified",
            "active",
            "created_at",
            "updated_at",
        ]


class PasswordNewRequest(Schema):
    reset_session_token: str
    new_password: str
    confirm_password: str

class PasswordVerifyOtpRequest(Schema):
    reset_session_token: str
    otp: str


class EmailChangeRequest(Schema):
    new_email: str
