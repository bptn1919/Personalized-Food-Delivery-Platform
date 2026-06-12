from http import HTTPStatus

from utils.router.exception import APIException


class InvalidEmailOrPassword(APIException):
    error_code = HTTPStatus.FORBIDDEN
    message_code = "INVALID_EMAIL_OR_PASSWORD"
    message = "Invalid email or password"


class PermissionDeniedError(APIException):
    error_code = HTTPStatus.FORBIDDEN
    message_code = "PERMISSION_DENIED"
    message = "You don't have permission to perform this action"
    
    def __init__(self, message: str = None):
        if message:
            self.message = message
        super().__init__()


class InvalidOldPassword(APIException):
    error_code = HTTPStatus.FORBIDDEN
    message_code = "INVALID_PASSWORD"
    message = "Password is mismatch"


class PasswordIsTooWeak(APIException):
    error_code = HTTPStatus.FORBIDDEN
    message_code = "PASSWORD_TOO_WEAK"
    message = "Password is too weak"
