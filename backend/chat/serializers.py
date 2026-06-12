from rest_framework import serializers
from .models import Message

class MessageSerializer(serializers.ModelSerializer):
    # Đổi tên cột 'text' thành 'message' để khớp 100% với JSON của WebSocket
    message = serializers.CharField(source='text')

    class Meta:
        model = Message
        # Chỉ trả về những thông tin Frontend thực sự cần
        fields = ['id', 'sender_id', 'message', 'created_at']