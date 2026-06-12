import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model
from .models import Conversation, Message

User = get_user_model()

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        user = self.scope['user']
        if user.is_anonymous:
            print("🚨 Đuổi một kẻ không có Token (hoặc Token hết hạn) ra khỏi cửa!")
            await self.close()
            return
        # 1. Lấy ID phòng chat từ URL (VD: ws://domain/ws/chat/1/)
        self.room_id = self.scope['url_route']['kwargs']['room_id']
        self.room_group_name = f'chat_{self.room_id}'

        # 2. Đăng ký user này vào "Group" (Phòng) trên Redis
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        # Chấp nhận kết nối
        await self.accept()
        print(f"✅ User connected to room: {self.room_group_name}")

    async def disconnect(self, close_code):
        # Rời khỏi "Group" khi tắt app/rớt mạng
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )
        print(f"❌ User disconnected from room: {self.room_group_name}")

    # Bắt tin nhắn từ Flutter gửi LÊN server
    async def receive(self, text_data):
        try:
            data = json.loads(text_data)
            message_text = data['message']
            
            # 👇 LẤY ID TỪ SCOPE, BỎ LUÔN CÁI SENDER_ID TỪ CLIENT GỬI LÊN 👇
            sender = self.scope['user'] 

            # Lưu vào Database
            await self.save_message(sender.id, self.room_id, message_text)

            # Bắn tin đi
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'chat_message', 
                    'message': message_text,
                    'sender_id': sender.id # Trả ngược ID thật về cho Front-end biết
                }
            )
        except json.JSONDecodeError:
            print(f"🚨 CẢNH BÁO: Client gửi sai format JSON.")

    # Bắt tin nhắn từ Redis đẩy XUỐNG Flutter
    async def chat_message(self, event):
        message_text = event['message']
        sender_id = event['sender_id']

        # Gửi cục JSON về lại cho điện thoại của Khách/Chef
        await self.send(text_data=json.dumps({
            'message': message_text,
            'sender_id': sender_id
        }))

    # Hàm phụ trợ: Lưu Database an toàn trong môi trường Async
    @database_sync_to_async
    def save_message(self, sender_id, room_id, text):
        try:
            conversation = Conversation.objects.get(id=room_id)
            sender = User.objects.get(id=sender_id)
            Message.objects.create(
                conversation=conversation,
                sender=sender,
                text=text
            )
        except Exception as e:
            print(f"🚨 Lỗi lưu Database: {e}")