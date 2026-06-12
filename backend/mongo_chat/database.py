import pymongo
from django.conf import settings

client = pymongo.MongoClient(settings.MONGO_URI)
db = client[settings.MONGO_DB_NAME]

conversations_collection = db['conversations']
messages_collection = db['messages']
device_tokens_collection = db['device_tokens']

notifications_collection = db['notifications']

# --- TẠO INDEX (Rất quan trọng để query nhanh) ---
# Tự động chạy khi file này được import lần đầu
def setup_indexes():
    # Index để tìm tin nhắn trong 1 phòng nhanh nhất, sắp xếp theo thời gian
    messages_collection.create_index([("room_id", pymongo.ASCENDING), ("created_at", pymongo.DESCENDING)])
    
    # Index để tìm các phòng chat mà 1 user đang tham gia
    conversations_collection.create_index("participants.user_id")

setup_indexes()