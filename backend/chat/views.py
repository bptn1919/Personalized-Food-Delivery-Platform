from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Q
from .models import Message, Conversation
from .serializers import MessageSerializer

# --- 1. LẤY DANH SÁCH CÁC CUỘC HỘI THOẠI (Cho màn hình List Chat) ---
class ConversationListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        
        # Tìm các phòng chat mà User tham gia (Dù là Khách hay Chef)
        # Sắp xếp theo updated_at để phòng có tin nhắn mới nhất hiện lên đầu
        conversations = Conversation.objects.filter(
            Q(customer=user) | Q(chef=user)
        ).order_by('-updated_at')
        
        result = []
        for conv in conversations:
            # Xác định ai là người đối diện (Partner)
            partner = conv.chef if conv.customer == user else conv.customer
            
            # Lấy tin nhắn cuối cùng để hiển thị bản xem trước (Preview)
            latest_msg = conv.messages.order_by('-created_at').first()
            
            result.append({
                "room_id": conv.id,
                "partner_id": partner.id,
                "partner_name": partner.fullname if hasattr(partner, 'fullname') and partner.fullname else partner.username,
                "latest_message": latest_msg.text if latest_msg else "Bắt đầu cuộc trò chuyện...",
                "updated_at": conv.updated_at.isoformat(),
            })
            
        return Response(result)

# --- 2. LẤY LỊCH SỬ TIN NHẮN TRONG 1 PHÒNG (Cho màn hình Detail Chat) ---
class ChatHistoryView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, room_id):
        try:
            conversation = Conversation.objects.get(id=room_id)
            
            # Bảo mật: Chỉ người trong cuộc mới được xem
            if request.user != conversation.customer and request.user != conversation.chef:
                return Response({"error": "Bạn không có quyền xem phòng chat này"}, status=403)

            # Lấy 50 tin nhắn mới nhất
            messages = Message.objects.filter(conversation=conversation).order_of_sub_at = Message.objects.filter(
                conversation=conversation
            ).order_by('-created_at')[:50]
            
            serializer = MessageSerializer(messages, many=True)
            return Response(serializer.data)
            
        except Conversation.DoesNotExist:
            return Response({"error": "Phòng chat không tồn tại"}, status=404)