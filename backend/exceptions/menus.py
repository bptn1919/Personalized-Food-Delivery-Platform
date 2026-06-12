from http import HTTPStatus

from utils.router.exception import APIException


class MenuDoesNotExist(APIException):
    error_code = HTTPStatus.NOT_FOUND
    message_code = "MENU_DOES_NOT_EXIST"
    message = "Menu does not exist"


class MenuIsNotDeleted(APIException):
    error_code = HTTPStatus.FORBIDDEN
    message_code = "MENU_IS_NOT_DELETED"
    message = "Menu is not deleted"
    
class PermissionDenied(APIException):
    error_code = HTTPStatus.FORBIDDEN
    message_code = "PERMISSION_DENIED"
    message = "You do not have permission to perform this action"

class MenuDishAlreadyExists(APIException):
    error_code = HTTPStatus.CONFLICT
    message_code = "MENU_DISH_ALREADY_EXISTS"
    message = "This dish is already in the menu"