from typing import List
from uuid import UUID

from django.http import HttpResponse
from ninja import Query

from utils.router.authenticate import AuthBear
from utils.router.controller import Controller, api, delete, get, post, put
from utils.router.paginate import paginate
from utils.types import AuthenticatedRequest
from exceptions.ingredient import IngredientImportFileInvalid, IngredientImportFileRequired

from .schemas.requests import FilterCategoryIngredientSchema, FilterIngredientSchema, IngredientSchema, OrderByIngredientSchema
from .schemas.requests import (
    IngredientAliasCreateSchema,
    IngredientSuggestionApproveAliasSchema,
    IngredientSuggestionApproveNewSchema,
    IngredientSuggestionOrderBySchema,
    IngredientSuggestionRejectSchema,
    IngredientSearchSchema,
    IngredientSuggestionFilterSchema,
    IngredientSuggestionResolveSchema,
    UserIngredientPreferenceSchema,
)
from .schemas.responses import (
    IngredientAliasResponse,
    IngredientAutocompleteItem,
    IngredientImportResult,
    IngredientResponse,
    IngredientSearchItem,
    IngredientSuggestionResponse,
    IngredientSuggestionApproveNewResponse,
    IngredientSuggestionApproveAliasResponse,
    IngredientSuggestionRejectResponse,
    UserIngredientPreferenceResponse,
)
from .services import IngredientService, IngredientSuggestionService
from utils.permissions.decorators import require_group

from utils.enums import UserTypeEnum

