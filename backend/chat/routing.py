from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    # Đường dẫn sẽ trông như thế này: ws://127.0.0.1:8000/ws/chat/1/
    re_path(r'ws/chat/(?P<room_id>\w+)/$', consumers.ChatConsumer.as_asgi()),
]