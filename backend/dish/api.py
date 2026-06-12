from uuid import UUID
from typing import cast, Optional

from ninja import Query

from utils.enums import UserTypeEnum
from utils.router.authenticate import AuthBear
from utils.router.controller import Controller, api, delete, get, post, put, patch
from utils.router.paginate import paginate
from utils.types import AuthenticatedRequest
from utils.permissions.decorators import require_permission, require_object_permission, require_group
from exceptions.dishes import DishIngredientAlreadyExists, DishPermissionDenied, DishIngredientNotFoundException
from exceptions.dishes import DishLocationNotFoundException, DishLocationHasChildrenException
from utils.exceptions import PermissionDeniedError
from dish.models import Dish, DishIngredient

from .schemas.requests import (
    FilterDishSchema,
    DishIngredientCreateSchema,
    DishIngredientSchema,
    DishAvailabilitySchema,
    DishWithAttachmentSchema,
    DishUpdateSchema,
    DishLocationCreateSchema,
    DishLocationUpdateSchema,
    DishIngredientSuggestionSchema,
    DishIngredientCreateBySuggestionSchema
)
from .schemas.responses import (
    DishIngredientPrivateResponse,
    DishIngredientSuggestionPreviewResponse,
    DishLocationShortResponse,
    DishResponse,
    DishAvailabilityListResponse,
    DishIngredientResponse,
    DishIngredientPreviewResponse,
    DishIngredientSaveResponse,
    TopDishResponse,
    DishLocationResponse,
    DishLocationTreeResponse,
    DishIngredientPublicResponse, DishIngredientBySuggestionResponse,
    DishSearchResponseSchema,
    DishListResponse,
)
from ingredient.schemas.responses import IngredientSuggestionResponse
from .services import DishService
from .services.search import DishSearchService
from admin.permissions import require_admin, require_admin_or_chef
from utils.enums import SortByEnum


