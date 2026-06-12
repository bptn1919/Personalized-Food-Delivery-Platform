import random
from django.contrib.auth.models import Group
from users.models import UserOTP
from users.schemas import PasswordNewRequest
from exceptions.auth import InvalidOrExpiredToken
from exceptions.users import UsernameOrPasswordIncorrect, AccountDeactivated
from utils.types import TUser, User

from .tokens import (
    get_refresh_payload,
    issue_access_token,
    issue_token_pair,
    revoke_all_refresh_tokens,
    revoke_refresh_token,
    rotate_refresh_token,
)
import secrets

class Query:
    
    @staticmethod
    def create_user(email: str, password: str, firstname: str, lastname: str, phone_number: str | None = None):
        user = User.objects.create_user(
            username=email.split("@")[0],  
            email=email,
            password=password,
            first_name=firstname,
            last_name=lastname,
            phone_number=phone_number,
            is_active=False,  # tạo user nhưng inactive
        )
        
        # Tự động thêm user vào group CUSTOMER
        customer_group, _ = Group.objects.get_or_create(name='CUSTOMER')
        user.groups.add(customer_group)
        
        return user
    
    @staticmethod
    def get_user_by_email_and_password(email: str, password: str) -> TUser:
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            raise UsernameOrPasswordIncorrect

        # Check if password is correct
        if not user.check_password(password):
            raise UsernameOrPasswordIncorrect
        
        # Check if account is active
        if not user.is_active:
            raise AccountDeactivated
        
        return user
    
    @staticmethod
    def assign_user_to_group(user: TUser, group_name: str = 'CUSTOMER'):
        """Gán user vào group"""
        group, _ = Group.objects.get_or_create(name=group_name)
        user.groups.add(group)

    @staticmethod
    def generate_tokens(user_id: int) -> tuple[str, str]:
        return issue_token_pair(user_id=user_id)

    @staticmethod
    def logout(user_id: int, refresh_token: str | None = None) -> bool:
        if refresh_token:
            # Validate token exists in Redis, then delete it immediately.
            revoke_refresh_token(refresh_token)
            return True
        revoke_all_refresh_tokens(user_id=user_id)
        return True

    @staticmethod
    def validate_refresh_token(refresh_token: str) -> dict:
        """Validate a refresh token and return its Redis payload (user_id, jti)."""
        return get_refresh_payload(refresh_token)

    @staticmethod
    def refresh_tokens(refresh_token: str) -> tuple[str, str]:
        # rotate_refresh_token validates, issues new, deletes old — returns (new_raw, user_id)
        new_refresh, user_id = rotate_refresh_token(refresh_token)
        new_access = issue_access_token(user_id=user_id)
        return new_access, new_refresh

    @staticmethod
    def update_me(user: TUser, full_name: str) -> TUser:
        user.first_name = full_name
        user.save()
        return user

    @staticmethod
    def check_password(user: TUser, password: str) -> bool:
        return user.check_password(raw_password=password)

    @staticmethod
    def change_password(user: TUser, password: str) -> TUser:
        user.set_password(raw_password=password)
        user.save()
        return user

    @staticmethod
    def get_user_by_email(email: str, only_active: bool = True):
        qs = User.objects.filter(email=email)
        if only_active:
            qs = qs.filter(is_active=True)
        return qs.first()
    
    @staticmethod
    def upgrade_customer_to_chef(user: TUser) -> TUser:
        """Chuyển user từ CUSTOMER sang CHEF"""
        # Xóa khỏi group CUSTOMER
        customer_group = Group.objects.get(name='CUSTOMER')
        user.groups.remove(customer_group)
        
        # Thêm vào group CHEF
        chef_group, _ = Group.objects.get_or_create(name='CHEF')
        user.groups.add(chef_group)
        
        return user
    
    @staticmethod
    def inactive_otp_token(user: TUser):
        return UserOTP.objects.filter(user=user, active=True).update(active=False)

    @staticmethod
    def create_reset_password_token(user: TUser, raw_token: str):
        return UserOTP.objects.create(user=user, token=raw_token)

    @staticmethod
    def get_reset_password_token(token: str):
        try:
            return UserOTP.objects.get(token=token, active=True)
        except UserOTP.DoesNotExist:
            raise InvalidOrExpiredToken
        
    #OTP
    @staticmethod
    def create_otp(user: TUser, purpose: str, target_email: str | None = None) -> tuple["UserOTP", str]:
        """Returns (UserOTP record, plain_otp).
        plain_otp must be emailed to the user; it is NOT stored in the database.
        """
        from users.models import _otp_hasher
        import secrets as _secrets

        plain_otp = f"{random.randint(0, 9999):04d}"
        otp_hash = _otp_hasher.hash(plain_otp)
        reset_session_token = _secrets.token_urlsafe(32)

        record = UserOTP.objects.create(
            user=user,
            otp_hash=otp_hash,
            attempts=0,
            reset_session_token=reset_session_token,
            purpose=purpose,
            target_email=target_email,
            otp_verified=False,
            active=True,
        )
        return record, plain_otp
    # @staticmethod
    # def get_otp_record(reset_session_token: str):
    #     return UserOTP.objects.filter(
    #         reset_session_token=reset_session_token,
    #         active=True
    #     ).first()

    @staticmethod
    def get_otp_record(reset_session_token: str):
        return UserOTP.objects.filter(
            reset_session_token=reset_session_token,
            active=True
        ).first()
    
    @staticmethod
    def mark_otp_verified(record: UserOTP):
        record.active = False # OTP chỉ được dùng 1 lần, sau khi verify thì inactive luôn
        record.otp_verified = True
        record.save(update_fields=["otp_verified"])
        
    @staticmethod
    def get_reset_password_otp(user: TUser, otp: str):
        try:
            return UserOTP.objects.get(user=user, otp=otp, active=True)
        except UserOTP.DoesNotExist:
            raise InvalidOrExpiredToken

    
    @staticmethod
    def reset_password(record: UserOTP, payload: PasswordNewRequest):
        record.user.set_password(raw_password=payload.new_password)
        record.user.save()
        record.active = False
        record.save()
        return True
