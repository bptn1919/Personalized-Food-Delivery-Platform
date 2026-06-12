from urllib.parse import parse_qs
from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from users.tokens import decode_access_token

User = get_user_model()

@database_sync_to_async
def get_user_from_jwt(token_key):
    try:
        payload = decode_access_token(token_key)
        user_id = payload.get("user_id")
        return User.objects.get(id=user_id)
    except Exception as e:
        print(f"🚨 WebSocket Auth Error: {str(e)}")
        return AnonymousUser()

class WebSocketJwtAuthMiddleware:
    """
    Custom Middleware to authenticate WebSockets using JWT in query string.
    """
    def __init__(self, inner):
        self.inner = inner

    async def __call__(self, scope, receive, send):
        # Extract query string parameters
        query_string = scope.get("query_string", b"").decode("utf-8")
        query_params = parse_qs(query_string)
        
        # Get the token from 'ws://.../?token=...'
        token = query_params.get("token", [None])[0]

        if token:
            scope["user"] = await get_user_from_jwt(token)
        else:
            scope["user"] = AnonymousUser()

        return await self.inner(scope, receive, send)