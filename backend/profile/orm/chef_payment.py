from profile.models import ChefPaymentInfo
from utils.types import User


class ChefPaymentInfoORM:
    """ORM layer for ChefPaymentInfo operations"""
    
    @staticmethod
    def get_by_user(user: User) -> ChefPaymentInfo | None:
        """Get chef payment info by user"""
        try:
            return ChefPaymentInfo.objects.get(user=user)
        except ChefPaymentInfo.DoesNotExist:
            return None
    
    @staticmethod
    def exists_for_user(user: User) -> bool:
        """Check if payment info exists for user"""
        return ChefPaymentInfo.objects.filter(user=user).exists()
    
    @staticmethod
    def create(
        user: User,
        bank_name: str,
        bank_code: str,
        bank_account_number: str,
        bank_account_name: str,
        bank_branch: str | None = None,
        citizen_id: str | None = None,
        tax_code: str | None = None,
        is_verified: bool = False
    ) -> ChefPaymentInfo:
        """Create new chef payment info"""
        return ChefPaymentInfo.objects.create(
            user=user,
            bank_name=bank_name,
            bank_code=bank_code,
            bank_account_number=bank_account_number,
            bank_account_name=bank_account_name,
            bank_branch=bank_branch,
            citizen_id=citizen_id,
            tax_code=tax_code,
            is_verified=is_verified
        )
    
    @staticmethod
    def update(
        payment_info: ChefPaymentInfo,
        bank_name: str | None = None,
        bank_code: str | None = None,
        bank_account_number: str | None = None,
        bank_account_name: str | None = None,
        bank_branch: str | None = None,
        citizen_id: str | None = None,
        tax_code: str | None = None,
        is_verified: bool | None = None
    ) -> ChefPaymentInfo:
        """Update chef payment info"""
        if bank_name is not None:
            payment_info.bank_name = bank_name
        if bank_code is not None:
            payment_info.bank_code = bank_code
        if bank_account_number is not None:
            payment_info.bank_account_number = bank_account_number
        if bank_account_name is not None:
            payment_info.bank_account_name = bank_account_name
        if bank_branch is not None:
            payment_info.bank_branch = bank_branch
        if citizen_id is not None:
            payment_info.citizen_id = citizen_id
        if tax_code is not None:
            payment_info.tax_code = tax_code
        if is_verified is not None:
            payment_info.is_verified = is_verified
        
        payment_info.save()
        return payment_info
    
    @staticmethod
    def delete(payment_info: ChefPaymentInfo) -> None:
        """Delete chef payment info"""
        payment_info.delete()
