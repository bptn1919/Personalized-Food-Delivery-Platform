from utils.router.controller import Controller, api, delete, get, post, put, patch
from utils.router.authenticate import AuthBear
from utils.permissions.decorators import require_group
from utils.enums import UserTypeEnum     # Tuỳ chỉnh lại đường dẫn import của bạn
from .services.location_service import LocationService
from .schemas.location_schemas import UpdateLocationInput, SuccessResponse, NearbyChefsResponse, OrderTrackingResponse, LocationPoint

# Giả sử bạn config api_controller thay vì @api
@api(prefix_or_class="tracking", tags=["Tracking"], auth=AuthBear())
class TrackingController(Controller):
    def __init__(self, service: LocationService) -> None:
        self.service = service

    @post("/chef/location", response=SuccessResponse)
    @require_group(UserTypeEnum.CHEF) # Chỉ Chef mới được bắn tọa độ lên
    def update_location(self, request, payload: UpdateLocationInput):
        """
        API để app của Chef liên tục bắn tọa độ vị trí hiện tại lên server
        """
        self.service.update_chef_location(
            user=request.user,
            latitude=payload.latitude,
            longitude=payload.longitude,
            heading=payload.heading
        )
        return {"success": True, "message": "Location updated successfully"}


    @get("/chefs/nearby", response=NearbyChefsResponse)
    @require_group(UserTypeEnum.CUSTOMER) # Khách hàng tìm Chef xung quanh
    def get_nearby_chefs(self, request, lat: float, lng: float, radius_km: float = 5.0):
        """
        API tìm kiếm các Chef đang hoạt động trong bán kính (mặc định 5km)
        """
        nearby_locations = self.service.get_nearby_chefs(lat, lng, radius_km)
        
        return {
            "search_center": {"lat": lat, "lng": lng},
            "radius_km": radius_km,
            "results": list(nearby_locations) # Ninja tự động parse list object này vào Schema
        }
        
        
    @get("/order/{order_id}/tracking", response=OrderTrackingResponse)
    @require_group(UserTypeEnum.CUSTOMER) # Khách hàng xem đơn của mình
    def get_order_tracking(self, request, order_id: int):
        """
        API lấy thông tin ban đầu để vẽ bản đồ Tracking: Điểm đến và Vị trí Chef.
        """
        # 1. Lấy thông tin đơn hàng (Mock logic - bạn thay bằng query DB của bạn)
        from tracking.models import Order 
        order = Order.objects.select_related('chef').get(id=order_id, customer=request.user)
        
        # 2. Lấy vị trí hiện tại của Chef
        from tracking.models import ChefLocation
        chef_loc = ChefLocation.objects.get(chef=order.chef)
        
        # 3. Trả về cả 2 tọa độ
        return {
            "order_id": order.id,
            "status": order.status,
            "chef_name": order.chef.get_full_name() or f"Chef {order.chef.id}",
            "chef_location": {
                "latitude": chef_loc.latitude,
                "longitude": chef_loc.longitude,
            },
            "destination": {
                "latitude": order.delivery_lat, # Tọa độ nhà khách hàng lưu lúc đặt đơn
                "longitude": order.delivery_lng,
            }
        }
        
        
        # ở address thêm tính năng để lấy lat và lng của khách hàng lúc đặt đơn, lưu vào DB để tiện cho việc tracking sau này.
        # Khi khách hàng đặt đơn, hệ thống sẽ lưu luôn lat và lng của khách hàng vào DB (ví dụ: order.delivery_lat, order.delivery_lng) để sau này khi tracking có thể lấy ra dễ dàng.
        # thực hiện UI.