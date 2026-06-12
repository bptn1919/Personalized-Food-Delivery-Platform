from django.db.models.expressions import RawSQL
from tracking.models import ChefLocation
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from certificate.models import Certificate
from django.db.models import OuterRef, Exists

class LocationService:
    def update_chef_location(self, user, latitude: float, longitude: float, heading: float = None):
        location_obj, created = ChefLocation.objects.get_or_create(chef=user)
        location_obj.latitude = latitude
        location_obj.longitude = longitude
        if heading is not None:
            location_obj.heading = heading
        location_obj.save()

        # 2. BẮN DỮ LIỆU QUA REDIS (REAL-TIME)
        # Giả sử chúng ta dùng format tên group là: tracking_chef_{chef_id}
        group_name = f"tracking_chef_{user.id}"
        channel_layer = get_channel_layer()
        
        async_to_sync(channel_layer.group_send)(
            group_name,
            {
                # "type" phải trùng với tên hàm xử lý trong Consumer của Customer
                "type": "send_location_update", 
                "data": {
                    "latitude": latitude,
                    "longitude": longitude,
                    "heading": heading,
                    "chef_id": user.id
                }
            }
        )

        return location_obj

    def get_nearby_chefs(self, lat: float, lng: float, radius_km: float):
        haversine_sql = """
            6371 * acos(
                cos(radians(%s)) * cos(radians(latitude)) *
                cos(radians(longitude) - radians(%s)) +
                sin(radians(%s)) * sin(radians(latitude))
            )
        """
        
        # 👇 TECH LEAD FIX: Định nghĩa một câu subquery để check chứng nhận An toàn thực phẩm
        safety_cert_subquery = Certificate.objects.filter(
            owner_id=OuterRef('chef_id'), # owner là User, chef_id ở ChefLocation trỏ đến User
            certificate_type="FOOD_SAFETY",
            status="APPROVED"
        )

        return (
            ChefLocation.objects
            # 👇 TECH LEAD FIX 1: Gom User và Profile vào cùng 1 câu lệnh JOIN
            .select_related('chef', 'chef__chef_profile') 
            .annotate(
                distance_km=RawSQL(haversine_sql, (lat, lng, lat)),
                # 👇 TECH LEAD FIX 2: Check chứng chỉ ngay từ dưới Database, đính kèm vào 'has_safety_cert'
                has_safety_cert=Exists(safety_cert_subquery) 
            )
            .filter(
                latitude__isnull=False,
                longitude__isnull=False,
                distance_km__lte=radius_km
            )
            .order_by('distance_km')[:10]
        )