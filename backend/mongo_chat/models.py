from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

class UserDevice(models.Model):
    # Liên kết với bảng User hiện tại của hệ thống
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='devices')
    
    # Lưu chuỗi Token định danh thiết bị do Firebase cấp
    fcm_token = models.CharField(max_length=255)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'user_device' # Đặt tên bảng tường minh trong SQL
        verbose_name = 'Thiết bị người dùng'
        verbose_name_plural = 'Các thiết bị người dùng'

    def __str__(self):
        # Sửa lại user.first_name hoặc user.username tùy vào cách setup của project
        return f"Device of User ID {self.user.id} - {self.fcm_token[:15]}..."