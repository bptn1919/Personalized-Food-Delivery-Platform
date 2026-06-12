from http import HTTPStatus

from utils.router.exception import APIException


class InvalidOrExpiredToken(APIException):
    error_code = HTTPStatus.UNAUTHORIZED
    message_code = "INVALID_OR_EXPIRED_TOKEN"
    message = "Invalid or expired token"

class InvalidOtp(APIException):
    error_code = HTTPStatus.FORBIDDEN
    message_code = "INVALID_OTP"
    message = "Invalid OTP" 
    
class ConfirmPasswordNotMatch(APIException):
    error_code = HTTPStatus.BAD_REQUEST
    message_code = "CONFIRM_PASSWORD_NOT_MATCH"
    message = "Confirm password does not match"
