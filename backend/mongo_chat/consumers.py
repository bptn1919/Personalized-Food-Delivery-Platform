import json
from datetime import datetime, timezone
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model
from bson.objectid import ObjectId
from bson.errors import InvalidId  # THÊM ĐỂ BẮT LỖI ID
from .database import messages_collection, conversations_collection
from users.tokens import decode_access_token

# 👇 1. IMPORT HÀM GỬI THÔNG BÁO TỪ BƯỚC TRƯỚC 👇
from .notifications import send_chat_notification

User = get_user_model()

class MongoChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_id = self.scope['url_route']['kwargs']['room_id']
        self.room_group_name = f'mongo_chat_{self.room_id}'

        # TECH LEAD FIX 1: Chặn ngay từ lúc Connect nếu Flutter gửi room_id sai định dạng
        try:
            ObjectId(self.room_id)
        except InvalidId:
            print(f"🚨 Connection rejected: Invalid room_id format ({self.room_id}).")
            await self.close(code=4000)
            return

        # Extract token from query string
        query_string = self.scope['query_string'].decode()
        token = None
        if 'token=' in query_string:
            token = query_string.split('token=')[1].split('&')[0]

        # Authenticate user
        self.user_info = await self.get_user_info(token)
        
        # If authentication fails, reject the connection
        if not self.user_info:
            print("🚨 Connection rejected: Invalid or missing token.")
            await self.close(code=4001) 
            return

        # Accept connection
        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()
        print(f"✅ User '{self.user_info['name']}' connected to {self.room_group_name}")

    async def disconnect(self, close_code):
        if hasattr(self, 'room_group_name'):
            await self.channel_layer.group_discard(self.room_group_name, self.channel_name)
            print(f"❌ User disconnected from {self.room_group_name}")

    async def receive(self, text_data):
        data = json.loads(text_data)
        
        message_type = data.get('type', 'text') 
        content = data.get('content', '')
        file_url = data.get('file_url', None)

        # Prepare message payload
        # LƯU Ý: Giữ nguyên room_id dạng String ở đây để tý nữa broadcast qua WebSocket không bị lỗi JSON
        new_message = {
            "room_id": self.room_id,
            "type": message_type,
            "content": content,
            "file_url": file_url,
            "sender": self.user_info, 
            "created_at": datetime.now(timezone.utc)
        }
        
        # Save to DB and get the generated ID
        msg_id = await self.save_to_mongo(new_message)
        new_message['_id'] = msg_id 
        new_message['created_at'] = new_message['created_at'].isoformat() 

        # Broadcast to the room
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat_message',
                'message': new_message
            }
        )

    async def chat_message(self, event):
        message = event['message']
        await self.send(text_data=json.dumps(message))

    @database_sync_to_async
    def get_user_info(self, token):
        if not token: 
            print("🚨 Auth Error: No token provided in WebSocket URL.")
            return None
            
        try:
            payload = decode_access_token(token)
            user = User.objects.get(id=payload['user_id'])
            return {
                "id": user.id,
                "name": getattr(user, 'username', f"User {user.id}"), 
            }
        except Exception as e:
            print(f"🚨 JWT Verification Failed: {str(e)}")
            return None

    @database_sync_to_async
    def save_to_mongo(self, message_data):
        # TECH LEAD FIX 2: Copy payload sang biến mới để ép kiểu ObjectId riêng cho DB, 
        # tránh làm ô nhiễm dictionary "message_data" đang dùng cho WebSocket.
        db_message = message_data.copy()
        db_message['room_id'] = ObjectId(self.room_id)
        
        # 1. Save message to 'messages' collection bằng db_message
        result = messages_collection.insert_one(db_message)
        
        # 2. Update 'last_message' preview in 'conversations' collection
        latest_content = message_data['content'] if message_data['type'] == 'text' else f"Sent a {message_data['type']}"
        
        conversations_collection.update_one(
            {"_id": ObjectId(self.room_id)},
            {
                "$set": {
                    "last_message": {
                        "content": latest_content,
                        "created_at": message_data['created_at']
                    },
                    "updated_at": message_data['created_at']
                }
            },
            upsert=True # Create the room if it doesn't exist
        )

        # 👇 3. GỌI HÀM BẮN THÔNG BÁO TỚI NGƯỜI NHẬN 👇
        try:
            send_chat_notification(
                room_id=self.room_id, # Truyền ID dạng String vào hàm xử lý thông báo
                sender_id=message_data['sender']['id'],
                message_content=latest_content
            )
        except Exception as e:
            print(f"🚨 Consumer failed to trigger notification: {e}")

        return str(result.inserted_id)