import os
import django

# Thay 'marketplace.settings' bằng đường dẫn đúng tới file settings của bạn
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'marketplace.settings')

# Setup Django trước khi import anything khác
django.setup()

from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter

# Khởi tạo ứng dụng Django ASGI
django_asgi_app = get_asgi_application()

application = ProtocolTypeRouter({
    # Các request HTTP bình thường (API cũ) sẽ đi đường này
    "http": django_asgi_app,
    
    # Các request WebSocket (Chat) sẽ đi đường này (Chúng ta sẽ add router chi tiết ở bài sau)
    "websocket": URLRouter(
        # Tạm thời để trống, bài sau ta sẽ điền file routing.py vào đây
        []
    ),
})