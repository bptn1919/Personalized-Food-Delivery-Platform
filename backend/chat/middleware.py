import urllib.parse
from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from users.tokens import decode_access_token

User = get_user_model()

@database_sync_to_async
def get_user_from_token(token_string):
    try:
        payload = decode_access_token(token_string)
        user_id = payload.get('user_id') 
        
        if user_id:
            return User.objects.get(id=user_id)
        return AnonymousUser()
    except Exception as e:
        # 🚨 THIS LOG IS CRITICAL FOR DEBUGGING
        print(f"🚨 JWT Decode Error: {e}")
        return AnonymousUser()

class JWTAuthMiddleware:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        # 1. Extract query string from URL
        query_string = scope.get("query_string", b"").decode("utf-8")
        query_params = urllib.parse.parse_qs(query_string)
        
        # 2. Get the 'token' parameter
        token = query_params.get("token", [None])[0]
        
        # 3. Verify token and assign User to scope
        if token:
            scope["user"] = await get_user_from_token(token)
        else:
            scope["user"] = AnonymousUser()

        return await self.app(scope, receive, send)