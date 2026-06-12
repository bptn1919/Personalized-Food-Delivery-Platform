from django.db import models
from django.conf import settings

class Conversation(models.Model):
    # Dùng string 'users.User' hoặc settings.AUTH_USER_MODEL để móc nối an toàn
    customer = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        related_name='customer_conversations', 
        on_delete=models.CASCADE
    )
    chef = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        related_name='chef_conversations', 
        on_delete=models.CASCADE
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    # Thời gian cập nhật tin nhắn cuối, dùng để sắp xếp ngoài màn hình Danh sách chat
    updated_at = models.DateTimeField(auto_now=True) 

    class Meta:
        db_table = 'chat_conversation'
        # Đảm bảo 1 Khách và 1 Chef chỉ có duy nhất 1 phòng chat
        unique_together = ('customer', 'chef')
        ordering = ['-updated_at']

    def __str__(self):
        return f"Chat: {self.customer} & {self.chef}"

class Message(models.Model):
    conversation = models.ForeignKey(
        Conversation, 
        related_name='messages', 
        on_delete=models.CASCADE
    )
    # Ai là người gửi? (Khách hay Chef đều gom vào đây)
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        related_name='sent_messages', 
        on_delete=models.CASCADE
    )
    
    text = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'chat_message'
        # Sắp xếp tin nhắn cũ nhất lên trên (để hiển thị từ trên xuống dưới trong khung chat)
        ordering = ['created_at']

    def __str__(self):
        return f"Msg from {self.sender} at {self.created_at}"