@api(prefix_or_class="dishes", tags=["Dish"], auth=AuthBear())
class DishController(Controller):
    def __init__(self, service: DishService) -> None:
        self.service = service

    @post("/", response=DishResponse, exceptions=(PermissionDeniedError,))
    @require_group(UserTypeEnum.CHEF)
    def create_dish(self, request: AuthenticatedRequest, payload: DishWithAttachmentSchema):
        """
        Tạo dish với attachment
        
        Flow:
        1. Chef gọi POST /api/attachments/presigned-url → nhận {uid, url}
        2. Chef PUT file lên presigned_url (upload trực tiếp lên S3) được request từ FRONTEND (browser / mobile app) gửi TRỰC TIẾP lên S3, vui lòng nén ảnh trước khi lưu
        3. Chef gọi PUT /api/attachments/{uid}/completed → backend verify
        4. Chef gọi API này với attachment_uid để tạo dish
        
        Request body:
        {
            "name": "Phở bò",
            "category": "FOOD",
            "price": 55000,
            "description": "",
            "status": "AVAILABLE",
            "attachment_uid": "xxx-xxx-xxx"
        }
        """
        return self.service.create_dish(user=request.user, payload=payload)

    @get("/", response=DishListResponse, paginate=True, auth=False)
    @paginate
    def get_all_dishes(
        self,
        request,
        filter: FilterDishSchema = Query(...),
        sort_by: SortByEnum = Query(SortByEnum.RATING_DESC),
    ):
        user = getattr(request, "user", None)
        return self.service.get_all_dishes(filter=filter, sort_by=sort_by, user=user)
    
    @get("/mine", response=DishListResponse, paginate=True)
    @paginate
    @require_group(UserTypeEnum.CHEF)
    def get_all_my_dishes(
        self, 
        request: AuthenticatedRequest,
        filter: FilterDishSchema = Query(...),
        sort_by: SortByEnum = Query(SortByEnum.RATING_DESC),
    ):
        """
        Lấy toàn bộ danh sách món ăn của chính tôi (Dành riêng cho Chef)
        """
       
        return self.service.get_dishes_by_chef(
            chef_id=str(request.user.id), 
            filter=filter, 
            sort_by=sort_by, 
            user=request.user
        )
        

    @get("/search", response=DishSearchResponseSchema, auth=False)
    def search_dishes(
        self,
        request,
        q: str = Query(..., description="Search query"),
        category: Optional[str] = Query(None, description="Filter by category"),
        location_id: Optional[int] = Query(None, description="Filter by location ID"),
        status: Optional[str] = Query(None, description="Filter by status"),
        available_today: bool = Query(False, description="Only available today"),
        limit: int = Query(50, ge=1, le=100, description="Max results"),
    ):
        """
        Production-grade dish search endpoint
        
        Pipeline: Normalize → Retrieve (Fuzzy + Alias) → Semantic → Rank → Filter
        
        Query parameters:
        - q: search query (required)
        - category: filter by DishCategoryEnum (optional)
        - location_id: filter by location ID (optional)
        - status: filter by status (optional)
        - available_today: show only dishes available today (default: false)
        - limit: max results (default: 50, max: 100)
        
        Response:
        {
            "query": "phở",
            "total": 5,
            "results": [
                {
                    "uid": "xxx",
                    "name": "Phở bò",
                    "category": "FOOD",
                    "price": 55000,
                    "description": "Phở bò truyền thống",
                    "status": "AVAILABLE",
                    "rating": 4.5,
                    "popularity_score": 95,
                    "search_score": 1.95,
                    "image_url": "https://...",
                    "location_id": 1
                }
            ]
        }
        """
        user = getattr(request, "user", None)
        return DishSearchService.search(
            user=user,
            query=q,
            category=category,
            location_id=location_id,
            status=status,
            available_today=available_today,
            limit=limit,
        )

    @get("/top", response=list[TopDishResponse], auth=False)

    def get_top_dishes(self, limit: int = Query(10, ge=1, le=50)):
        return self.service.get_top_dishes(limit=limit)

    @get("/{uid}", response=DishResponse)
    def get_dish(self, request, uid: UUID):
        user = getattr(request, "user", None)
        return self.service.get_dish_by_uid(uid=uid, user=user)

    @patch("/{uid}", response=DishResponse, exceptions=(DishPermissionDenied,))
    @require_object_permission('dish.change_dish', Dish, owner_field='owner')
    def update_dish(
        self, request: AuthenticatedRequest, uid: UUID, payload: DishUpdateSchema
    ):
        return self.service.update_dish(user=request.user, uid=uid, payload=payload)

    #get các ingredient của một dish, dành cho cus, không cần auth
    @get("/{uid}/ingredients", response=DishIngredientPublicResponse, exceptions=(DishPermissionDenied,))
    def get_all_ingredients_of_dish_for_customers(self, uid: UUID):
        """[CUSTOMER]Lấy tất cả ingredient của dish, dành cho khách hàng, chỉ trả về thông tin public như tên ingredient và dữ liệu dinh dưỡng tổng hợp của dish"""
        return self.service.get_all_ingredients_of_dish_for_customers(uid=uid)
    
    @get("/{uid}/ingredients/chef", response=DishIngredientPrivateResponse, exceptions=(DishPermissionDenied,))
    @require_object_permission('dish.view_dish', Dish, owner_field='owner')
    def get_all_ingredients_of_dish_for_chefs(self, request: AuthenticatedRequest, uid: UUID):
        """[CHEF]Lấy tất cả ingredient của dish, dành cho chef, có thêm thông tin private như confidence, note, và dữ liệu dinh dưỡng chi tiết của từng ingredient"""
        return self.service.get_all_ingredients_of_dish_for_chefs(uid=uid)
    
    @post("/{uid}/ingredients/preview", response=DishIngredientPreviewResponse, exceptions=(DishPermissionDenied,))
    @require_object_permission('dish.view_dish', Dish, owner_field='owner')
    def preview_ingredient_for_dish(self, request: AuthenticatedRequest, uid: UUID, payload: DishIngredientCreateSchema):
        """[CHEF]Xem trước ingredient sẽ ảnh hưởng như thế nào đến dish nếu thêm vào (dựa trên dữ liệu dinh dưỡng)"""
        return self.service.preview_ingredient_for_dish(uid=uid, payload=payload)
    
    @post("/{uid}/ingredients", response=DishIngredientSaveResponse, exceptions=(DishPermissionDenied, DishIngredientAlreadyExists))
    @require_object_permission('dish.change_dish', Dish, owner_field='owner')
    def add_ingredient_to_dish(self, request:AuthenticatedRequest, uid: UUID, payload: DishIngredientCreateSchema):
        """[CHEF]thêm nguyên liệu có sẵn trong hệ thống, nếu muốn thêm nguyên liệu mới chưa có trong hệ thống thì dùng API suggest_ingredient_for_dish phía dưới"""
        return self.service.add_ingredient_to_dish(user=request.user, uid=uid, payload=payload)
    
    #API add nguyên liệu được chính chef đó suggest trước đó nhưng đang PENDING vào dish
    @post("/{uid}/ingredients/add-suggested", response=DishIngredientBySuggestionResponse, exceptions=(DishPermissionDenied, DishIngredientAlreadyExists))
    @require_object_permission('dish.change_dish', Dish, owner_field='owner')
    def add_suggested_ingredient_to_dish(self, request: AuthenticatedRequest, uid: UUID, payload: DishIngredientCreateBySuggestionSchema):
        """[CHEF]thêm nguyên liệu đã được suggest trước đó (PENDING) vào dish"""
        return self.service.add_suggested_ingredient_to_dish(user=request.user, uid=uid, payload=payload)
    
    @put("/{uid}/deleted", response=bool, exceptions=(DishPermissionDenied,))
    @require_object_permission('dish.change_dish', Dish, owner_field='owner')
    def soft_delete_dish(self, request: AuthenticatedRequest, uid: UUID):
        return self.service.soft_delete_dish(uid=uid, user=request.user)

    @delete("/{uid}", response=bool, exceptions=(DishPermissionDenied,))
    @require_group(UserTypeEnum.ADMIN)
    def hard_delete_dish(self, request: AuthenticatedRequest, uid: UUID):
        return self.service.hard_delete_dish(user=request.user, uid=uid)

    @put("/{uid}/restored", response=bool, exceptions=(DishPermissionDenied,))
    @require_object_permission('dish.change_dish', Dish, owner_field='owner', check_deleted=False)
    def restore_dish(self, request: AuthenticatedRequest, uid: UUID) -> bool:
        print("🔄 [API] Received request to restore dish with UID:", uid)
        return self.service.restore_dish(user=request.user, uid=uid)

    @get("/{uid}/availabilities", response=DishAvailabilityListResponse)
    def get_availabilities(self, request: AuthenticatedRequest, uid: UUID):
        return self.service.get_dish_availabilities(uid=uid)

    @post("/{uid}/availabilities", response=DishAvailabilityListResponse, exceptions=(PermissionDeniedError,))
    @require_object_permission('dish.change_dish', Dish, owner_field='owner')
    def create_availabilities(self, request: AuthenticatedRequest, uid: UUID, payload: DishAvailabilitySchema):
        return self.service.create_dish_availabilities(uid=uid, payload=payload)
    
    @post("/{uid}/ingredients/suggestion/preview", response=DishIngredientSuggestionPreviewResponse, exceptions=(DishPermissionDenied, DishIngredientAlreadyExists, PermissionDeniedError))
    @require_object_permission('dish.change_dish', Dish, owner_field='owner')
    def preview_suggest_ingredient_for_dish(self, request: AuthenticatedRequest, uid: UUID, payload: DishIngredientSuggestionSchema):
        """Xem trước đề xuất thêm ingredient vào dish sẽ ảnh hưởng như thế nào đến dish nếu được duyệt (dựa trên dữ liệu dinh dưỡng)"""
        return self.service.preview_suggest_ingredient_for_dish(uid=uid, payload=payload, user=request.user)
    #----- SUGGEST NEW INGREDIENT FOR DISH (FLpreview_suggest_ingredient_for_dishOW: CHEF SUGGEST → ADMIN APPROVE/REJECT) -----#
    @post("/{uid}/ingredients/suggestion", response=IngredientSuggestionResponse, exceptions=(DishPermissionDenied, DishIngredientAlreadyExists))
    @require_object_permission('dish.change_dish', Dish, owner_field='owner')
    def suggest_ingredient_for_dish(self, request: AuthenticatedRequest, uid: UUID, payload: DishIngredientSuggestionSchema):
        """Chef đề xuất thêm ingredient vào dish, sẽ tạo ra DishIngredient với trạng thái pending, admin sẽ duyệt sau"""
        return self.service.suggest_ingredient_for_dish(user=request.user, uid=uid, payload=payload)

