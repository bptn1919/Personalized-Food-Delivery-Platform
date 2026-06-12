import json
from channels.generic.websocket import AsyncWebsocketConsumer

class TrackingConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        # Lấy chef_id từ URL WebSocket (VD: ws://domain/ws/tracking/chef/5/)
        self.chef_id = self.scope['url_route']['kwargs']['chef_id']
        self.group_name = f"tracking_chef_{self.chef_id}"

        # Cho phép Customer join vào group Redis của Chef này
        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name
        )
        await self.accept()

    async def disconnect(self, close_code):
        # Rời khỏi group khi Customer tắt app
        await self.channel_layer.group_discard(
            self.group_name,
            self.channel_name
        )

    # Hàm này hứng dữ liệu từ file service (chú ý tên hàm phải khớp với "type" ở bước 1)
    async def send_location_update(self, event):
        data = event['data']
        
        # Bắn dữ liệu (JSON) xuống app Flutter của Customer
        await self.send(text_data=json.dumps({
            "action": "location_update",
            "data": data
        }))