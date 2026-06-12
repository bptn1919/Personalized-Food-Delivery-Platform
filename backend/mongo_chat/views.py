from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .database import conversations_collection, messages_collection, notifications_collection
from django.contrib.auth import get_user_model
from .models import UserDevice
import pymongo
from datetime import datetime, timezone as py_timezone
from rest_framework.decorators import api_view, permission_classes
from bson.objectid import ObjectId
from bson.errors import InvalidId  # BẮT BUỘC THÊM CÁI NÀY ĐỂ BẮT LỖI ID SAI FORMAT

User = get_user_model()

# --- 1. LẤY DANH SÁCH PHÒNG CHAT ---
class MongoConversationListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user_id = request.user.id

        # 1. Lấy danh sách phòng từ MongoDB
        cursor = conversations_collection.find(
            {"participants.user_id": user_id}
        ).sort("updated_at", pymongo.DESCENDING)

        conversations = []
        partner_ids = set()

        # 2. Vòng lặp 1: Xử lý ObjectId và gom ID của đối phương
        for conv in cursor:
            conv['_id'] = str(conv['_id']) # Trả về String để Flutter đọc được JSON
            
            partner_id = None
            for participant in conv.get('participants', []):
                if participant.get('user_id') != user_id:
                    partner_id = participant.get('user_id')
                    break
            
            conv['partner_id'] = partner_id
            if partner_id:
                partner_ids.add(partner_id)
                
            conversations.append(conv)

        # 3. Chọc vào SQL lấy tên
        users = User.objects.filter(id__in=partner_ids)
        user_map = {u.id: u.username for u in users} 

        # 4. Đắp tên vào từng phòng chat
        for conv in conversations:
            p_id = conv.get('partner_id')
            conv['partner_name'] = user_map.get(p_id, "Người dùng ẩn danh")

        return Response(conversations)
    

# --- 2. LẤY LỊCH SỬ TIN NHẮN ---
class MongoMessageHistoryView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, room_id):
        # TECH LEAD FIX: Bắt lỗi nếu room_id gửi lên không phải là ObjectId hợp lệ
        try:
            obj_room_id = ObjectId(room_id)
        except InvalidId:
            return Response({"error": "room_id không hợp lệ (Không phải ObjectId)!"}, status=400)

        # TECH LEAD FIX: Đổi "_id" thành "room_id". Tin nhắn thuộc về phòng, chứ không phải ID tin nhắn bằng ID phòng!
        cursor = messages_collection.find(
            {"room_id": obj_room_id} 
        ).sort("created_at", pymongo.DESCENDING).limit(50)

        messages = []
        for msg in cursor:
            msg['_id'] = str(msg['_id'])
            # Cũng nên convert lại room_id sang string để trả về cho Client dễ xài
            if 'room_id' in msg and isinstance(msg['room_id'], ObjectId):
                msg['room_id'] = str(msg['room_id'])
            messages.append(msg)

        return Response(messages)


# --- CÁC API THIẾT BỊ VÀ THÔNG BÁO ---
# class RegisterDeviceView(APIView):
#     permission_classes = [IsAuthenticated]

#     def post(self, request):
#         fcm_token = request.data.get('fcm_token')
#         if not fcm_token:
#             return Response({"error": "Thiếu fcm_token"}, status=400)

#         UserDevice.objects.update_or_create(
#             user=request.user, 
#             fcm_token=fcm_token,
#             defaults={'fcm_token': fcm_token}
#         )
#         return Response({"message": "Đã lưu thiết bị thành công!"})