@api(prefix_or_class="dishingredients", tags=["Dish Ingredient"], auth=AuthBear())
class DishIngredientController(Controller):
    def __init__(self, service: DishService) -> None:
        self.service = service

    @get("/{uid}", response=DishIngredientResponse, exceptions=(DishIngredientNotFoundException,))
    @require_object_permission('dish.change_dish', DishIngredient, owner_field='created_by')
    def get_dish_ingredient(self, request: AuthenticatedRequest, uid: UUID):
        return self.service.get_dish_ingredient_by_uid(uid=uid)
    
    @patch("/{uid}", response=DishIngredientSaveResponse, exceptions=(DishPermissionDenied, PermissionDeniedError))
    @require_object_permission('dish.change_dish', DishIngredient, owner_field='created_by')
    def update_dish_ingredient(self, request: AuthenticatedRequest, uid: UUID, payload: DishIngredientSchema):
        """Cập nhật thông tin DishIngredient dành cho chef sau khi đã add vào dish"""
        return self.service.update_dish_ingredient(user=request.user, uid=uid, payload=payload)

    @patch("/{uid}/soft-deleted", response=bool, exceptions=(DishPermissionDenied, PermissionDeniedError))
    @require_object_permission('dish.change_dish', DishIngredient, owner_field='created_by')
    def soft_delete_dish_ingredient(self, request: AuthenticatedRequest, uid: UUID):
        """Soft delete DishIngredient"""
        return self.service.soft_delete_dish_ingredient(uid=uid, user=request.user)

