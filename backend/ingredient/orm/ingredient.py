from difflib import SequenceMatcher
from typing import Any, List, Optional, cast
from uuid import UUID

from django.contrib.postgres.search import TrigramSimilarity
from django.db import IntegrityError
from django.db import connection
from django.db import transaction
from django.utils import timezone
from django.apps import apps

from attachment.models import Attachment
from dish.models import DishIngredient
from dish.schemas.requests import DishIngredientSuggestionSchema
from ingredient.models import AllergicIngredient, FavouriteIngredient, Ingredient, IngredientAlias, IngredientSuggestion
from ingredient.schemas.requests import (
    FilterIngredientSchema,
    IngredientSchema,
    IngredientSuggestionOrderBySchema,
    OrderByIngredientSchema,
)
from utils.enums import IngredientCategoryEnum, IngredientImportStatusEnum, IngredientSourceEnum
from utils.functions.remove_accents import remove_accents
from utils.functions.check_relation import has_related_objects
from utils.types import TUser
from ingredient.constants import DISH_NUTRIENT_FIELDS


class IngredientORM:
    @staticmethod
    def find_suggestion_candidates(suggested_name: str, limit: int = 10, category: Optional[str] = None):
        normalized_query = remove_accents((suggested_name or "")).strip().lower()
        if not normalized_query:
            return []

        candidate_map: dict[UUID, dict] = {}

        def upsert_candidate(
            ingredient: Ingredient,
            score: float,
            match_type: str,
            matched_alias: str | None = None,
        ):
            current = candidate_map.get(ingredient.uid)
            payload = {
                "uid": ingredient.uid,
                "name": ingredient.name,
                "category": ingredient.category,
                "matched_alias": matched_alias,
                "match_type": match_type,
                "score": round(float(score), 4),
            }
            if not current or payload["score"] > current["score"]:
                candidate_map[ingredient.uid] = payload

        # =========================================================
        # 🔥 STAGE 1: EXACT MATCH (HIGHEST PRIORITY)
        # =========================================================

        # 🔥 FIX: giữ score tier rõ ràng (exact luôn > prefix > fuzzy)
        alias_exact_q = IngredientAlias.objects.select_related("ingredient").filter(
            is_active=True,
            alias_no_accent=normalized_query,
            ingredient__deleted=False,
        )
        if category:
            alias_exact_q = alias_exact_q.filter(ingredient__category=category)
        alias_exact = alias_exact_q
        for alias in alias_exact:
            upsert_candidate(alias.ingredient, score=1.0, match_type="alias_exact", matched_alias=alias.alias)

        name_exact_q = Ingredient.objects.filter(
            deleted=False,
            name_no_accent=normalized_query
        )
        if category:
            name_exact_q = name_exact_q.filter(category=category)
        name_exact = name_exact_q
        for ingredient in name_exact:
            upsert_candidate(ingredient, score=0.98, match_type="name_exact")

        # =========================================================
        # 🔥 STAGE 2: PREFIX MATCH
        # =========================================================

        name_prefix_q = Ingredient.objects.filter(
            deleted=False,
            name_no_accent__startswith=normalized_query
        )
        if category:
            name_prefix_q = name_prefix_q.filter(category=category)
        name_prefix = name_prefix_q
        for ingredient in name_prefix:
            upsert_candidate(ingredient, score=0.9, match_type="prefix_name")

        alias_prefix_q = IngredientAlias.objects.select_related("ingredient").filter(
            is_active=True,
            alias_no_accent__startswith=normalized_query,
            ingredient__deleted=False,
        )
        if category:
            alias_prefix_q = alias_prefix_q.filter(ingredient__category=category)
        alias_prefix = alias_prefix_q
        for alias in alias_prefix:
            upsert_candidate(alias.ingredient, score=0.88, match_type="prefix_alias", matched_alias=alias.alias)

        # =========================================================
        # 🔥 STAGE 3: FUZZY (TRIGRAM)
        # =========================================================

        if connection.vendor == "postgresql":
            try:
                trigram_name_q = (
                    Ingredient.objects.filter(deleted=False)
                    .annotate(similarity=TrigramSimilarity("name_no_accent", normalized_query))
                    .filter(similarity__gte=0.2)
                )
                if category:
                    trigram_name_q = trigram_name_q.filter(category=category)
                trigram_name_qs = trigram_name_q.order_by("-similarity")[: max(limit * 2, 20)]
                for ingredient in trigram_name_qs:
                    # 🔥 FIX: normalize score để không vượt prefix
                    score = 0.5 + float(getattr(ingredient, "similarity", 0.0)) * 0.4
                    upsert_candidate(ingredient, score=score, match_type="trigram_name")

                trigram_alias_q = (
                    IngredientAlias.objects.select_related("ingredient")
                    .filter(is_active=True, ingredient__deleted=False)
                    .annotate(similarity=TrigramSimilarity("alias_no_accent", normalized_query))
                    .filter(similarity__gte=0.2)
                )
                if category:
                    trigram_alias_q = trigram_alias_q.filter(ingredient__category=category)
                trigram_alias_qs = trigram_alias_q.order_by("-similarity")[: max(limit * 2, 20)]
                for alias in trigram_alias_qs:
                    score = 0.5 + float(getattr(alias, "similarity", 0.0)) * 0.4
                    upsert_candidate(
                        alias.ingredient,
                        score=score,
                        match_type="trigram_alias",
                        matched_alias=alias.alias,
                    )
            except Exception as e:
                # Fallback to basic search if pg_trgm is not enabled or other DB error
                print(f"PostgreSQL Trigram Search Error (falling back): {e}")
                fallback_q = Ingredient.objects.filter(deleted=False, name_no_accent__icontains=normalized_query)
                if category:
                    fallback_q = fallback_q.filter(category=category)
                for ingredient in fallback_q[:limit]:
                    upsert_candidate(ingredient, score=0.4, match_type="fallback_contains")

        else:
            # fallback
            fallback_q = Ingredient.objects.filter(deleted=False)
            if category:
                fallback_q = fallback_q.filter(category=category)
            for ingredient in fallback_q[:200]:
                score = SequenceMatcher(None, normalized_query, ingredient.name_no_accent).ratio()
                if score >= 0.25:
                    score = 0.5 + score * 0.4
                    upsert_candidate(ingredient, score=score, match_type="fuzzy_fallback")

        # =========================================================
        # 🔥 FINAL SORT
        # =========================================================

        results = sorted(
            candidate_map.values(),
            key=lambda item: (-item["score"], item["name"].lower()),
        )

        # 🔥 FIX: mark best candidate (UX improvement)
        if results:
            results[0]["is_best"] = True

        return results[:limit]
    @staticmethod
    def create_new_ingredient(user: TUser, payload: IngredientSchema):
        name = " ".join(payload.name.strip().lower().split())

        if Ingredient.objects.filter(name__iexact=name, deleted=False).exists():
            raise ValueError("Ingredient name already exists")

        # Lấy dict từ payload và loại bỏ trường 'name' cũ
        ingredient_data = payload.dict()
        ingredient_data['name'] = name  # Ghi đè name đã chuẩn hóa
        ingredient_data['owner'] = user
        ingredient_data['updater'] = user
        
        return Ingredient.objects.create(**ingredient_data)
    @staticmethod
    def get_all_ingredients(
        filter: Optional[FilterIngredientSchema] = None,
        order_by: Optional[OrderByIngredientSchema] = None,
    ):
        query = Ingredient.objects.filter(deleted=False)
        if filter:
            query = query.filter(filter.get_filter_expression())
        if order_by:
            query = query.order_by(order_by.get_order_by_expression())
        return query

    @staticmethod
    def get_ingredient_by_uid(uid: UUID):
        try:
            return Ingredient.objects.get(uid=uid, deleted=False)
        except Ingredient.DoesNotExist:
            return None

    @staticmethod
    def find_one_pending_suggestin_by_uid(uid: UUID):
        try:
            return IngredientSuggestion.objects.get(uid=uid, status=IngredientImportStatusEnum.PENDING)
        except IngredientSuggestion.DoesNotExist:
            return None
        
    @staticmethod
    def find_user_pending_suggestions(user, query, limit=10, category=None):
        normalized_query = remove_accents((query or "")).strip().lower()

        qs = IngredientSuggestion.objects.filter(
            created_by=user,
            deleted=False,
            status=IngredientImportStatusEnum.PENDING,
        )

        if category:
            qs = qs.filter(suggested_category=category)

        if normalized_query:
            qs = qs.filter(
                suggested_name_no_accent__icontains=normalized_query
            )

        return qs.order_by("-created_at")[:limit]
    
    @staticmethod
    def get_dish_ingredients_by_suggestion(suggestion):
        return DishIngredient.objects.filter(
            suggestion=suggestion,
            deleted=False,
        )

    @staticmethod
    def get_ingredient_by_uids(uids: List[UUID]):
        return Ingredient.objects.filter(uid__in=uids, deleted=False)

    @staticmethod
    def search_ingredients(
        query: str,
        filter: Optional[FilterIngredientSchema] = None,
        order_by: Optional[OrderByIngredientSchema] = None,
        limit: int = 10,
    ):
        raw_query = (query or "").strip().lower()
        normalized_query = remove_accents(raw_query).strip().lower()
        if not normalized_query:
            return []

        candidates = Ingredient.objects.filter(deleted=False)
        if filter:
            candidates = candidates.filter(filter.get_filter_expression())
        if order_by:
            candidates = candidates.order_by(order_by.get_order_by_expression())
        else:
            candidates = candidates.order_by("name")
        candidates = candidates.prefetch_related("aliases")

        def score_label(label: str) -> tuple[float, str | None]:
            label_raw = (label or "").strip().lower()
            label_norm = remove_accents(label_raw).strip().lower()

            if label_raw == raw_query:
                return 1.0, None
            if label_norm == normalized_query:
                return 0.995, None

            if label_raw.startswith(raw_query):
                return 0.99, None

            if label_norm.startswith(normalized_query):
                # Accent-insensitive prefix, but weaker than raw prefix.
                # Still keep a small boost so "cá basa" outranks broad fuzzy matches.
                return 0.93, None

            if normalized_query in label_norm:
                return 0.9, None

            return SequenceMatcher(None, normalized_query, label_norm).ratio() * 0.8, None

        results: list[dict] = []
        for ingredient in candidates:
            best_score = 0.0
            matched_alias = None

            possible_labels = [(ingredient.name, None)]
            for alias in cast(Any, ingredient).aliases.all():
                if alias.is_active:
                    possible_labels.append((alias.alias, alias.alias))

            for label, alias_value in possible_labels:
                score, _ = score_label(label)

                if score > best_score:
                    best_score = score
                    matched_alias = alias_value

            if best_score >= 0.25:
                results.append(
                    {
                        "uid": ingredient.uid,
                        "name": ingredient.name,
                        "category": ingredient.category,
                        "matched_alias": matched_alias,
                        "score": round(best_score, 4),
                    }
                )

        results.sort(key=lambda item: (-item["score"], item["name"].lower()))
        if limit and limit > 0:
            return results[:limit]
        return results

    @staticmethod
    def autocomplete_ingredients(query: str, limit: int = 10):
        raw_query = (query or "").strip().lower()
        normalized_query = remove_accents(raw_query).strip().lower()
        if not normalized_query:
            return []

        def score_label(label: str) -> float:
            label_raw = (label or "").strip().lower()
            label_norm = remove_accents(label_raw).strip().lower()

            if label_raw == raw_query:
                return 1.0
            if label_norm == normalized_query:
                return 0.995
            if label_raw.startswith(raw_query):
                return 0.99
            if label_norm.startswith(normalized_query):
                return 0.93
            if normalized_query in label_norm:
                return 0.9
            return SequenceMatcher(None, normalized_query, label_norm).ratio() * 0.8

        results: list[dict] = []
        seen: set[UUID] = set()

        ingredients = Ingredient.objects.filter(deleted=False).prefetch_related("aliases")
        for ingredient in ingredients:
            best_score = 0.0

            for label in [ingredient.name, *[alias.alias for alias in cast(Any, ingredient).aliases.all() if alias.is_active]]:
                score = score_label(label)
                if score > best_score:
                    best_score = score

            if best_score < 0.25:
                continue

            seen.add(ingredient.uid)
            results.append(
                {
                    "uid": ingredient.uid,
                    "name": ingredient.name,
                    "category": ingredient.category,
                    "score": round(best_score, 4),
                }
            )

        results.sort(key=lambda item: (-item["score"], item["name"].lower()))
        return [
            {
                "uid": item["uid"],
                "name": item["name"],
                "category": item["category"],
            }
            for item in results[:limit]
        ]
        
    @staticmethod
    def create_ingredient_alias(ingredient: Ingredient, alias: str, user: TUser | None = None):
        alias_instance, _ = IngredientAlias.objects.update_or_create(
            alias_no_accent=remove_accents(alias),
            defaults={
                "ingredient": ingredient,
                "alias": alias,
                "created_by": user,
                "is_active": True,
            },
        )
        return alias_instance

    @staticmethod
    def list_ingredient_aliases(search: str | None = None):
        query = IngredientAlias.objects.select_related("ingredient").order_by("alias")
        if search:
            normalized = remove_accents(search).strip().lower()
            query = query.filter(alias_no_accent__icontains=normalized)
        return query

    @staticmethod
    def create_ingredient_suggestion(
        user,
        custom_name: str,
        suggested_category: IngredientCategoryEnum,
        attachment: Attachment | None = None,
    ):
        name = custom_name.strip()
        normalized_name = remove_accents(name).strip().lower()

        return IngredientSuggestion.objects.create(
            suggested_name=name,
            suggested_name_no_accent=normalized_name,
            suggested_category=suggested_category,
            created_by=user,
            attachment=attachment,
            status=IngredientImportStatusEnum.PENDING,
        )

    @staticmethod
    def list_ingredient_suggestions(
        status: str | None = None,
        search: str | None = None,
        category: IngredientCategoryEnum | None = None,
        created_by_id: int | None = None,
        order_by: IngredientSuggestionOrderBySchema | None = None,
    ):
        query = IngredientSuggestion.objects.select_related(
            "created_by",
            "verified_by",
            "ingredient",
            "resolved_alias",
        ).filter(deleted=False)
        if status:
            query = query.filter(status=status)
        if search:
            normalized = remove_accents(search).strip().lower()
            if normalized:
                query = query.filter(suggested_name_no_accent__icontains=normalized)
        if category:
            query = query.filter(suggested_category=category)
        if created_by_id is not None:
            query = query.filter(created_by_id=created_by_id)
        if order_by:
            query = query.order_by(order_by.get_order_by_expression())
        else:
            query = query.order_by("-created_at")
        return query

    @staticmethod
    def get_ingredient_suggestion_by_uid(uid: UUID):
        try:
            return IngredientSuggestion.objects.select_related(
                "created_by",
                "verified_by",
                "ingredient",
                "resolved_alias",
            ).get(uid=uid)
        except IngredientSuggestion.DoesNotExist:
            return None

    @staticmethod
    def get_ingredient_suggestion_by_uid_and_owner(uid: UUID, user: TUser):
        try:
            return IngredientSuggestion.objects.get(uid=uid, created_by=user)
        except IngredientSuggestion.DoesNotExist:
            return None
        
    @staticmethod
    def soft_delete_ingredient_suggestion(suggestion: IngredientSuggestion):
        suggestion.deleted = True
        suggestion.save(update_fields=["deleted"])
        return True
    
    @staticmethod
    @transaction.atomic
    def approve_ingredient_suggestion(
        suggestion: IngredientSuggestion,
        user: TUser,
        ingredient_uid: UUID | None = None,
        suggested_category: str | None = None,
        resolution_note: str | None = None,
    ):
        if ingredient_uid is not None:
            ingredient = Ingredient.objects.filter(uid=ingredient_uid, deleted=False).first()
            if not ingredient:
                return None
        else:
            category = suggested_category or suggestion.suggested_category
            if not category:
                return None
            ingredient = Ingredient.objects.filter(
                name_no_accent=suggestion.suggested_name_no_accent,
                deleted=False,
            ).first()

            if ingredient is None:
                ingredient = Ingredient.objects.create(
                    name=suggestion.suggested_name,
                    category=category,
                    owner=user,
                    updater=user,
                )

        alias = IngredientORM.create_ingredient_alias(
            ingredient=ingredient,
            alias=suggestion.suggested_name,
            user=user,
        )

        suggestion.ingredient = ingredient
        suggestion.resolved_alias = alias
        suggestion.status = IngredientImportStatusEnum.APPROVED
        suggestion.verified_by = user
        suggestion.verified_at = timezone.now()
        suggestion.rejection_reason = None
        suggestion.resolution_note = resolution_note
        suggestion.save(
            update_fields=[
                "ingredient",
                "resolved_alias",
                "status",
                "verified_by",
                "verified_at",
                "rejection_reason",
                "resolution_note",
                "updated_at",
            ]
        )

        dish_ingredient_model = apps.get_model("dish", "DishIngredient")
        dish_ingredient_model.objects.filter(
            suggestion=suggestion,
            deleted=False,
        ).update(
            ingredient=ingredient,
            approval_status=IngredientImportStatusEnum.APPROVED,
            updated_by=user,
            updated_at=timezone.now(),
        )
        return suggestion

    @staticmethod
    def create_new_ingredient_from_dishingredient(user: TUser, category: IngredientCategoryEnum, dish_ingredient: DishIngredient, attachment: Attachment | None = None):
        #tính nutrion scale theo weight=100, sau này có thể update lại nếu có thông tin chính xác hơn
        def scale_to_100g(value, weight):
            if value is None or not weight or weight <= 0:
                return None
            return value * (100 / weight)
        
        nutrition_data = {}

        for field in DISH_NUTRIENT_FIELDS:
            raw_value = getattr(dish_ingredient, field, None)
            nutrition_data[field] = scale_to_100g(raw_value, dish_ingredient.weight)

        ingredient = Ingredient.objects.create(
            name=dish_ingredient.custom_name,
            category=category,
            weight=100,
            owner=user,
            updater=user,
            attachment=attachment,
            **nutrition_data
        )
        return ingredient


    @staticmethod
    def approve_suggestion_as_new_ingredient(
        suggestion: IngredientSuggestion,
        user: TUser,
        ingredient: Ingredient,
        resolution_note: str | None = None,
    ):

        suggestion.ingredient = ingredient
        suggestion.status = IngredientImportStatusEnum.APPROVED
        suggestion.verified_by = user
        suggestion.verified_at = timezone.now()
        suggestion.resolution_note = resolution_note
        suggestion.save(
            update_fields=[
                "ingredient",
                "status",
                "verified_by",
                "verified_at",
                "resolution_note"
            ]
        )
        return suggestion

    @staticmethod
    @transaction.atomic
    def approve_suggestion_as_alias(
        suggestion: IngredientSuggestion,
        user: TUser,
        ingredient: Ingredient,
        resolution_note: str | None = None,
    ):

        alias = IngredientORM.create_ingredient_alias(
            ingredient=ingredient,
            alias=suggestion.suggested_name,
            user=user,
        )

        suggestion.ingredient = ingredient
        suggestion.resolved_alias = alias
        suggestion.status = IngredientImportStatusEnum.APPROVED
        suggestion.verified_by = user
        suggestion.verified_at = timezone.now()
        suggestion.rejection_reason = None
        suggestion.resolution_note = resolution_note
        suggestion.save(
            update_fields=[
                "ingredient",
                "resolved_alias",
                "status",
                "verified_by",
                "verified_at",
                "rejection_reason",
                "resolution_note",
            ]
        )
        return suggestion

    @staticmethod
    def reject_ingredient_suggestion(
        suggestion: IngredientSuggestion,
        user: TUser,
        rejection_reason: str,
    ):
        suggestion.status = IngredientImportStatusEnum.REJECTED
        suggestion.verified_by = user
        suggestion.verified_at = timezone.now()
        suggestion.rejection_reason = rejection_reason
        suggestion.resolution_note = rejection_reason
        suggestion.save(
            update_fields=[
                "status",
                "verified_by",
                "verified_at",
                "rejection_reason",
                "resolution_note",
            ]
        )

        return suggestion

    @staticmethod
    def update_ingredient(ingredient: Ingredient, user: TUser, payload: IngredientSchema):
        for key, value in payload.dict().items():
            setattr(ingredient, key, value)
        ingredient.updater = user
        ingredient.save()
        return ingredient

    @staticmethod
    def soft_delete_ingredient(user: TUser, ingredient: Ingredient) -> bool:
        if has_related_objects(instance=ingredient, exclude=["attachment"]):
            return False
        ingredient.deleted = True
        ingredient.updater = user
        ingredient.save()
        return True

    @staticmethod
    def delete_ingredient(ingredient: Ingredient) -> bool:
        try:
            ingredient.delete()
            return True
        except IntegrityError:
            return False

    @staticmethod
    def restore_ingredient(user: TUser, ingredient: Ingredient):
        if not ingredient.deleted:
            return False
        ingredient.deleted = False
        ingredient.updater = user
        ingredient.save()
        return True

    @staticmethod
    def add_attachment(ingredient: Ingredient, attachment: Attachment):
        ingredient.attachment = attachment
        ingredient.save()
        return ingredient

    @staticmethod
    def add_favourite_ingredient(user: TUser, ingredient: Ingredient):
        favourite, _ = FavouriteIngredient.objects.update_or_create(
            user=user,
            ingredient=ingredient,
            defaults={"deleted": False},
        )
        return favourite

    @staticmethod
    def remove_favourite_ingredient(user: TUser, ingredient: Ingredient) -> bool:
        # không cho hard delete để giữ lịch sử yêu thích, chỉ soft delete bằng cách set một trường deleted=False sẽ hợp lý hơn, nhưng tạm thời cứ để vậy đã
        obj = FavouriteIngredient.objects.get(user=user, ingredient=ingredient)
        obj.deleted = True
        obj.save(update_fields=["deleted"])
        return True

    @staticmethod
    def list_favourite_ingredients(user: TUser):
        return Ingredient.objects.filter(
            favourite_ingredient_fk_ingredient__user=user,
            favourite_ingredient_fk_ingredient__deleted=False,
            deleted=False,
        ).order_by("name")

    @staticmethod
    def add_allergic_ingredient(user: TUser, ingredient: Ingredient):
        allergic, _ = AllergicIngredient.objects.update_or_create(
            user=user,
            ingredient=ingredient,
            defaults={"deleted": False},
        )
        return allergic
    
    @staticmethod
    def remove_allergic_ingredient(user: TUser, ingredient: Ingredient) -> bool:
        # không cho hard delete để giữ lịch sử dị ứng, chỉ soft delete bằng cách set một trường deleted=False sẽ hợp lý hơn, nhưng tạm thời cứ để vậy đã
        obj = AllergicIngredient.objects.get(user=user, ingredient=ingredient)
        obj.deleted = True
        obj.save(update_fields=["deleted"])
        return True

    @staticmethod
    def list_allergic_ingredients(user: TUser):
        return Ingredient.objects.filter(
            allergic_ingredient_fk_ingredient__user=user,
            allergic_ingredient_fk_ingredient__deleted=False,
            deleted=False,
        ).order_by("name")
