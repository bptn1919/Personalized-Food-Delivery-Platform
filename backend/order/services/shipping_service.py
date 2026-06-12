import requests
import json
from django.conf import settings

class AhamoveAdapter:
    # Sử dụng môi trường Staging (Test) của Ahamove
    BASE_URL = "https://apistg.ahamove.com/v1" 
    
    # Lấy Token từ settings.py (hoặc biến môi trường .env)
    # Nếu chưa có, bạn điền tạm token test của Ahamove vào đây
    TOKEN = getattr(settings, 'AHAMOVE_API_TOKEN', 'YOUR_AHAMOVE_STG_TOKEN') 
    
    @staticmethod
    def estimate_fee(pickup_lat: float, pickup_lng: float, dropoff_lat: float, dropoff_lng: float, city_code: str = "SGN") -> int:
        """
        Gọi API Ahamove để lấy giá cước (Estimated Fee).
        """
        url = f"{AhamoveAdapter.BASE_URL}/order/estimated_fee"
        
        # Chọn mã dịch vụ xe máy (BIKE)
        # Mặc định cấu hình SGN-BIKE cho khu vực TP.HCM
        service_id = f"{city_code}-BIKE" 
        
        # Ahamove yêu cầu 'path' phải là chuỗi JSON chứa mảng các điểm đến
        path_data = [
            {
                "lat": pickup_lat,
                "lng": pickup_lng,
                "address": "Điểm lấy món" # Có thể truyền thêm địa chỉ text nếu có
            },
            {
                "lat": dropoff_lat,
                "lng": dropoff_lng,
                "address": "Điểm giao món"
            }
        ]
        
        payload = {
            "token": AhamoveAdapter.TOKEN,
            "order_time": 0, # 0 nghĩa là yêu cầu lấy giá cho thời điểm hiện tại
            "service_id": service_id,
            "path": json.dumps(path_data)
        }
        
        try:
            # 👇 TECH LEAD FIX: BẮT BUỘC có timeout=5.0 để chống nghẽn Server
            response = requests.get(url, params=payload, timeout=5.0) 
            
            if response.status_code == 200:
                data = response.json()
                # API Ahamove trả về tổng phí trong trường 'total_price'
                return int(data.get("total_price", 15000)) 
            else:
                # Ghi log lỗi nếu Token sai hoặc tham số không hợp lệ
                print(f"🚨 Ahamove API Error: [{response.status_code}] {response.text}")
                return 15000 # Fallback về mức giá sàn
                
        except requests.exceptions.RequestException as e:
            # Bắt lỗi mất mạng, timeout, hoặc DNS
            print(f"🚨 Ahamove Network Exception: {e}")
            return 15000 # Fallback an toàn