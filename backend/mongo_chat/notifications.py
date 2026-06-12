from firebase_admin import messaging
from django.contrib.auth import get_user_model
from datetime import datetime
from bson.objectid import ObjectId
from bson.errors import InvalidId
from django.utils import timezone

# Cập nhật đường dẫn import của bạn cho đúng
from .database import conversations_collection, notifications_collection
from .models import UserDevice

User = get_user_model()

def send_chat_notification(room_id, sender_id, message_content):
    try:
        # 👇 TECH LEAD FIX 1: Truy vấn SQL lấy tên người gửi ngay lập tức
        sender_name = "Tin nhắn mới"
        try:
            sender = User.objects.get(id=sender_id)
            sender_name = sender.username 
        except User.DoesNotExist:
            pass

        # 1. MONGODB: Lấy thông tin phòng chat
        try:
            room_object_id = ObjectId(room_id)
        except InvalidId:
            return

        room = conversations_collection.find_one({"_id": room_object_id}) 
        if not room or "participants" not in room:
            return

        participants = room.get("participants", [])
        
        # 2. Lọc ra những người nhận
        list_receiver_ids = []
        for p in participants:
            uid = p.get('user_id') if isinstance(p, dict) else p
            if uid is not None and str(uid) != str(sender_id):
                list_receiver_ids.append(int(uid))
        
        if not list_receiver_ids:
            return
        
        # 👇 TECH LEAD FIX 2: Nhét sender_name vào Record của MongoDB
        noti_docs = []
        for uid in list_receiver_ids:
            noti_docs.append({
                "user_id": int(uid),
                "title": "New Message",
                "body": message_content,
                "type": "chat",
                "room_id": str(room_id),
                "sender_name": sender_name, # 🌟 LƯU CHẾT TÊN VÀO ĐÂY
                "is_read": False,
                "created_at": timezone.now()
            })
        if noti_docs:
            notifications_collection.insert_many(noti_docs)

        # 3. SQL (DJANGO ORM): Lấy FCM Tokens
        devices = UserDevice.objects.filter(user__id__in=list_receiver_ids)
        tokens = [device.fcm_token for device in devices if device.fcm_token]
        
        if not tokens:
            return

        # 👇 TECH LEAD FIX 3: Push Notification hiện luôn tên người gửi
        message = messaging.MulticastMessage(
            notification=messaging.Notification(
                title=sender_name, # 🌟 Rung chuông hiện tên người gửi
                body=message_content,
            ),
            data={
                "room_id": str(room_id),
                "type": "chat",
                "sender_name": sender_name,
            },
            tokens=tokens, 
        )
        print(f"✅ Chat Notification Prepared for Room {room_id} with {len(tokens)} tokens.")

        messaging.send_each_for_multicast(message)

    except Exception as e:
        print(f"🚨 Failed to send push notification: {e}")
        
def send_order_notification(customer_id, order_id, title, body, chef_name=None):
    """
    Trigger FCM notification to the customer for order updates (Confirmed, Delivering, etc.)
    """
    try:
        # ==========================================
        # 1. LƯU VÀO MONGODB (Chuông thông báo)
        # ==========================================
        noti_doc = {
            "user_id": int(customer_id),
            "title": title,
            "body": body,
            "type": "order",           # 👈 Điểm mấu chốt để Flutter hiện Icon Xe tải màu Xanh
            "order_id": str(order_id), # Lưu thêm order_id để sau này Frontend bấm vào thì nhảy sang trang Chi tiết đơn
            "sender_name": chef_name,  # 👈 Tái sử dụng trường này để hiện tên Đầu bếp (Denormalization)
            "is_read": False,
            "created_at": timezone.now()
        }
        notifications_collection.insert_one(noti_doc)

        # ==========================================
        # 2. SQL (DJANGO ORM): Lấy FCM Tokens của Customer
        # ==========================================
        # Một user có thể đăng nhập trên nhiều máy (điện thoại, tablet), nên dùng filter để lấy hết
        devices = UserDevice.objects.filter(user_id=customer_id)
        tokens = [device.fcm_token for device in devices if device.fcm_token]
        
        if not tokens:
            print(f"🚨 Notice: No FCM tokens found in SQL for customer {customer_id}.")
            return

        # ==========================================
        # 3. BẮN PUSH NOTIFICATION QUA FIREBASE
        # ==========================================
        message = messaging.MulticastMessage(
            notification=messaging.Notification(
                title=title, 
                body=body,
            ),
            data={
                "order_id": str(order_id),
                "type": "order", # Truyền type ngầm để Flutter biết luồng xử lý khi app đang tắt
            },
            tokens=tokens, 
        )

        response = messaging.send_each_for_multicast(message)
        print(f"✅ Order Notification Sent! Success: {response.success_count}, Failed: {response.failure_count}")

    except Exception as e:
        print(f"🚨 Failed to send order notification: {e}")
        
def get_unread_count(user_id: int) -> int:
        """
        Đếm số lượng thông báo chưa đọc của một User cụ thể trong MongoDB.
        """
        try:
            # Query tìm các document thuộc về user này và có is_read = False
            query = {
                "user_id": int(user_id),
                "is_read": False
            }
            
            # 👇 TECH LEAD TRICK: Dùng count_documents thay vì len(list(find())) để tối ưu RAM
            count = notifications_collection.count_documents(query)
            return count
            
        except Exception as e:
            print(f"🚨 Failed to count unread notifications for user {user_id}: {e}")
            return 0