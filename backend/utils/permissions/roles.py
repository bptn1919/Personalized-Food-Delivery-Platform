from utils.enums import UserTypeEnum
from utils.types import TUser


def get_user_role(user: TUser) -> UserTypeEnum:
    if user.groups.filter(name=UserTypeEnum.CHEF).exists():
        return UserTypeEnum.CHEF
    if user.groups.filter(name=UserTypeEnum.CUSTOMER).exists():
        return UserTypeEnum.CUSTOMER
    return UserTypeEnum.ADMIN