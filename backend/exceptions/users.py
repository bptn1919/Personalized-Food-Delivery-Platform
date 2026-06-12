from http import HTTPStatus

from utils.router.exception import APIException


class UserNotFound(APIException):
    error_code = HTTPStatus.NOT_FOUND
    message_code = "USER_NOT_FOUND"
    message = "User not found"


class UsernameOrPasswordIncorrect(APIException):
    error_code = HTTPStatus.NOT_ACCEPTABLE
    message_code = "USERNAME_OR_PASSWORD_INCORRECT"
    message = "Username or password incorrect"


class PasswordIncorrect(APIException):
    error_code = HTTPStatus.UNAUTHORIZED
    message_code = "PASSWORD_INCORRECT"
    message = "Password incorrect"

class EmailAlreadyInUse(APIException):
    error_code = HTTPStatus.CONFLICT
    message_code = "EMAIL_ALREADY_IN_USE"
    message = "Email already in use"

class BankNameRequired(APIException):
    error_code = HTTPStatus.BAD_REQUEST
    message_code = "BANK_NAME_REQUIRED"
    message = "Bank name is required"

class BankAccountNumberRequired(APIException):
    error_code = HTTPStatus.BAD_REQUEST
    message_code = "BANK_ACCOUNT_NUMBER_REQUIRED"
    message = "Bank account number is required"

class BankAccountNameRequired(APIException):
    error_code = HTTPStatus.BAD_REQUEST
    message_code = "BANK_ACCOUNT_NAME_REQUIRED"
    message = "Bank account name is required"

class AccountDeactivated(APIException):
    error_code = HTTPStatus.FORBIDDEN
    message_code = "ACCOUNT_DEACTIVATED"
    message = "Your account has been deactivated. Please contact admin for support."
