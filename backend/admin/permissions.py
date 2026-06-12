from functools import wraps
from utils.exceptions import PermissionDeniedError
from utils.types import AuthenticatedRequest
from utils.enums import UserTypeEnum


def require_admin(func):
    """
    Decorator kiểm tra user có thuộc group ADMIN không
    Sử dụng: @require_admin trước function
    """
    @wraps(func)
    def wrapper(self, request: AuthenticatedRequest, *args, **kwargs):
        if not request.user.groups.filter(name=UserTypeEnum.ADMIN).exists():
            raise PermissionDeniedError("Only admin can access this endpoint")
        return func(self, request, *args, **kwargs)
    return wrapper


def require_admin_or_chef(func):
    """
    Decorator kiểm tra user có thuộc group ADMIN hoặc CHEF không
    Sử dụng: @require_admin_or_chef trước function
    """
    @wraps(func)
    def wrapper(self, request: AuthenticatedRequest, *args, **kwargs):
        is_admin = request.user.groups.filter(name=UserTypeEnum.ADMIN).exists()
        is_chef = request.user.groups.filter(name=UserTypeEnum.CHEF).exists()
        if not (is_admin or is_chef):
            raise PermissionDeniedError("Only admin or chef can access this endpoint")
        return func(self, request, *args, **kwargs)
    return wrapper
