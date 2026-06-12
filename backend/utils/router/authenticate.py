from http import HTTPStatus

from django.http import HttpRequest
from ninja.security import HttpBearer

from django.contrib.auth import get_user_model
from users.tokens import decode_access_token
from utils.router.exception import APIException


class InvalidOrExpiredToken(APIException):
    error_code = HTTPStatus.UNAUTHORIZED
    message_code = "INVALID_OR_EXPIRED_TOKEN"
    message = "Invalid or expired token"


class AuthBear(HttpBearer):
    @classmethod
    def authenticate(cls, request: HttpRequest, token: str):
        try:
            payload = decode_access_token(token)
        except Exception as exc:
            print(f"🚨 [TECH LEAD DEBUG] JWT Error Detail Payload: {type(exc).__name__} - {str(exc)}")
            raise InvalidOrExpiredToken from exc

        user_id = payload.get("user_id")
        if not user_id:
            raise InvalidOrExpiredToken

        User = get_user_model()
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist as exc:
            print(f"🚨 [TECH LEAD DEBUG] JWT Error Detail User: {type(exc).__name__} - {str(exc)}")
            raise InvalidOrExpiredToken from exc

        setattr(request, "user", user)
        setattr(request, "token", token)

        return request
