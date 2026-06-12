from django.urls import path
from .views import MongoConversationListView, MongoMessageHistoryView, RegisterDeviceView, UnregisterDeviceView, MongoGetOrCreateRoomView
from . import views

urlpatterns = [
    # API: /api/mongo-chat/conversations/
    path('conversations/', MongoConversationListView.as_view(), name='mongo-conversation-list'),
    
    path('room/get-or-create/', MongoGetOrCreateRoomView.as_view(), name='get-or-create-room'),
    
    # API: /api/mongo-chat/<room_id>/messages/
    path('<str:room_id>/messages/', MongoMessageHistoryView.as_view(), name='mongo-chat-history'),
    
    path('device/register/', RegisterDeviceView.as_view(), name='register-device'),
    path('device/unregister/', UnregisterDeviceView.as_view(), name='unregister_device'),
    
    path('notifications/', views.fetch_notifications),
    path('notifications/<str:noti_id>/read/', views.mark_notification_read),
    path('notifications/<str:noti_id>/', views.delete_notification),
]