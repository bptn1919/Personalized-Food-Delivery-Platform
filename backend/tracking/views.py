from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status

from .schemas.location_schemas import UpdateLocationSchema, NearbyChefSchema
from .services.location_service import LocationService

class UpdateChefLocationAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        # 1. Gọi Service
        location_obj = LocationService.get_or_create_location(request.user)
        
        # 2. Đưa vào Schema xử lý lưu trữ
        schema = UpdateLocationSchema(location_obj, data=request.data, partial=True)
        if schema.is_valid():
            schema.save()
            return Response({"success": True, "message": "Location updated"}, status=status.HTTP_200_OK)
        
        return Response(schema.errors, status=status.HTTP_400_BAD_REQUEST)


class GetNearbyChefsAPIView(APIView):
    def get(self, request):
        # 1. Validate Input
        try:
            user_lat = float(request.query_params.get('lat'))
            user_lng = float(request.query_params.get('lng'))
        except (TypeError, ValueError):
            return Response({"error": "Valid lat and lng are required."}, status=status.HTTP_400_BAD_REQUEST)

        radius_km = float(request.query_params.get('radius_km', 5.0))

        # 2. Gọi Service xử lý Logic DB
        nearby_locations = LocationService.get_nearby_chefs_query(user_lat, user_lng, radius_km)
        
        # 3. Đưa vào Schema ép kiểu JSON
        schema = NearbyChefSchema(nearby_locations, many=True)
        
        return Response({
            "search_center": {"lat": user_lat, "lng": user_lng},
            "radius_km": radius_km,
            "results": schema.data
        }, status=status.HTTP_200_OK)