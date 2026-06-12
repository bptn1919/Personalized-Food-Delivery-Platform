from ninja import Schema
from utils.router.controller import Controller, api, get

from utils.router.authenticate import AuthBear
from .notifications import get_unread_count

class UnreadCountResponse(Schema):
    unread_count: int

@api(prefix_or_class="notifications", tags=["Notification"], auth=AuthBear())
class NotificationController(Controller):
    
    @get("/unread-count", response=UnreadCountResponse)
    def unread_count_api(self, request):
        """
        Lấy tổng số thông báo chưa đọc của user đang đăng nhập
        """
        user_id = request.user.id 
        
        # Gọi thẳng hàm đã viết
        count = get_unread_count(user_id)
        
        return {"unread_count": count}