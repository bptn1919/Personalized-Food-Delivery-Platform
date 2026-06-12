from functools import wraps
import inspect

from utils.types import AuthenticatedRequest
from utils.exceptions import PermissionDeniedError
from uuid import UUID
from utils.enums import UserTypeEnum


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _resolve_owner_field(obj, owner_field: str):
    """
    Traverse dotted owner_field path on a model instance.
    E.g. owner_field='dish.owner' → obj.dish.owner
    Single-field path (e.g. 'owner', 'chef', 'created_by') also works.
    """
    current = obj
    for part in owner_field.split('.'):
        current = getattr(current, part, None)
        if current is None:
            return None
    return current


def _query_object(model_class, uid, check_deleted: bool = True):
    """
    Query model by uid.
    When check_deleted=True AND the model has a 'deleted' field, adds deleted=False filter.
    Set check_deleted=False for restore endpoints where the object is already deleted.
    Raises model_class.DoesNotExist on miss.
    """
    field_names = {f.name for f in model_class._meta.get_fields()}
    filter_kwargs = {'uid': uid}
    if check_deleted and 'deleted' in field_names:
        filter_kwargs['deleted'] = False
    return model_class.objects.get(**filter_kwargs)


def _raise_not_found(model_class):
    """Raise the appropriate not-found exception for well-known models."""
    from exceptions.certificates import CertificateNotFoundException
    from exceptions.dishes import DishNotFoundException
    from exceptions.orders import OrderNotFoundException
    from exceptions.menus import MenuDoesNotExist

    name = model_class.__name__
    if name == 'Certificate':
        raise CertificateNotFoundException
    if name == 'Dish':
        raise DishNotFoundException
    if name == 'Order':
        raise OrderNotFoundException
    if name == 'Menu':
        raise MenuDoesNotExist
    raise PermissionDeniedError(f"{name} not found")


# ---------------------------------------------------------------------------
# Public decorators
# ---------------------------------------------------------------------------

def require_permission(permission_codename: str):
    """Kiểm tra user có Django permission không."""
    def decorator(func):
        @wraps(func)
        def wrapper(self, request: AuthenticatedRequest, *args, **kwargs):
            if not request.user.has_perm(permission_codename):
                raise PermissionDeniedError(f"You don't have permission: {permission_codename}")
            return func(self, request, *args, **kwargs)
        return wrapper
    return decorator


def require_group(group_name: UserTypeEnum):
    """Kiểm tra user thuộc group (role) chỉ định."""
    def decorator(func):
        @wraps(func)
        def wrapper(self, request: AuthenticatedRequest, *args, **kwargs):
            if not request.user.groups.filter(name=group_name).exists():
                raise PermissionDeniedError(f"You must be in {group_name} group")
            return func(self, request, *args, **kwargs)
        return wrapper
    return decorator


