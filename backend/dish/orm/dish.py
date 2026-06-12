from typing import Any, List, Optional, cast
from uuid import UUID

from django.db import IntegrityError
from django.db.models import Avg, CharField, Count, Exists, ExpressionWrapper, F, FloatField, IntegerField, OuterRef, Prefetch, Subquery, Sum, Value, Case, When, BooleanField
from django.db.models.functions import Coalesce
from profile.models import CustomerFavoriteDish, CustomerProfile
from ingredient.models import AllergicIngredient, Ingredient
from attachment.models import Attachment
from dish.models import Dish, DishIngredient,DishAvailability, DishLocation
from dish.schemas.requests import FilterDishSchema, DishIngredientSuggestionSchema
from utils.functions.check_relation import has_related_objects
from utils.types import TUser
from django.utils import timezone
from django.db import transaction
from datetime import date
from order.models import OrderItem
from review.models import Review
from utils.enums import AllergyModeEnum, DishLocationTypeEnum, OrderStatusEnum, IngredientSourceEnum, IngredientImportStatusEnum, SortByEnum
from ingredient.models import IngredientSuggestion



class DishORM:
    @staticmethod
    def create_dish_with_attachment(user: TUser, dish_data: dict, attachment=None):
        """Tạo dish với attachment (presigned URL flow)"""
        return Dish.objects.create(
            **dish_data, owner=user, updater=user, attachment=attachment
        )

    @staticmethod
    def get_all_dishes(filter, sort_by=SortByEnum.RATING_DESC, user=None):

        today = timezone.localdate()

        sold_count_subquery = (
            OrderItem.objects
            .filter(dish_id=OuterRef("uid"), order__status=OrderStatusEnum.COMPLETED)
            .values("dish_id")
            .annotate(total_quantity=Sum("quantity"))
            .values("total_quantity")[:1]
        )

        availability_subquery = (
            DishAvailability.objects
            .filter(
                dish_id=OuterRef("uid"),
                available_date=today,
                is_available=True,
            )
            .values("available_quantity")[:1]
        )

        query = Dish.objects.filter(deleted=False).select_related(
            'attachment',
            'owner',
            'location',
            'location__parent',
            'location__parent__parent',
        ).annotate(
            sold_count=Coalesce(Subquery(sold_count_subquery, output_field=IntegerField()), Value(0)),
            in_stock=Coalesce(Subquery(availability_subquery, output_field=IntegerField()), Value(0)),
        )

        # ===== FILTER NORMAL =====
        if filter:
            query = query.filter(filter.get_filter_expression())

        # ===== ALLERGY LOGIC =====
        allergic_ids = []
        allergy_mode = AllergyModeEnum.WARN

        if user:
            profile = CustomerProfile.objects.filter(user_id=user.id).first()
            if profile:
                allergy_mode = profile.allergy_mode

                allergic_ids = list(
                    AllergicIngredient.objects.filter(
                        user_id=user.id,
                        deleted=False
                    ).values_list("ingredient_id", flat=True)
                )

        # 🔥 HIDE MODE → EXCLUDE DISHES
        if user and allergy_mode == AllergyModeEnum.HIDE and allergic_ids:
            query = query.exclude(
                dish_ingredient_fk_dish__ingredient_id__in=allergic_ids,
                dish_ingredient_fk_dish__deleted=False
            ).distinct()

        if user:
            favorite_subquery = CustomerFavoriteDish.objects.filter(
                user_id=user.id,
                dish_id=OuterRef("uid"),
                deleted=False,
            )
            query = query.annotate(is_favorite=Exists(favorite_subquery))
        else:
            query = query.annotate(
                is_favorite=Value(False, output_field=BooleanField())
            )
      
        # ===== SORT =====
        if sort_by == SortByEnum.PRICE_DESC:
            query = query.order_by("-price")
        elif sort_by == SortByEnum.PRICE_ASC:
            query = query.order_by("price")
        elif sort_by == SortByEnum.SOLD_DESC:
            query = query.order_by("-sold_count")
        elif sort_by == SortByEnum.SOLD_ASC:
            query = query.order_by("sold_count")
        elif sort_by == SortByEnum.RATING_ASC:
            query = query.order_by("avg_rating")
        else:
            query = query.order_by("-avg_rating")

        return query
    
    @staticmethod
    def get_dishes_by_chef(chef_id: str, filter, sort_by=SortByEnum.RATING_DESC, user=None):
        # 1. Tái sử dụng lại toàn bộ QuerySet phức tạp từ get_all_dishes
        # (Lưu ý: Thay 'ClassName' bằng tên class ORM hiện tại của bạn, ví dụ: DishORM)
        base_query = DishORM.get_all_dishes(filter=filter, sort_by=sort_by, user=user)
        
        # 2. Append thêm điều kiện lọc theo Chef (owner)
        # Tùy thuộc vào model của bạn, field này có thể là 'owner_id' hoặc 'owner__id'
        final_query = base_query.filter(owner_id=chef_id)
        
        return final_query

    @staticmethod
    def get_top_dishes(limit: int = 10):
        today = timezone.localdate()
        m = 50.0
        system_avg_rating = (
            Review.objects
            .filter(deleted=False)
            .aggregate(avg_rating=Avg("rating"))
            .get("avg_rating")
            or 0.0
        )

        sold_count_subquery = (
            OrderItem.objects
            .filter(dish_id=OuterRef("uid"), order__status=OrderStatusEnum.COMPLETED)
            .values("dish_id")
            .annotate(total_quantity=Sum("quantity"))
            .values("total_quantity")[:1]
        )

        review_count_subquery = (
            Review.objects
            .filter(dish_id=OuterRef("uid"), deleted=False)
            .values("dish_id")
            .annotate(total_reviews=Count("uid"))
            .values("total_reviews")[:1]
        )
        
        availability_subquery = (
            DishAvailability.objects
            .filter(
                dish_id=OuterRef("uid"),
                available_date=today,
                is_available=True,
            )
            .values("available_quantity")[:1]
        )

        return (
            Dish.objects
            .filter(deleted=False)
            .select_related("attachment", "owner")
            .annotate(
                sold_count=Coalesce(Subquery(sold_count_subquery, output_field=IntegerField()), Value(0)),
                review_count=Coalesce(Subquery(review_count_subquery, output_field=IntegerField()), Value(0)),
                in_stock=Coalesce(Subquery(availability_subquery, output_field=IntegerField()), Value(0)),
            )
            .annotate(
                score=ExpressionWrapper(
                    (F("review_count") / (F("review_count") + Value(m))) * F("avg_rating")
                    + (Value(m) / (F("review_count") + Value(m))) * Value(float(system_avg_rating)),
                    output_field=FloatField(),
                )
            )
            .order_by("-score", "-sold_count", "-review_count", "name")[:limit]
        )
    
    #get dish deleted or not to restore
    @staticmethod
    def get_dish_by_uid_including_deleted(uid: UUID):
        try:
            return Dish.objects.get(uid=uid)
        except Dish.DoesNotExist:
            return None
        
    @staticmethod
    def get_dish_by_uid(uid: UUID):
        try:
            today = timezone.localdate()
            sold_count_subquery = (
                OrderItem.objects
                .filter(dish_id=OuterRef("uid"), order__status=OrderStatusEnum.COMPLETED)
                .values("dish_id")
                .annotate(total_quantity=Sum("quantity"))
                .values("total_quantity")[:1]
            )

            availability_subquery = (
                DishAvailability.objects
                .filter(
                    dish_id=OuterRef("uid"),
                    available_date=today,
                    is_available=True,
                )
                .values("available_quantity")[:1]
            )

            return (
                Dish.objects
                .select_related('attachment', 'owner', 'location', 'location__parent', 'location__parent__parent')
                .annotate(
                    sold_count=Coalesce(Subquery(sold_count_subquery, output_field=IntegerField()), Value(0)),
                    in_stock=Coalesce(Subquery(availability_subquery, output_field=IntegerField()), Value(0)),
                )
                .get(uid=uid, deleted=False)
            )
        except Dish.DoesNotExist:
            return None


    @staticmethod
    def get_dish_by_uids(uids: List[UUID]):
        return Dish.objects.filter(uid__in=uids, deleted=False)

    @staticmethod
    def update_dish(dish: Dish, user: TUser, payload: dict):
        for key, value in payload.items():
            setattr(dish, key, value)
        dish.updater = user
        dish.save()
        return dish

    @staticmethod
    def get_all_ingredients_of_dish_for_customers(dish: Dish):
        return (
            DishIngredient.objects
            .filter(dish=dish, deleted=False)
            .select_related("ingredient")
            .only(
                "uid",
                "custom_name",
                "confidence",
                "weight",
                "energy",
                "protein",
                "lipid",
                "carbohydrate",
                "fiber",
                "natri",
                "cholesterol",
                "ingredient_id",     
                "ingredient__name",
            )
        )
    @staticmethod
    def add_ingredient_to_dish(
        dish: Dish,
        ingredient: Ingredient | None,
        weight: float,
        custom_name: str | None = None,
        approval_status: str = "APPROVED",
        confidence: float | None = None,
        source: str | None = None,
        suggestion=None,
        created_by: TUser | None = None,
        updated_by: TUser | None = None,
        nutrient_values: dict | None = None,
    ):
        nutrient_values = nutrient_values or {}
        data = dict(
            dish=dish,
            ingredient=ingredient,
            custom_name=custom_name,
            source=source,
            suggestion=suggestion,
            created_by=created_by,
            updated_by=updated_by,
            approval_status=approval_status,
            weight=weight,
            **nutrient_values,
        )

        if confidence is not None:
            data["confidence"] = confidence

        return DishIngredient.objects.create(**data)
    
    @staticmethod
    def dish_has_ingredient_suggestion(dish, suggestion):
        return DishIngredient.objects.filter(
            dish=dish,
            suggestion=suggestion,
            deleted=False
        ).exists()
    
    @staticmethod
    def get_one_dish_ingredient_by_suggestion_and_user(suggestion, user):
        return DishIngredient.objects.filter(
            suggestion=suggestion,
            created_by=user,
        ).order_by("-created_at").first()
    
    @staticmethod
    def get_all_ingredients_of_dish_for_chefs(dish: Dish):
        return (
            DishIngredient.objects
            .filter(dish=dish, deleted=False)
            .select_related("ingredient")
            .annotate(
                # 👉 name fallback
                ingredient_name=Coalesce(
                    F("ingredient__name"),
                    F("custom_name"),
                    Value("Unknown Ingredient"),
                    output_field=CharField()
                ),

                # 👉 xác định custom hay không
                is_custom=Case(
                    When(ingredient__isnull=True, then=Value(True)),
                    default=Value(False),
                    output_field=BooleanField()
                )
            )
            .only(
                "uid",  # ✅ THÊM DÒNG NÀY - QUAN TRỌNG!
                "ingredient__uid",
                "ingredient__name",
                "custom_name",
                "weight",
                "energy",
                "protein",
                "lipid",
                "carbohydrate",
                "fiber",
                "natri",
                "cholesterol",
                "confidence",
                "source",
                "approval_status",
            )
            .order_by("-updated_at")
        )
    @staticmethod
    def create_dish_ingredient_from_suggestion(user: TUser, dish: Dish, suggestion: IngredientSuggestion, payload: DishIngredientSuggestionSchema, confidence: float | None = None):
        # tạo ra, với source là suggestion, approval_status là pending
        return DishIngredient.objects.create(
            dish=dish,
            custom_name=payload.custom_name,
            source=IngredientSourceEnum.CHEF_SUGGESTION,
            approval_status=IngredientImportStatusEnum.PENDING,
            suggestion=suggestion,
            created_by=user,
            updated_by=user,
            weight=payload.weight,
            energy=payload.energy,
            protein=payload.protein,
            lipid=payload.lipid,
            carbohydrate=payload.carbohydrate,
            fiber=payload.fiber,
            natri=payload.natri,
            kali=payload.kali,
            vitamin_b_2=payload.vitamin_b_2,
            vitamin_pp=payload.vitamin_pp,
            vitamin_c=payload.vitamin_c,
            calcium=payload.calcium,
            phosphorus=payload.phosphorus,
            fe=payload.fe,
            mg=payload.mg,
            zn=payload.zn,
            confidence=confidence if confidence is not None else 1.0,
        )

    @staticmethod
    def dish_has_ingredient(dish: Dish, ingredient: Ingredient) -> bool:
        return DishIngredient.objects.filter(dish=dish, ingredient=ingredient, deleted=False).exists()

    @staticmethod
    def get_dish_ingredient_by_dish_and_ingredient(dish: Dish, ingredient: Ingredient) -> Optional[DishIngredient]:
        return DishIngredient.objects.filter(dish=dish, ingredient=ingredient, deleted=False).first()

    @staticmethod
    def dish_has_custom_ingredient(dish: Dish, custom_name: str, user: TUser) -> bool:
        return DishIngredient.objects.filter(
            dish=dish,
            ingredient__isnull=True,
            custom_name__iexact=custom_name,
            created_by=user,
            deleted=False,
        ).exists()
    
    #=======DISH INGREDIENT========
    @staticmethod
    def get_dish_ingredient_by_uid_with_select_related(uid: UUID):
        try:
            return DishIngredient.objects.select_related("dish", "ingredient").get(uid=uid, deleted=False)
        except DishIngredient.DoesNotExist:
            return None
        
    @staticmethod
    def get_dish_ingredient_by_uid(uid: UUID):
        try:
            return DishIngredient.objects.get(uid=uid, deleted=False)
        except DishIngredient.DoesNotExist:
            return None 
    
    @staticmethod
    def update_dish_ingredient(
        dish_ingredient: DishIngredient,
        weight: float,
        nutrient_values: dict | None = None,
        ingredient: Ingredient | None = None,
        custom_name: str | None = None,
        approval_status: str | None = None,
        source: str | None = None,
        suggestion=None,
        updated_by: TUser | None = None,
    ):
        nutrient_values = nutrient_values or {}
        dish_ingredient.weight = weight
        if ingredient is not None or custom_name is not None:
            dish_ingredient.ingredient = ingredient
            dish_ingredient.custom_name = custom_name
        if approval_status is not None:
            dish_ingredient.approval_status = approval_status
        if source is not None:
            dish_ingredient.source = source
        dish_ingredient.suggestion = suggestion
        if updated_by is not None:
            dish_ingredient.updated_by = updated_by
        for field, value in nutrient_values.items():
            setattr(dish_ingredient, field, value)
        dish_ingredient.save()
        return dish_ingredient
   
    @staticmethod
    def apply_alias_resolution_to_dish_ingredient(
        *,
        dish_ingredient: DishIngredient,
        ingredient: Ingredient,
        nutrient_values: dict,
        user: TUser,
        confidence: float = 1.0,
        approval_status: str = IngredientImportStatusEnum.APPROVED,
        source: str = IngredientSourceEnum.USDA,
    ):
        dish_ingredient.ingredient = ingredient
        dish_ingredient.custom_name = None

        dish_ingredient.approval_status = approval_status
        dish_ingredient.source = source

        dish_ingredient.updated_by = user

        # 👉 nutrient overwrite
        for field, value in nutrient_values.items():
            setattr(dish_ingredient, field, value)

        # 👉 IMPORTANT: confidence update (fix core issue)
        dish_ingredient.confidence = confidence

        dish_ingredient.save(update_fields=[
            "ingredient",
            "custom_name",
            "approval_status",
            "source",
            "updated_by",
            "confidence",
            *nutrient_values.keys()
        ])

        return dish_ingredient
    @staticmethod
    def soft_delete_dish_ingredient(dish_ingredient: DishIngredient, user: TUser) -> bool:
        dish_ingredient.deleted = True
        dish_ingredient.save()
        return True
    

    @staticmethod
    def soft_delete_dish(user: TUser, dish: Dish) -> bool:
        # if has_related_objects(instance=dish, exclude=["attachment"]):
        #     return False
        dish.deleted = True
        dish.updater = user
        dish.save()
        return True

    @staticmethod
    def delete_dish(dish: Dish) -> bool:
        try:
            dish.delete()
            return True
        except IntegrityError:
            return False

    @staticmethod
    def restore_dish(user: TUser, dish: Dish):
        if not dish.deleted:
            return False
        dish.deleted = False
        dish.updater = user
        dish.save()
        return True

    @staticmethod
    def add_attachment(dish: Dish, attachment: Attachment):
        dish.attachment = attachment
        dish.save()
        return dish


    @staticmethod
    def get_dish_availabilities(uid: UUID):
        dish = (
            Dish.objects
            .filter(uid=uid, deleted=False)
            .prefetch_related(
                Prefetch(
                    'availability_fk_dish',
                    queryset=DishAvailability.objects.filter(
                        available_date__gte=timezone.now().date(),
                        is_available=True,
                        available_quantity__gt=0
                    ).order_by('available_date')
                )
            )
            .first()
        )

        if not dish:
            return None

        return {
            "dish_uid": str(dish.uid),
            "dish_name": dish.name,
            "availabilities": [
                {
                    "available_date": availability.available_date,
                    "available_quantity": availability.available_quantity,
                    "note": availability.note
                }
                for availability in cast(Any, dish).availability_fk_dish.all()
            ]
        }
        
    @staticmethod
    @transaction.atomic
    def create_or_update_availability(dish: Dish, available_date: date, available_quantity: int, note: str | None = None):
        # Tìm bản ghi availability theo dish + ngày
        availability, created = DishAvailability.objects.get_or_create(
            dish=dish,
            available_date=available_date,
            defaults={
                "available_quantity": available_quantity,
                "is_available": True,
                "note": note
            }
        )

        if not created:
            # Nếu đã có thì cập nhật lại
            availability.available_quantity = available_quantity
            availability.is_available = True
            if note is not None:
                availability.note = note
            availability.save()

        return availability
    @staticmethod
    def reduce_quantity(dish, available_date, quantity):
        """
        Trừ số lượng món trong DishAvailability. 
        Nếu record chưa tồn tại thì raise error thay vì tạo mới.
        """
        with transaction.atomic():
            try:
                # khóa bản ghi để tránh race condition
                availability = DishAvailability.objects.select_for_update().get(
                    dish=dish,
                    available_date=available_date
                )
            except DishAvailability.DoesNotExist:
                raise ValueError(f"Dish {dish.name} chưa có sẵn trong ngày {available_date}")

            if availability.available_quantity < quantity:
                raise ValueError(
                    f"Không đủ số lượng món {dish.name} trong ngày {available_date}"
                )

            availability.available_quantity -= quantity
            availability.save()
            return availability
    
    @staticmethod
    def increase_quantity(dish, available_date, quantity):
        """
        Hoàn trả số lượng món trong DishAvailability (khi hủy đơn).
        """
        with transaction.atomic():
            try:
                # Khóa bản ghi để tránh race condition
                availability = DishAvailability.objects.select_for_update().get(
                    dish=dish,
                    available_date=available_date
                )
            except DishAvailability.DoesNotExist:
                # Nếu chưa có record, tạo mới với số lượng được hoàn
                availability = DishAvailability.objects.create(
                    dish=dish,
                    available_date=available_date,
                    available_quantity=quantity
                )
                return availability
            
            availability.available_quantity += quantity
            availability.save()
            return availability
        
    @staticmethod
    def count_ingredients_of_dish(dish: Dish) -> int:
        return DishIngredient.objects.filter(dish=dish, deleted=False).count()
    
    @staticmethod
    def get_dish_ingredient_by_suggestion_uid(suggestion_uid: UUID):
        try:
            return DishIngredient.objects.get(suggestion__uid=suggestion_uid, deleted=False)
        except DishIngredient.DoesNotExist:
            return None
 
    @staticmethod
    def update_dish_ingredients_by_suggestion(
        suggestion: IngredientSuggestion,
        ingredient: Ingredient,
        status: IngredientImportStatusEnum,
        source: IngredientSourceEnum,
        user: TUser,
        confidence: float | None = None,
    ):
        update_data = {
            "ingredient": ingredient,
            "approval_status": status,
            "source": source,
            "updated_by": user,
            "updated_at": timezone.now(),
        }

        # 👉 chỉ update nếu có truyền
        if confidence is not None:
            update_data["confidence"] = confidence

        return DishIngredient.objects.filter(
            suggestion=suggestion,
            deleted=False,
        ).update(**update_data)
    
    @staticmethod
    def get_country_locations():
        return DishLocation.objects.filter(type=DishLocationTypeEnum.COUNTRY).order_by("name")