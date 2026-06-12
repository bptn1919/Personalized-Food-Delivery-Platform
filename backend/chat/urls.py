from django.urls import path
from .views import ChatHistoryView, ConversationListView

urlpatterns = [
    # Đường dẫn sẽ là: /api/chat/<room_id>/messages/
    path('<str:room_id>/messages/', ChatHistoryView.as_view(), name='chat-history'),
    
    path('conversations/', ConversationListView.as_view(), name='conversation-list'),
]