class RegisterDeviceView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        print("====== [FCM DEBUG] BẮT ĐẦU GỌI API ======")
        
        # 1. Kiểm tra User đã lọt qua được lớp IsAuthenticated chưa
        print(f"👤 User đang gọi: {request.user} (ID: {request.user.id})")
        
        # 2. Kiểm tra xem Frontend gửi lên cái gì
        print(f"📦 Dữ liệu thô (request.data): {request.data}")

        fcm_token = request.data.get('fcm_token')
        
        # 3. Kiểm tra biến token sau khi lấy ra
        print(f"🔑 FCM Token nhận được: '{fcm_token}'")

        if not fcm_token:
            print("❌ LỖI: Token bị rỗng hoặc Frontend gửi sai key!")
            return Response({"error": "Thiếu fcm_token"}, status=400)

        try:
            # 4. Lưu vào Database (Đã FIX bug update_or_create)
            print("⏳ Đang lưu vào Database...")
            device, created = UserDevice.objects.update_or_create(
                user=request.user, # CHỈ tìm bằng user thôi
                defaults={'fcm_token': fcm_token} # Lưu/Cập nhật cái này
            )
            
            # 5. Kiểm tra kết quả DB
            if created:
                print(f"✅ Đã TẠO MỚI bản ghi cho user {request.user.username}")
            else:
                print(f"🔄 Đã CẬP NHẬT token cho user {request.user.username}")
                
            return Response({"message": "Đã lưu thiết bị thành công!"})
            
        except Exception as e:
            # 6. Bắt trọn ổ các lỗi ngầm (Database Crash)
            print(f"💥 DATABASE CRASH: {str(e)}")
            return Response({"error": "Lỗi hệ thống khi lưu DB"}, status=500)
    
class UnregisterDeviceView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        fcm_token = request.data.get('fcm_token')
        if not fcm_token:
            return Response({"error": "Thiếu fcm_token"}, status=400)

        deleted_count, _ = UserDevice.objects.filter(
            user=request.user, 
            fcm_token=fcm_token
        ).delete()

        return Response({
            "message": "Đã gỡ liên kết thiết bị thành công!",
            "deleted_count": deleted_count
        }, status=200)
        
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def fetch_notifications(request):
    cursor = notifications_collection.find({"user_id": request.user.id}).sort("created_at", -1)
    notis = []
    for n in cursor:
        n['_id'] = str(n['_id'])
        if 'created_at' in n:
            n['created_at'] = n['created_at'].replace(tzinfo=py_timezone.utc).isoformat()
        notis.append(n)
    return Response(notis, status=200)

@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def mark_notification_read(request, noti_id):
    if noti_id == "all":
        notifications_collection.update_many(
            {"user_id": request.user.id, "is_read": False},
            {"$set": {"is_read": True}}
        )
    else:
        # TECH LEAD FIX: Bọc try-except để chống crash 500
        try:
            obj_noti_id = ObjectId(noti_id)
        except InvalidId:
            return Response({"error": "noti_id không hợp lệ!"}, status=400)

        notifications_collection.update_one(
            {"_id": obj_noti_id, "user_id": request.user.id},
            {"$set": {"is_read": True}}
        )
    return Response({"message": "Success"}, status=200)

@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_notification(request, noti_id):
    try:
        obj_noti_id = ObjectId(noti_id)
    except InvalidId:
        return Response({"error": "noti_id không hợp lệ!"}, status=400)

    notifications_collection.delete_one({"_id": obj_noti_id, "user_id": request.user.id})
    return Response({"message": "Deleted"}, status=200)


# --- 3. TẠO HOẶC LẤY PHÒNG CHAT (GET-OR-CREATE) ---
class MongoGetOrCreateRoomView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user_id = request.user.id
        partner_id = request.data.get('partner_id')

        if not partner_id:
            return Response({"error": "Thiếu partner_id"}, status=400)

        try:
            partner_id = int(partner_id)
        except ValueError:
            return Response({"error": "partner_id must be integer (ID)"}, status=400)

        if user_id == partner_id:
            return Response({"error": "You cannot chat with yourself"}, status=400)

        existing_room = conversations_collection.find_one({
            "participants.user_id": {"$all": [user_id, partner_id]},
            "participants": {"$size": 2}
        })

        if existing_room:
            return Response({
                "room_id": str(existing_room["_id"]),
                "is_new": False
            }, status=200)

        new_room = {
            "participants": [
                {"user_id": user_id},
                {"user_id": partner_id}
            ],
            "last_message": None,
            "created_at": datetime.now(py_timezone.utc),
            "updated_at": datetime.now(py_timezone.utc)
        }

        result = conversations_collection.insert_one(new_room)

        return Response({
            "room_id": str(result.inserted_id),
            "is_new": True
        }, status=201)