@api(prefix_or_class="dish-locations", tags=["Dish Location"], auth=AuthBear())
class DishLocationController(Controller):
    def __init__(self, service: DishService) -> None:
        self.service = service

    @post("/", response=DishLocationResponse, exceptions=(DishLocationNotFoundException,))
    @require_group(UserTypeEnum.ADMIN)
    def create_dish_location(self, request: AuthenticatedRequest, payload: DishLocationCreateSchema):
        return self.service.create_dish_location(payload=payload)

    @get("/", response=list[DishLocationResponse])
    def get_dish_locations(self, parent_id: int | None = Query(None), type: str | None = Query(None)):
        return self.service.get_dish_locations(parent_id=parent_id, type=type)

    @get("/tree", response=list[DishLocationTreeResponse])
    def get_dish_location_tree(self):
        return self.service.get_dish_location_tree()
    
        # lấy danh sách các location loại country
    @get("/countries", response=list[DishLocationShortResponse])
    def get_country_locations(self):
        return self.service.get_country_locations()

    @get("/{location_id}", response=DishLocationResponse, exceptions=(DishLocationNotFoundException,))
    def get_dish_location(self, location_id: int):
        return self.service.get_dish_location_by_id(location_id=location_id)
    

    @patch("/{location_id}", response=DishLocationResponse, exceptions=(DishLocationNotFoundException, PermissionDeniedError))
    @require_group(UserTypeEnum.ADMIN)
    def update_dish_location(self, request: AuthenticatedRequest, location_id: int, payload: DishLocationUpdateSchema):
        return self.service.update_dish_location(location_id=location_id, payload=payload)

    @delete("/{location_id}", response=bool, exceptions=(DishLocationNotFoundException, DishLocationHasChildrenException, PermissionDeniedError))
    @require_group(UserTypeEnum.ADMIN)
    def delete_dish_location(self, request: AuthenticatedRequest, location_id: int):
        return self.service.delete_dish_location(location_id=location_id)
    