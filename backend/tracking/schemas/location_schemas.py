from ninja import Schema
from typing import List, Optional
from datetime import datetime

# Request Schemas
class UpdateLocationInput(Schema):
    latitude: float
    longitude: float
    heading: Optional[float] = None

# Response Schemas
class SuccessResponse(Schema):
    success: bool
    message: str

class NearbyChefItem(Schema):
    # --- THÔNG TIN ĐỊNH DANH & UI ---
    chef_id: int
    chef_name: str
    avatar: Optional[str] = None
    
    # --- THÔNG TIN VỊ TRÍ ---
    latitude: float
    longitude: float
    distance_km: float
    
    # --- THÔNG TIN UY TÍN (SOCIAL PROOF) ---
    avg_rating: float = 0.0
    is_food_safety_certified: bool = False

    @staticmethod
    def resolve_chef_id(obj):
        return obj.chef.id
        
    @staticmethod
    def resolve_chef_name(obj):
        return obj.chef.get_full_name() or f"Chef {obj.chef.id}"

    @staticmethod
    def resolve_avatar(obj):
        profile = getattr(obj.chef, 'chef_profile', None)
        return profile.avatar.public_url if profile and profile.avatar else None

    @staticmethod
    def resolve_avg_rating(obj):
        profile = getattr(obj.chef, 'chef_profile', None)
        return getattr(profile, 'avg_rating', 0.0) if profile else 0.0

    @staticmethod
    def resolve_is_food_safety_certified(obj):
        # Ưu tiên lấy từ annotate để tránh N+1 Query
        if hasattr(obj.chef, 'has_safety_cert'):
            return obj.chef.has_safety_cert
            
        return obj.chef.certificate_fk_owner.filter(
            certificate_type="FOOD_SAFETY", 
            status="APPROVED"
        ).exists()

class NearbyChefsResponse(Schema):
    search_center: dict
    radius_km: float
    results: List[NearbyChefItem]
    
class LocationPoint(Schema):
    latitude: float
    longitude: float

class OrderTrackingResponse(Schema):
    order_id: int
    status: str
    chef_location: LocationPoint
    destination: LocationPoint
    chef_name: str