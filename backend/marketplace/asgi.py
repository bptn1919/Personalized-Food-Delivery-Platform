import os
import django
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter

# Import cả 2 file routing
import chat.routing
import mongo_chat.routing

# Import Middleware gác cổng của bạn
from chat.middleware import JWTAuthMiddleware

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'marketplace.settings')

# ⚠️ QUAN TRỌNG: Gọi django.setup() trước khi import models
django.setup()

django_asgi_app = get_asgi_application()

application = ProtocolTypeRouter({
    "http": django_asgi_app,
    "websocket": JWTAuthMiddleware(
        URLRouter(
            chat.routing.websocket_urlpatterns +
            mongo_chat.routing.websocket_urlpatterns
        )
    ),
})