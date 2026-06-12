import jwt
from django.contrib.auth import get_user_model
from rest_framework import authentication, exceptions
from users.tokens import decode_access_token

class PureJWTAuthentication(authentication.BaseAuthentication):
    def authenticate(self, request):
        # 1. ĐƯA LÊN ĐÂY: Khởi tạo User model ngay từ đầu để dùng cho cả khối try và except
        User = get_user_model() 

        auth_header = request.headers.get('Authorization')
        if not auth_header:
            return None

        try:
            token = auth_header.split(' ')[1]
            payload = decode_access_token(token)
            
            user_id = payload.get('user_id')
            if not user_id:
                raise exceptions.AuthenticationFailed('Token không chứa user_id')

            user = User.objects.get(id=user_id)
            return (user, None)

        except jwt.ExpiredSignatureError:
            raise exceptions.AuthenticationFailed('Token đã hết hạn')
        except (jwt.InvalidTokenError, IndexError, User.DoesNotExist):
            raise exceptions.AuthenticationFailed('Xác thực thất bại')

    def authenticate_header(self, request):
        return 'Bearer'