def require_user_group(group_name: str, action: str | None = None, user_arg: str = "user"):
    """Decorator cho service layer: kiểm tra tham số user có thuộc group hay không."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            user = kwargs.get(user_arg)
            if user is None and len(args) >= 2:
                user = args[1]
            if user is None or not user.groups.filter(name=group_name).exists():
                action_text = action or "perform this action"
                raise PermissionDeniedError(f"Only {group_name} can {action_text}")
            return func(*args, **kwargs)
        return wrapper
    return decorator


def chef_required(action: str):
    """Shortcut decorator cho service methods yêu cầu user thuộc group CHEF."""
    return require_user_group(UserTypeEnum.CHEF, action=action)


def require_object_permission(
    permission_codename: str,
    model_class,
    owner_field: str = 'owner',
    check_deleted: bool = True,
):
    """
    Kiểm tra permission + ownership. Chỉ owner hoặc ADMIN mới được phép.

    Parameters:
    - permission_codename: e.g. 'dish.change_dish'
    - model_class: e.g. Dish, DishIngredient, Menu
    - owner_field: field chứa owner, hỗ trợ dotted path (vd: 'dish.owner', 'created_by', 'chef')
    - check_deleted: False cho restore endpoints (object đã bị soft-delete)
    """
    def decorator(func):
        @wraps(func)
        def wrapper(self, request: AuthenticatedRequest, *args, **kwargs):
            if not request.user.has_perm(permission_codename):
                raise PermissionDeniedError(f"You don't have permission: {permission_codename}")

            uid = kwargs.get('uid')
            if not uid:
                raise ValueError("require_object_permission requires 'uid' parameter")

            try:
                obj = _query_object(model_class, uid, check_deleted=check_deleted)
            except model_class.DoesNotExist:
                _raise_not_found(model_class)

            owner = _resolve_owner_field(obj, owner_field)
            if owner is not None:
                owner_id = owner.id if hasattr(owner, 'id') else owner
                is_owner = owner_id == request.user.id
                is_admin = request.user.groups.filter(name=UserTypeEnum.ADMIN).exists()
                if not (is_owner or is_admin):
                    raise PermissionDeniedError(
                        f"You can only modify your own {model_class.__name__.lower()}s"
                    )

            request._permission_checked_object = obj
            return func(self, request, *args, **kwargs)
        return wrapper
    return decorator


def require_owner_or_admin(
    model_class,
    owner_field: str = 'owner',
    check_deleted: bool = True,
):
    """
    Kiểm tra ownership (không cần permission). Cho phép owner hoặc ADMIN.

    Parameters:
    - model_class: Model class
    - owner_field: hỗ trợ dotted path
    - check_deleted: False cho restore endpoints
    """
    def decorator(func):
        @wraps(func)
        def wrapper(self, request: AuthenticatedRequest, *args, **kwargs):
            uid = kwargs.get('uid')
            if not uid:
                raise ValueError("require_owner_or_admin requires 'uid' parameter")

            try:
                obj = _query_object(model_class, uid, check_deleted=check_deleted)
            except model_class.DoesNotExist:
                _raise_not_found(model_class)

            owner = _resolve_owner_field(obj, owner_field)
            if owner is not None:
                owner_id = owner.id if hasattr(owner, 'id') else owner
                is_owner = owner_id == request.user.id
                is_admin = request.user.groups.filter(name=UserTypeEnum.ADMIN).exists()
                if not (is_owner or is_admin):
                    raise PermissionDeniedError(
                        f"Bạn không có quyền truy cập {model_class.__name__.lower()} này."
                    )

            request._permission_checked_object = obj
            return func(self, request, *args, **kwargs)
        return wrapper
    return decorator


def require_owner(
    model_class,
    owner_field: str = 'owner',
    check_deleted: bool = True,
):
    """
    Kiểm tra ownership. CHỈ OWNER — admin không được phép.

    Parameters:
    - model_class: Model class
    - owner_field: hỗ trợ dotted path
    - check_deleted: False cho restore endpoints
    """
    def decorator(func):
        @wraps(func)
        def wrapper(self, request: AuthenticatedRequest, *args, **kwargs):
            uid = kwargs.get('uid')
            if not uid:
                raise ValueError("require_owner requires 'uid' parameter")

            try:
                obj = _query_object(model_class, uid, check_deleted=check_deleted)
            except model_class.DoesNotExist:
                _raise_not_found(model_class)

            owner = _resolve_owner_field(obj, owner_field)
            if owner is not None:
                owner_id = owner.id if hasattr(owner, 'id') else owner
                if owner_id != request.user.id:
                    raise PermissionDeniedError(
                        "Chỉ chủ sở hữu mới có quyền thực hiện hành động này."
                    )

            request._permission_checked_object = obj
            return func(self, request, *args, **kwargs)
        return wrapper
    return decorator


def sync_user_feature(user_arg="user", update_fields=None):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            result = func(*args, **kwargs)

            if result is None or result is False:
                return result

            try:
                bound = inspect.signature(func).bind_partial(*args, **kwargs)
                bound.apply_defaults()
                user = bound.arguments.get(user_arg)
            except Exception:
                user = None

            if user is None and len(args) >= 2:
                user = args[1]

            if user is not None and hasattr(user, "id"):
                from recommendation.services.recommendation import RecommendationService

                RecommendationService().rebuild_user_feature(
                    user.id,
                    update_fields=update_fields
                )

            return result
        return wrapper
    return decorator
