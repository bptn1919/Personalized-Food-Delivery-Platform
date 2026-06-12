from django.urls import re_path

from tracking.consumers import TrackingConsumer
from . import consumers

websocket_urlpatterns = [
    # Đường dẫn sẽ là: ws://127.0.0.1:8000/ws/mongo-chat/<room_id>/
    re_path(r'ws/mongo-chat/(?P<room_id>\w+)/$', consumers.MongoChatConsumer.as_asgi()),
    re_path('ws/tracking/chef/<int:chef_id>/', TrackingConsumer.as_asgi()),
]