@api(prefix_or_class="ingredients", tags=["Ingredient"], auth=AuthBear())
class IngredientController(Controller):
    def __init__(self, service: IngredientService, suggestion_service: IngredientSuggestionService) -> None:
        self.service = service
        self.suggestion_service = suggestion_service

    @post("/", response=IngredientResponse)
    @require_group(UserTypeEnum.ADMIN)
    def create_new_ingredient(self, request: AuthenticatedRequest, payload: IngredientSchema):
        """[ADMIN] Tạo mới 1 ingredient chuẩn vào hệ thống (src USDA)"""
        return self.service.create_new_ingredient(user=request.user, payload=payload)

   
    @get("/", response=IngredientResponse, paginate=True)
    @paginate
    
    def get_all_ingredients(
        self,
        request: AuthenticatedRequest,
        filter: FilterIngredientSchema = Query(...),
        order_by: OrderByIngredientSchema = Query(...),
        
    ):
        return self.service.get_all_ingredients(filter=filter, order_by=order_by)
    
    
    @get("/chef", response=IngredientSearchItem, paginate=True)
    @paginate
    @require_group(UserTypeEnum.CHEF)
    def get_all_ingredients_for_chef(
        self,
        request: AuthenticatedRequest,
        filter: FilterIngredientSchema = Query(...),
        order_by: OrderByIngredientSchema = Query(...),
    ):
        """[CHEF] Lấy danh sách nguyên liệu, bao gồm cả nguyên liệu chuẩn và nguyên liệu do chef đó đề xuất thêm vào hệ thống nhưng đang PENDING
        UI nên hiển thị:
        - Nguyên liệu chuẩn: hiển thị bình thường
        - Nguyên liệu PENDING: hiển thị mờ hơn, hiển thị sau cùng có thêm thông tin "Đang chờ duyệt" 
        """
        return self.service.get_all_ingredients_for_chef(user=request.user, filter=filter, order_by=order_by)

    
    @get("/export-template", response=None)
    @require_group(UserTypeEnum.ADMIN)
    def export_ingredient_template(self, request: AuthenticatedRequest):
        """[ADMIN] Tải về file excel mẫu để import nguyên liệu"""
        file_bytes = self.service.export_ingredient_template_excel(user=request.user)

        response = HttpResponse(
            file_bytes,
            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
        response["Content-Disposition"] = (
            "attachment; filename=ingredient_import_template.xlsx"
        )
        return response
    @post(
        "/import-excel",
        response=IngredientImportResult,
        exceptions=(IngredientImportFileRequired, IngredientImportFileInvalid),
    )
    @require_group(UserTypeEnum.ADMIN)
    def import_ingredients_excel(self, request: AuthenticatedRequest):
        """[ADMIN] Import nguyên liệu hàng loạt từ file excel, file phải có định dạng giống file mẫu tải về từ API export-template"""
        print("DEBUG: request.FILES =", request.FILES)
        print("DEBUG: request.POST =", request.POST)
        
        excel_file = request.FILES.get("file")
        
        if not excel_file:
            print("DEBUG: No file found in request!")
            print("DEBUG: request.FILES keys =", list(request.FILES.keys()) if request.FILES else "empty")
        
        return self.service.import_ingredients_from_excel(user=request.user, file=excel_file)

    @get("/search", response=IngredientSearchItem, paginate=True)
    @paginate
    @require_group(UserTypeEnum.CHEF)
    def search_ingredients(
        self,
        request: AuthenticatedRequest,
        payload: IngredientSearchSchema = Query(...),
        filter: FilterCategoryIngredientSchema = Query(...),
    ):
        query = payload.query or ""
        return self.service.search_ingredients(
            user=request.user, 
            query=query,
            filter=filter,
            limit=payload.limit,
            )

    @get("/autocomplete", response=list[IngredientAutocompleteItem])
    @require_group(UserTypeEnum.CHEF)
    def autocomplete_ingredients(
        self,
        request: AuthenticatedRequest,
        query: str = Query(""),
        limit: int = Query(10, ge=1, le=50),
    ):
        return self.service.autocomplete_ingredients(query=query, limit=limit)

    @post("/aliases", response=IngredientAliasResponse)
    @require_group(UserTypeEnum.ADMIN)
    def create_ingredient_alias(self, request: AuthenticatedRequest, payload: IngredientAliasCreateSchema):
        """[ADMIN] Tạo alias cho một ingredient chuẩn, giúp hệ thống nhận diện được các tên gọi khác nhau của cùng một nguyên liệu, ví dụ: "ớt bột" và "ớt đỏ xay" có thể là alias của cùng một ingredient chuẩn "ớt đỏ" """
        return self.service.create_ingredient_alias(user=request.user, payload=payload)

    @get("/aliases", response=list[IngredientAliasResponse])
    @require_group(UserTypeEnum.ADMIN)
    def list_ingredient_aliases(self, request: AuthenticatedRequest, search: str | None = Query(None)):
        """[ADMIN] Danh sách các alias đã tạo, có thể search theo tên alias hoặc tên ingredient chuẩn"""
        return self.service.list_ingredient_aliases(search=search)

    @get("/suggestions/all", response=IngredientSuggestionResponse, paginate=True)
    @paginate
    @require_group(UserTypeEnum.ADMIN)
    def list_ingredient_suggestions(
        self,
        request: AuthenticatedRequest,
        filter: IngredientSuggestionFilterSchema = Query(...),
        order_by: IngredientSuggestionOrderBySchema = Query(...),
    ):
        """[ADMIN] Danh sách các đề xuất thêm ingredient, có thể filter theo trạng thái và order by ngày tạo"""
        return self.service.list_ingredient_suggestions(filter=filter, order_by=order_by)
    
    @get("/suggestions/me", response=IngredientSuggestionResponse, paginate=True)
    @paginate
    @require_group(UserTypeEnum.CHEF)
    def get_my_ingredient_suggestions(
        self,
        request: AuthenticatedRequest,
        filter: IngredientSuggestionFilterSchema = Query(...),
        order_by: IngredientSuggestionOrderBySchema = Query(...),
    ):
        """[CHEF] Danh sách các đề xuất thêm ingredient của chính chef đó, có thể filter theo trạng thái và order by ngày tạo"""
        return self.service.get_my_ingredient_suggestions(
            user=request.user,
            filter=filter,
            order_by=order_by,
        )
    
    @put("/suggestions/{uid}/deleted", response=bool)
    @require_group(UserTypeEnum.CHEF)
    def soft_delete_ingredient_suggestion(self, request: AuthenticatedRequest, uid: UUID):
        """[CHEF] Xóa mềm đề xuất thêm ingredient của chính chef đó, chỉ có tác dụng với các suggestion đang PENDING, sau khi soft delete thì chef có thể tạo lại suggestion mới nếu muốn"""
        return self.suggestion_service.soft_delete_ingredient_suggestion(user=request.user, uid=uid)

    @post("/suggestions/{uid}/approve-new", response=IngredientSuggestionApproveNewResponse)
    @require_group(UserTypeEnum.ADMIN)
    def approve_new_ingredient_suggestion(
        self,
        request: AuthenticatedRequest,
        uid: UUID,
        payload: IngredientSuggestionApproveNewSchema,
    ):
        """[ADMIN] Phê duyệt đề xuất thêm ingredient mới vào hệ thống"""
        return self.service.approve_new_ingredient_suggestion(user=request.user, uid=uid, payload=payload)

    @post("/suggestions/{uid}/approve-alias", response=IngredientSuggestionApproveAliasResponse)
    @require_group(UserTypeEnum.ADMIN)
    def approve_alias_ingredient_suggestion(
        self,
        request: AuthenticatedRequest,
        uid: UUID,
        payload: IngredientSuggestionApproveAliasSchema,
    ):
        """[ADMIN] Phê duyệt đề xuất thêm alias cho ingredient"""
        return self.service.approve_alias_ingredient_suggestion(user=request.user, uid=uid, payload=payload)

    @post("/suggestions/{uid}/reject", response=IngredientSuggestionRejectResponse)
    @require_group(UserTypeEnum.ADMIN)
    def reject_ingredient_suggestion(
        self,
        request: AuthenticatedRequest,
        uid: UUID,
        payload: IngredientSuggestionRejectSchema,
    ):
        """[ADMIN] Từ chối đề xuất thêm ingredient hoặc alias, phải điền lý do từ chối để feedback cho chef"""
        return self.service.reject_ingredient_suggestion(request.user, uid, payload.rejection_reason)

    @post("/me/favourites", response=UserIngredientPreferenceResponse)
    def add_favourite_ingredient(
        self,
        request: AuthenticatedRequest,
        payload: UserIngredientPreferenceSchema,
    ):
        return self.service.add_favourite_ingredient(user=request.user, payload=payload)

    @get("/me/favourites", response=list[UserIngredientPreferenceResponse])
    def list_favourite_ingredients(self, request: AuthenticatedRequest):
        return self.service.list_favourite_ingredients(user=request.user)

    @delete("/me/favourites/{ingredient_uid}", response=bool)
    def remove_favourite_ingredient(self, request: AuthenticatedRequest, ingredient_uid: UUID):
        return self.service.remove_favourite_ingredient(user=request.user, ingredient_uid=ingredient_uid)

    @post("/me/allergies", response=UserIngredientPreferenceResponse)
    def add_allergic_ingredient(
        self,
        request: AuthenticatedRequest,
        payload: UserIngredientPreferenceSchema,
    ):
        return self.service.add_allergic_ingredient(user=request.user, payload=payload)

    @get("/me/allergies", response=list[UserIngredientPreferenceResponse])
    def list_allergic_ingredients(self, request: AuthenticatedRequest):
        return self.service.list_allergic_ingredients(user=request.user)

    @delete("/me/allergies/{ingredient_uid}", response=bool)
    def remove_allergic_ingredient(self, request: AuthenticatedRequest, ingredient_uid: UUID):
        return self.service.remove_allergic_ingredient(user=request.user, ingredient_uid=ingredient_uid)

    @get("/{uid}", response=IngredientResponse)
    def get_ingredient(self, uid: UUID):
        return self.service.get_ingredient_by_uid(uid=uid)

    @put("/{uid}", response=IngredientResponse)
    @require_group(UserTypeEnum.ADMIN)
    def update_ingredient(
        self, request: AuthenticatedRequest, uid: UUID, payload: IngredientSchema
    ):
        return self.service.update_ingredient(user=request.user, uid=uid, payload=payload)

    @put("/{uid}/deleted", response=bool)
    @require_group(UserTypeEnum.ADMIN)
    def soft_delete_ingredient(self, request: AuthenticatedRequest, uid: UUID):
        return self.service.soft_delete_ingredient(uid=uid, user=request.user)

    @delete("/{uid}", response=bool)
    @require_group(UserTypeEnum.ADMIN)
    def hard_delete_ingredient(self, request: AuthenticatedRequest, uid: UUID):
        return self.service.hard_delete_ingredient(uid=uid)

    @put("/{uid}/restored", response=bool)
    @require_group(UserTypeEnum.ADMIN)
    def restore_ingredient(self, request: AuthenticatedRequest, uid: UUID) -> bool:
        return self.service.restore_ingredient(user=request.user, uid=uid)
