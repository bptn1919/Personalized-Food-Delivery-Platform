import re
import math
from uuid import UUID
from django.db.models import Prefetch
from exceptions.attachments import AttachmentNotFound
from utils.enums import IngredientImportStatusEnum, IngredientSourceEnum, AllergyModeEnum, SortByEnum
from dish.services.validation import validate_ingredient_weight
from dish.models import Dish, DishLocation, DishIngredient
from ninja.errors import ValidationError
import math
from attachment.services import AttachmentService
from ingredient.services import IngredientService, IngredientSuggestionService
from exceptions.dishes import (
    DishIngredientSuggestionAlreadyExists,
    DishNotFoundException,
    DishIsNotDeleted,
    DishIsReferenced,
    DishIngredientAlreadyExists,
    DishIngredientNotFoundException,
    DishPermissionDenied,
    DishLocationNotFoundException,
    DishLocationHasChildrenException,
)
from exceptions.ingredient import IngredientSuggestionNotFound, NutritionValidationException
from dish.orm.dish import DishORM
from ingredient.orm.ingredient import IngredientORM
from ingredient.models import AllergicIngredient
from profile.models import CustomerFavoriteDish, CustomerProfile
from exceptions.ingredient import IngredientDoesNotExist
from dish.schemas.requests import (
    DishIngredientCreateBySuggestionSchema,
    FilterDishSchema,
    DishIngredientCreateSchema,
    DishIngredientSchema,
    DishAvailabilitySchema,
    DishWithAttachmentSchema,
    DishUpdateSchema,
    DishLocationCreateSchema,
    DishLocationUpdateSchema,
    DishIngredientSuggestionSchema,
)
from utils.types import TUser
from dish.schemas.responses import DishAvailabilityListResponse
from dish.models import DishLocation
from ingredient.models import IngredientSuggestion
from typing import Any, Optional, cast
from utils.functions.remove_accents import remove_accents
from ingredient.constants import (
    HIGH_FAT_KEYWORDS,
    HIGH_PROTEIN_KEYWORDS,
    HIGH_SUGAR_KEYWORDS,
    DISH_NUTRIENT_FIELDS
)
import math

class IngredientSuggestionHelper:

    # =========================================================
    # 🔧 INTERNAL MATCH
    # =========================================================

    @staticmethod
    def _match_keywords(text: str, keywords: dict[str, list[str]]) -> dict[str, bool]:
        def has_match(word_list):
            return any(
                re.search(rf"\b{re.escape(k)}\b", text)
                for k in word_list
            )

        return {
            "strong": has_match(keywords["strong"]),
            "weak": has_match(keywords["weak"]),
        }

    # =========================================================
    # 🚀 MAIN FUNCTION
    # =========================================================

    @staticmethod
    def infer_tags(name: str) -> dict[str, bool]:
        text = (name or "").strip().lower()

        fat = IngredientSuggestionHelper._match_keywords(
            text, HIGH_FAT_KEYWORDS
        )
        sugar = IngredientSuggestionHelper._match_keywords(
            text, HIGH_SUGAR_KEYWORDS
        )
        protein = IngredientSuggestionHelper._match_keywords(
            text, HIGH_PROTEIN_KEYWORDS
        )

        return {
            "high_fat": fat["strong"] or (fat["weak"] and not fat["strong"]),
            "high_sugar": sugar["strong"] or (sugar["weak"] and not sugar["strong"]),
            "high_protein": protein["strong"] or (protein["weak"] and not protein["strong"]),
        }
    
class DishService:
    # ===== CONFIG =====
    LOWER_BOUND = 0.5
    UPPER_BOUND = 2.0

    HARD_LOWER_BOUND = 0.3
    HARD_UPPER_BOUND = 3.0

    ENERGY_MACRO_TOLERANCE = 0.15

    RATIO_CONFIDENCE_PENALTY = 0.3
    MACRO_CONFIDENCE_PENALTY = 0.3
    INGREDIENT_COUNT_CONFIDENCE_PENALTY = 0.2
    SEMANTIC_CONFIDENCE_PENALTY = 0.1
    ENERGY_CONFIDENCE_PENALTY = 0.15

    PENDING_CUSTOM_INGREDIENT_PENALTY = 0.25
    REJECTED_CUSTOM_INGREDIENT_PENALTY = 0.45
    CHEF_SUGGESTION_SOURCE_PENALTY = 0.1
    ZERO_OVERRIDE_TOLERANCE = 0.5
    
    def __init__(self):
        self.orm = DishORM()
        self.ingredient_orm = IngredientORM()
        self.attachment_service = AttachmentService()
        self.ingredient_service = IngredientService()
        self.ingredient_suggestion_service = IngredientSuggestionService()
        self.CUSTOMER_ROUND_CONFIG = {
        "weight": 1,
        "energy": 0,
        "protein": 1,
        "lipid": 1,
        "carbohydrate": 1,
        "fiber": 1,
        "natri": 1,
        "cholesterol": 0,
    }
        self.CHEF_ROUND_CONFIG = {
            "weight": 2,
            "energy": 2,
            "protein": 3,
            "lipid": 3,
            "carbohydrate": 3,
            "fiber": 3,
            "natri": 3,
            "kali": 3,
            "cholesterol": 2,

            # micronutrients (rất nhỏ → cần precision cao)
            "retinol": 4,
            "caroten": 4,
            "vitamin_b_1": 4,
            "vitamin_b_2": 4,
            "vitamin_pp": 4,
            "vitamin_c": 4,
            "calcium": 3,
            "phosphorus": 3,
            "fe": 3,
            "mg": 3,
            "zn": 3,

            # confidence giữ thấp precision
            "confidence": 4,
        }


    def _ratio_score(self, actual: float, expected: float) -> float:
        if expected <= 0 or actual is None:
            return 1.0

        ratio = max(actual, 1e-6) / max(expected, 1e-6)
        deviation = abs(math.log(ratio))

        return math.exp(-1.5 * deviation)


    def _ratio_severity(self, actual: float, expected: float) -> float:
        """
        0.0 = OK
        1.0 = cực sai
        """

        # ======================
        # CASE 1: expected = 0
        # ======================
        if expected is None or expected == 0:
            if actual <= self.ZERO_OVERRIDE_TOLERANCE:
                return 0.0

            # LOG SCALE severity (KHÔNG tuyến tính)
            return min(1.0, math.log10(actual + 1) / 4)

        # ======================
        # CASE 2: normal
        # ======================
        ratio = actual / max(expected, 1e-6)
        deviation = abs(math.log(max(ratio, 1e-6)))

        # smooth nonlinear severity
        return min(1.0, deviation / 2.5)
    
    @staticmethod
    def _scaled_value(
        base_value: Optional[float],
        reference_weight: Optional[float],
        weight: float,
    ) -> Optional[float]:
        if base_value is None:
            return None
        reference = reference_weight if reference_weight and reference_weight > 0 else 100
        return base_value * (weight / reference)
    # =========================================================
    # 1️⃣ COMPUTE (PURE)
    # =========================================================

    def _compute_nutrition(self, payload, ingredient):
        values = {}

        for field in DISH_NUTRIENT_FIELDS:
            base = getattr(ingredient, field, None)

            expected = self._scaled_value(
                base_value=base,
                reference_weight=getattr(ingredient, "weight", None),
                weight=payload.weight,
            )

            override = getattr(payload, field, None)

            values[field] = override if override is not None else expected
          
        return values

    # =========================================================
    # 2️⃣ ANALYZE (WARNING + FLAGS)
    # =========================================================
    def _analyze_nutrition_no_ingredient(self, payload, values):
        warnings = []

        severity = {
            "macro": 0.0,
            "energy": 0.0,
            "outlier": 0.0,
            "semantic": 0.0,
            "completeness": 0.0,
        }

        protein = values.get("protein") or 0
        lipid = values.get("lipid") or 0
        carb = values.get("carbohydrate") or 0
        weight = max(payload.weight or 1.0, 1.0)

        # ======================
        # MACRO (UPDATED)
        # ======================
        severity["macro"] = self._compute_macro_severity(
            protein, lipid, carb, weight
        )

        if severity["macro"] > 0.35:
            warnings.append({
                "type": "macro",
                "severity": severity["macro"],
                "message": "Tổng macro lệch so với trọng lượng",
            })

        # ======================
        # ENERGY (UPDATED)
        # ======================
        energy = values.get("energy") or 0
        severity["energy"] = self._compute_energy_severity(
            energy, protein, lipid, carb
        )

        if severity["energy"] > 0.35:
            warnings.append({
                "type": "energy",
                "severity": severity["energy"],
                "message": "Năng lượng không khớp macro",
            })

        # ======================
        # OUTLIER (FIBER FIX YOUR BUG)
        # ======================
        severity["outlier"], outlier_fields = self._compute_outlier_severity(values, payload.weight)
        if severity["outlier"] > 0:
            warnings.append({
                "type": "outlier",
                "severity": severity["outlier"],
                "fields": outlier_fields,
                "message": "Dữ liệu dinh dưỡng bất thường",
            })
        # ======================
        # SEMANTIC LIGHT
        # ======================
        if lipid > weight * 0.8:
            severity["semantic"] = 0.7
            warnings.append({
                "type": "semantic",
                "severity": 0.7,
                "message": "Chất béo quá cao so với khối lượng",
            })

        return warnings, severity
    
    def _analyze_nutrition_ratio(self, payload, ingredient, values):
        warnings = []

        severity = {
            "ratio": 0.0,
            "macro": 0.0,
            "energy": 0.0,
        }

        protein = values.get("protein") or 0
        lipid = values.get("lipid") or 0
        carb = values.get("carbohydrate") or 0

        # ======================
        # RATIO CHECK
        # ======================
        for field in DISH_NUTRIENT_FIELDS:
            override = getattr(payload, field, None)
            base = getattr(ingredient, field, None)

            expected = self._scaled_value(
                base_value=base,
                reference_weight=getattr(ingredient, "weight", None),
                weight=payload.weight,
            )

            actual = override if override is not None else expected

            if expected is None:
                continue

            # ======================
            # CASE expected = 0 (FIXED)
            # ======================
            if expected == 0:
                if actual > self.ZERO_OVERRIDE_TOLERANCE:
                    warnings.append({
                        "type": "ratio_zero",
                        "field": field,
                        "severity": 1.0,
                        "message": f"{field} sai nghiêm trọng (USDA=0 nhưng nhập {actual})",
                    })
                continue

            # ======================
            # NORMAL CASE
            # ======================
            ratio = actual / max(expected, 1e-6)

            if ratio < self.HARD_LOWER_BOUND or ratio > self.HARD_UPPER_BOUND:
                warnings.append({
                    "type": "ratio_hard",
                    "field": field,
                    "severity": 1.0,
                    "message": f"{field} sai nghiêm trọng ({ratio:.2f}x)",
                })

            severity["ratio"] = max(
                severity["ratio"],
                self._ratio_severity(actual, expected)
            )

            if severity["ratio"] > 0.4:
                warnings.append({
                    "type": "ratio",
                    "field": field,
                    "severity": severity["ratio"],
                    "message": f"{field} lệch nhẹ",
                })

        # ======================
        # MACRO (UNIFIED)
        # ======================
        severity["macro"] = self._compute_macro_severity(
            protein, lipid, carb, payload.weight
        )

        if severity["macro"] > 0.4:
            warnings.append({
                "type": "macro",
                "severity": severity["macro"],
                "message": "Macro không phù hợp",
            })

        # ======================
        # ENERGY (UNIFIED)
        # ======================
        energy = values.get("energy") or 0
        severity["energy"] = self._compute_energy_severity(
            energy, protein, lipid, carb
        )

        if severity["energy"] > 0.4:
            warnings.append({
                "type": "energy",
                "severity": severity["energy"],
                "message": "Energy không khớp macro",
            })

        return warnings, severity
    # =========================================================
    # 3️⃣ CONFIDENCE (ONLY FLAGS)
    # =========================================================

    def _compute_confidence(
        self,
        payload,
        ingredient,
        values,
        severity,
        approval_status,
        source,
    ):
        similarity = self._compute_similarity_to_usda_entry(
            payload=payload,
            ingredient=ingredient,
            values=values,
        )

        completeness = self._compute_completeness_score(values=values)

        quality = self._compute_data_quality_score(
            severity=severity,
            approval_status=approval_status,
            source=source,
        )

        confidence = similarity * completeness * quality

        return round(max(0.0, min(confidence, 1.0)), 3)
    
    def _compute_similarity_to_usda_entry(self, *, payload, ingredient, values) -> float:
        # For custom ingredient suggestion (no mapped USDA entry yet), keep conservative default.
        if ingredient is None:
            return 0.65

        scores: list[float] = []
        for field in DISH_NUTRIENT_FIELDS:
            expected = self._scaled_value(
                base_value=getattr(ingredient, field, None),
                reference_weight=getattr(ingredient, "weight", None),
                weight=payload.weight,
            )
            actual = values.get(field)

            if expected is None or actual is None or expected <= 0:
                continue

            ratio = max(float(actual), 1e-6) / max(float(expected), 1e-6)
            # 1.0 when ratio=1, smoothly decreases when mismatch increases.
            score = math.exp(-abs(math.log(ratio)))
            scores.append(max(0.0, min(1.0, score)))

        if not scores:
            return 0.75
        return max(0.35, min(sum(scores) / len(scores), 1.0))

    def _compute_completeness_score(self, *, values) -> float:
        core_fields = ["energy", "protein", "lipid", "carbohydrate"]
        total_fields = DISH_NUTRIENT_FIELDS

        # ======================
        # CORE COMPLETENESS (70%)
        # ======================
        core_available = sum(1 for f in core_fields if values.get(f) is not None)
        core_ratio = core_available / len(core_fields)

        # ======================
        # FULL COMPLETENESS (30%)
        # ======================
        total_available = sum(1 for f in total_fields if values.get(f) is not None)
        full_ratio = total_available / len(total_fields)

        # ======================
        # COMBINE
        # ======================
        score = 0.7 * core_ratio + 0.3 * full_ratio

        return max(0.2, min(1.0, score))

    def _compute_data_quality_score(self, *, severity, approval_status, source):
        quality = 1.0
        # CORE penalties
        quality *= (1.0 - 0.7 * severity.get("ratio", 0))
        quality *= (1.0 - 0.5 * severity.get("macro", 0))
        quality *= (1.0 - 0.4 * severity.get("energy", 0))
        quality *= (1.0 - 0.3 * severity.get("outlier", 0))
        quality *= (1.0 - 0.2 * severity.get("semantic", 0))  # 🔥 thêm cái này

        # SOURCE penalty
        if source == IngredientSourceEnum.CHEF_SUGGESTION:
            quality *= 0.9

        # APPROVAL penalty
        if approval_status == IngredientImportStatusEnum.PENDING:
            quality *= 0.85
        elif approval_status == IngredientImportStatusEnum.REJECTED:
            quality *= 0.5

        return max(0.05, min(quality, 1.0))

# hàm process ingredient sẽ được gọi trong cả 2 API add_ingredient_to_dish và suggest_ingredient_for_dish, vì dù có phải suggest hay không thì khi thêm ingredient vào dish cũng đều cần compute, analyze và compute confidence để trả về cho frontend hiển thị cảnh báo nếu có
    def _process_ingredient_pipeline(
        self,
        payload,
        ingredient,
        approval_status=None,
        source=None,
    ):
        # Layer 1: weight sanity check trước khi tính nutrition
        ingredient_category = ingredient.category if ingredient else None
        ingredient_name = (
            ingredient.name
            if ingredient
            else getattr(payload, "custom_name", "") or ""
        )
        validate_ingredient_weight(
            weight=float(payload.weight),
            ingredient_category=ingredient_category,
            ingredient_name=ingredient_name,
        )

        # ======================
        # 1. COMPUTE
        # ======================
        if ingredient:
            values = self._compute_nutrition(payload, ingredient)
        else:
            values = {
                field: getattr(payload, field, None)
                for field in DISH_NUTRIENT_FIELDS
            }

        # ======================
        # 2. ANALYZE
        # ======================
        if ingredient is not None:
            warnings, severity = self._analyze_nutrition_ratio(
                payload=payload, ingredient=ingredient, values=values
            )
        else:
            warnings, severity = self._analyze_nutrition_no_ingredient(
                payload=payload, values=values
            )

            warnings.append({
                "type": "info",
                "field": "ingredient",
                "severity": 0.3,
                "message": "Nguyên liệu chưa có trong USDA (AI estimate)",
            })

        # ======================
        # 3. CONFIDENCE
        # ======================
        confidence = self._compute_confidence(
            payload=payload,
            ingredient=ingredient,
            values=values,
            severity=severity,
            approval_status=approval_status,
            source=source,
        )

        return values, warnings, confidence

    @staticmethod
    def _get_custom_name(payload: DishIngredientSchema | DishIngredientCreateSchema) -> str:
        payload_any = cast(Any, payload)
        return (payload_any.custom_name or "").strip()
    
    def _compute_macro_severity(self, protein, lipid, carb, weight):
        if weight <= 0:
            return 0.0

        total = protein + lipid + carb
        density = (total / weight) * 100  # per 100g

        # HARD FAIL -> return max severity instead of crashing
        if density > 100 or density < 1:
            return 1.0

        # SAFE ZONE
        if 5 <= density <= 30:
            return 0.0

        # smooth penalty (logistic-like)
        if density < 5:
            x = (5 - density) / 5
        else:
            x = (density - 30) / 30
        return min(1.0, x ** 1.5)
    
    def _compute_energy_severity(self, energy, protein, lipid, carb):
        expected = 4 * protein + 9 * lipid + 4 * carb

        if expected <= 0:
            return 0.0

        ratio = energy / expected

        # HARD FAIL -> return max severity instead of crashing
        if ratio < 0.4 or ratio > 1.8:
            return 1.0

        # SAFE ZONE
        if 0.8 <= ratio <= 1.2:
            return 0.0

        # smooth penalty (log scale)
        deviation = abs(math.log(ratio))

        return min(1.0, deviation)
    
    def _compute_outlier_severity(self, values, weight):
        if weight <= 0:
            return 0.0, []

        factor = 100 / weight

        LIMITS = {
            "energy": 900,          # kcal

            "protein": 60,          # g
            "lipid": 100,           # g
            "carbohydrate": 120,    # g
            "fiber": 50,            # g

            "natri": 3000,          # mg
            "kali": 5000,           # mg
            "cholesterol": 500,     # mg

            "retinol": 3000,        # µg
            "caroten": 15000,       # µg

            "vitamin_b_1": 10,      # mg
            "vitamin_b_2": 10,      # mg
            "vitamin_pp": 100,      # mg
            "vitamin_c": 1000,      # mg

            "calcium": 3000,        # mg
            "phosphorus": 2000,     # mg
            "fe": 30,               # mg
            "mg": 1000,             # mg
            "zn": 40,               # mg
        }

        SAFE_RATIO = 0.8
        HARD_RATIO = 3.0

        worst = 0.0
        fields = []

        for field in DISH_NUTRIENT_FIELDS:
            v = values.get(field)
            if v is None:
                continue

            per100 = v * factor
            limit = LIMITS.get(field)
            if not limit:
                continue

            # HARD FAIL
            if per100 > limit * HARD_RATIO:
                raise NutritionValidationException(
                    f"{field} vượt ngưỡng vật lý",
                    field
                )

            safe = limit * SAFE_RATIO

            # SAFE ZONE
            if per100 <= safe:
                continue

            # normalize [0 → 1]
            x = (per100 - safe) / (limit * HARD_RATIO - safe)

            score = x ** 1.5 * (2 - x)

            worst = max(worst, score)
            fields.append(field)

        return worst, fields

    def create_dish(self, user: TUser, payload: DishWithAttachmentSchema):
        """Tạo dish với attachment đã upload và completed"""
        attachment = None
        if payload.attachment_uid is not None:
            attachment = self.attachment_service.handle_attachment(uid=payload.attachment_uid)
        # Create dish with attachment
        dish_data = payload.dict(exclude={"attachment_uid", "location_id"})

        if payload.location_id is not None:
            location = DishLocation.objects.filter(pk=payload.location_id).first()
            if not location:
                raise DishLocationNotFoundException
            dish_data["location"] = location

        return self.orm.create_dish_with_attachment(user=user, dish_data=dish_data, attachment=attachment)

    def get_all_dishes(
        self,
        filter: FilterDishSchema,
        sort_by: SortByEnum = SortByEnum.RATING_DESC,
        user: TUser | None = None
    ):
        return self.orm.get_all_dishes(filter=filter, sort_by=sort_by, user=user)
    
    def get_dishes_by_chef(
        self,
        chef_id: str,
        filter: FilterDishSchema,
        sort_by: SortByEnum = SortByEnum.RATING_DESC,
        user: TUser | None = None
    ):
        return self.orm.get_dishes_by_chef(
            chef_id=chef_id, 
            filter=filter, 
            sort_by=sort_by, 
            user=user
        )

    def get_top_dishes(self, limit: int = 10):
        return self.orm.get_top_dishes(limit=limit)

    def get_dish_by_uid(self, uid: UUID, user: TUser | None = None):
        dish = self.orm.get_dish_by_uid(uid=uid)

        if not dish:
            raise DishNotFoundException

        # default values (guest-safe)
        dish.is_favorite = False
        dish.allergy_warning = False
        dish.allergen_ingredients = []

        # ===== GUEST FLOW =====
        if user is None:
            return dish

        # ===== USER FLOW =====
        profile = CustomerProfile.objects.filter(user_id=user.id).first()
        allergy_mode = (profile.allergy_mode if profile else AllergyModeEnum.WARN)

        allergic_ids = list(
            AllergicIngredient.objects.filter(
                user_id=user.id,
                deleted=False
            ).values_list("ingredient_id", flat=True)
        )

        # check allergy
        has_allergy = False
        allergen_ingredients = []

        if allergic_ids:
            qs = DishIngredient.objects.filter(
                dish_id=dish.uid,
                ingredient_id__in=allergic_ids,
                deleted=False
            )

            has_allergy = qs.exists()

            allergen_ingredients = list(
                qs.values_list("ingredient__name", flat=True)
            )

        # mode handling
        if allergy_mode == AllergyModeEnum.HIDE and has_allergy:
            raise DishNotFoundException

        dish.allergy_warning = (
            has_allergy and allergy_mode == AllergyModeEnum.WARN
        )

        dish.allergen_ingredients = allergen_ingredients

        dish.is_favorite = CustomerFavoriteDish.objects.filter(
            user_id=user.id,
            dish_id=dish.uid,
            deleted=False
        ).exists()

        return dish

    def update_dish(self, user: TUser, uid: UUID, payload: DishUpdateSchema):
        dish = self.get_dish_by_uid(uid=uid)
        
        # Update attachment
        if payload.attachment_uid is not None:
            try:
                dish_image_uuid = UUID(str(payload.attachment_uid))
            except ValueError:
                raise AttachmentNotFound
            dish.attachment = self.attachment_service.handle_attachment(uid=dish_image_uuid)

        # ✅ SỬA: Xử lý location_id
        # Kiểm tra nếu payload có chứa location_id (kể cả null)
        if hasattr(payload, 'location_id'):
            if payload.location_id is not None:
                location = DishLocation.objects.filter(pk=payload.location_id).first()
                if not location:
                    raise DishLocationNotFoundException
                dish.location = location
            else:
                # Cho phép xóa location
                dish.location = None
            
            print(f"📍 [Backend] Updating dish {uid} with location_id: {payload.location_id}")
            print(f"📍 [Backend] Location after update: {dish.location}")
        
        update_payload = payload.dict(exclude={"attachment_uid", "location_id"}, exclude_none=True)
        result = self.orm.update_dish(
            user=user,
            dish=dish,
            payload=update_payload,
        )
        
        # ✅ Log kết quả
        print(f"✅ [Backend] Dish updated, location_id: {dish.location_id if dish.location else None}")
        
        return result

    def compute_dish_confidence(self, ingredients):
        total_weight = 0.0
        weighted_sum = 0.0
        confidences = []

        for di in ingredients:
            w = di.weight or 0.0
            c = di.confidence or 0.0

            if w > 0:
                total_weight += w
                weighted_sum += w * c

            confidences.append(c)

        if total_weight == 0:
            return 0.0

        # =========================
        # BASE: weighted average
        # =========================
        weighted_avg = weighted_sum / total_weight

        # =========================
        # PENALTY 1: low-quality ingredient
        # =========================
        min_conf = min(confidences) if confidences else 0.0
        quality_penalty = 0.5 + 0.5 * min_conf

        # =========================
        # PENALTY 2: too few ingredients (NEW)
        # =========================
        n = len(ingredients)
        k = 5  # số ingredient đủ để tin tưởng

        coverage = 0.5 + 0.5 * (1 - math.exp(-n / k))

        # =========================
        # FINAL
        # =========================
        dish_conf = weighted_avg * quality_penalty * coverage

        return round(dish_conf, 3)
    

    def generate_note(self, conf: float) -> str:
        if conf >= 0.8:
            return "Dữ liệu dinh dưỡng đáng tin cậy"
        elif conf >= 0.5:
            return "Một số nguyên liệu chưa được xác thực hoàn toàn"
        else:
            return "Dữ liệu có thể không chính xác"
        
    def build_confidence_text(self, conf: float) -> str:
        percent = round(conf * 100, 1)

        if conf >= 0.8:
            return f"Độ tin cậy cao ({percent}%)"
        elif conf >= 0.5:
            return f"Độ tin cậy trung bình ({percent}%)"
        else:
            return f"Độ tin cậy thấp ({percent}%)"
   
    def build_response_customer(self, ingredients, dish_conf):
        note = self.generate_note(dish_conf)

        percent = round(dish_conf * 100, 1)

        r = self.smart_round

        # 👇 NEW
        nutrition_total = self.compute_total_nutrition(ingredients)

        ingredient_list = []

        for di in ingredients:
            name = (
                di.ingredient.name
                if di.ingredient and di.ingredient.name
                else di.custom_name
            ) or "Unknown Ingredient"
            ingredient_list.append({
                "ingredient_name": name,
                "weight": r("weight", di.weight),
                "energy": r("energy", di.energy),
                "protein": r("protein", di.protein),
                "lipid": r("lipid", di.lipid),
                "carbohydrate": r("carbohydrate", di.carbohydrate),
                "fiber": r("fiber", di.fiber),
                "natri": r("natri", di.natri),
                "cholesterol": r("cholesterol", di.cholesterol),
            })

        return {
            "confidence_of_dish": dish_conf,
            "confidence_text": self.build_confidence_text(dish_conf),
            "note": note,
            "nutrition_total": nutrition_total,   
            "ingredients": ingredient_list,
        }
    
    def smart_round(self, field, value, mode="customer"):
        if value is None:
            return 0.0

        config = (
            self.CHEF_ROUND_CONFIG
            if mode == "chef"
            else self.CUSTOMER_ROUND_CONFIG
        )

        return round(value, config.get(field, 2))
    
    def compute_total_nutrition(self, ingredients):
        # r = self.smart_round
        r = lambda f, v: self.smart_round(f, v, "customer")

        return {
            "energy": r("energy", sum((di.energy or 0.0) for di in ingredients)),
            "protein": r("protein", sum((di.protein or 0.0) for di in ingredients)),
            "lipid": r("lipid", sum((di.lipid or 0.0) for di in ingredients)),
            "carbohydrate": r("carbohydrate", sum((di.carbohydrate or 0.0) for di in ingredients)),
            "fiber": r("fiber", sum((di.fiber or 0.0) for di in ingredients)),
            "natri": r("natri", sum((di.natri or 0.0) for di in ingredients)),
            "cholesterol": r("cholesterol", sum((di.cholesterol or 0.0) for di in ingredients)),
        }
    
    def compute_total_nutrition_chef(self, ingredients):
        fields = [
            "energy", "protein", "lipid", "carbohydrate", "fiber",
            "natri", "kali", "cholesterol",
            "retinol", "caroten",
            "vitamin_b_1", "vitamin_b_2", "vitamin_pp", "vitamin_c",
            "calcium", "phosphorus", "fe", "mg", "zn",
        ]

        totals = {field: 0.0 for field in fields}

        for di in ingredients:
            for field in fields:
                totals[field] += getattr(di, field, 0.0) or 0.0

        # 👉 làm tròn
        r = self.smart_round

        return {
            field: r(field, totals[field])
            for field in fields
        }
        
    def get_all_ingredients_of_dish_for_customers(self, uid: UUID):
        # check dish exist
        dish = self.get_dish_by_uid(uid=uid)

        ingredients = list(
            self.orm.get_all_ingredients_of_dish_for_customers(dish=dish)
        )
        
        mapped_ingredients = []
        for item in ingredients:
            # 👇 TECH LEAD DEBUG: Bắt tận tay data từ DB lên
            print(f"\n--- 🔍 DEBUG DISH INGREDIENT: {item.uid} ---")
            print(f"1. custom_name: '{getattr(item, 'custom_name', 'KHÔNG CÓ CỘT NÀY')}'")
            print(f"2. type(item.ingredient): {type(getattr(item, 'ingredient', None))}")
            
            try:
                if item.ingredient:
                    print(f"3. ingredient.name: '{item.ingredient.name}'")
                else:
                    print("3. item.ingredient là NONE (Khóa ngoại bị rỗng dưới DB!)")
            except Exception as e:
                print(f"🔥 LỖI CRASH KHI GỌI TÊN: {e}")

            # Xử lý gán tên an toàn
            name = item.computed_ingredient_name

            # ... (Map các fields khác như cũ)
            mapped_ingredients.append({
                "ingredient_name": name,
                "weight": item.weight,
                # ...
            })

        if not ingredients:
            return {
                "confidence_of_dish": 0.0,
                "note": "Không có dữ liệu nguyên liệu",
                "ingredients": []
            }

        # compute confidence
        dish_conf = self.compute_dish_confidence(ingredients)

        return self.build_response_customer(ingredients, dish_conf)
    
    def build_response_chef(self, ingredients, dish_conf):
        # 👉 dùng round config cho chef
        r = lambda f, v: self.smart_round(f, v, "chef")

        percent = round(dish_conf * 100, 1)
        text = self.build_confidence_text(dish_conf)
        note = self.generate_note(dish_conf)

        ingredient_list = []

        for di in ingredients:
            ingredient_list.append({
                # ✅ THÊM UID CỦA DISHINGREDIENT VÀO ĐÂY
                "uid": str(di.uid),  # ← ĐÂY LÀ DÒNG QUAN TRỌNG!
                
                # ===== PUBLIC =====
                "ingredient_name": di.computed_ingredient_name,
                "is_custom": di.is_custom,

                "weight": r("weight", di.weight or 0.0),
                "energy": r("energy", di.energy or 0.0),
                "protein": r("protein", di.protein or 0.0),
                "lipid": r("lipid", di.lipid or 0.0),
                "carbohydrate": r("carbohydrate", di.carbohydrate or 0.0),
                "fiber": r("fiber", di.fiber or 0.0),
                "natri": r("natri", di.natri or 0.0),
                "cholesterol": r("cholesterol", di.cholesterol or 0.0),

                # ===== PRIVATE =====
                "confidence": r("confidence", di.confidence or 0.0),
                "source": di.source,
                "approval_status": di.approval_status,
                
                # ✅ THÊM INGREDIENT_UID NẾU CẦN
                "ingredient_uid": di.computed_ingredient_uid,
            })

        nutrition_total = self.compute_total_nutrition_chef(ingredients)

        return {
            "confidence_of_dish": r("confidence", dish_conf),
            "confidence_percent": percent,
            "confidence_text": text,
            "note": note,
            "nutrition_total": nutrition_total,
            "ingredients": ingredient_list,
        }
    def get_all_ingredients_of_dish_for_chefs(self, uid: UUID):
        dish = self.get_dish_by_uid(uid=uid)

        ingredients = list(
            self.orm.get_all_ingredients_of_dish_for_chefs(dish=dish)
        )

        if not ingredients:
            return {
                "confidence_of_dish": 0.0,
                "confidence_percent": 0.0,
                "confidence_text": "Không có dữ liệu",
                "note": "Không có dữ liệu nguyên liệu",
                "nutrition_total": {},
                "ingredients": []
            }

        dish_conf = self.smart_round(
            "confidence",
            self.compute_dish_confidence(ingredients)
        )

        return self.build_response_chef(ingredients, dish_conf)
    
    def preview_ingredient_for_dish(self, uid: UUID, payload: DishIngredientSchema):
        ingredient = self.ingredient_service.get_ingredient_by_uid(uid=payload.ingredient_uid)
        if not ingredient:
            raise IngredientDoesNotExist

        values, warnings, confidence = self._process_ingredient_pipeline(
            payload=payload,
            ingredient=ingredient,
            approval_status=IngredientImportStatusEnum.APPROVED,
            source=IngredientSourceEnum.USDA,
        )

        return {
            "ingredient_uid": ingredient.uid,
            "ingredient_name": ingredient.name,
            "weight": payload.weight,
            "nutritions": values,
            "warnings": warnings,
            "confidence": confidence,
        }
    
    def add_ingredient_to_dish(self, user: TUser, uid: UUID, payload: DishIngredientCreateSchema):
        dish = self.orm.get_dish_by_uid(uid=uid)
        if not dish:
            raise DishNotFoundException
            
        ingredient = self.ingredient_service.get_ingredient_by_uid(uid=payload.ingredient_uid)
        if not ingredient:
            raise IngredientDoesNotExist

        values, warnings, confidence = self._process_ingredient_pipeline(
            payload=payload,
            ingredient=ingredient,
            approval_status=IngredientImportStatusEnum.APPROVED,
            source=IngredientSourceEnum.USDA,
        )

        if self.orm.dish_has_ingredient(dish=dish, ingredient=ingredient):
            dish_ingredient = self.orm.get_dish_ingredient_by_dish_and_ingredient(dish=dish, ingredient=ingredient)
        else:
            dish_ingredient = self.orm.add_ingredient_to_dish(
                dish=dish,
                ingredient=ingredient,
                custom_name=None,
                source=IngredientSourceEnum.USDA,
                suggestion=None,
                created_by=user,
                updated_by=user,
                approval_status=IngredientImportStatusEnum.APPROVED,
                weight=payload.weight,
                nutrient_values=values,
                confidence=confidence,
            )

        return {
            "status": dish_ingredient.approval_status,
            "dish_uid": dish.uid,
            "ingredient_uid": ingredient.uid if ingredient else None,
            "ingredient_name": ingredient.name if ingredient else None,
            "custom_name": dish_ingredient.custom_name,
            "source": dish_ingredient.source,
            "suggestion_uid": dish_ingredient.suggestion.uid if dish_ingredient.suggestion else None,
            "approval_status": dish_ingredient.approval_status,
            "created_by_id": dish_ingredient.created_by_id,
            "updated_by_id": dish_ingredient.updated_by_id,
            "nutritions": values,
            "warnings": warnings,
            "confidence": confidence,
        }

    def add_suggested_ingredient_to_dish(self, user: TUser, uid: UUID, payload: DishIngredientCreateBySuggestionSchema):
        dish = self.orm.get_dish_by_uid(uid=uid)
        if not dish:
            raise DishNotFoundException

        suggestion = self.ingredient_orm.find_one_pending_suggestin_by_uid(uid=payload.suggestion_uid)
        if not suggestion:
            raise IngredientSuggestionNotFound

        if self.orm.dish_has_ingredient_suggestion(dish=dish, suggestion=suggestion):
            raise DishIngredientAlreadyExists
        
        #TODO: tìm 1 cái dish ingredient của chef đó có cùng suggestion để lấy các trường dinh dưỡng, và dựa vào tỉ lệ weight giữa hai cái để tính ra values nutrition cho dish ingredient mới,
        old_di = self.orm.get_one_dish_ingredient_by_suggestion_and_user(
            suggestion=suggestion,
            user=user,
        )
        values = {}
        for field in DISH_NUTRIENT_FIELDS:
            old_val = getattr(old_di, field, None) if old_di else None

            if old_val is not None:
                values[field] = (payload.weight / old_di.weight) * old_val
            else:
                values[field] = None

        dish_ingredient = self.orm.add_ingredient_to_dish(
            dish=dish,
            ingredient=None,
            weight=payload.weight,
            custom_name=suggestion.suggested_name,
            source=IngredientSourceEnum.CHEF_SUGGESTION,
            suggestion=suggestion,
            created_by=user,
            updated_by=user,
            approval_status=IngredientImportStatusEnum.PENDING,
            nutrient_values=values,
            confidence=old_di.confidence if old_di else None,
        )

        return {
            "status": "success",
            "dish_uid": dish.uid,
            "ingredient_custom_name": dish_ingredient.custom_name, 
            "source": dish_ingredient.source,
            "suggestion_uid": dish_ingredient.suggestion.uid if dish_ingredient.suggestion else None,
            "approval_status": dish_ingredient.approval_status,
            "created_by_id": user.id,
            "updated_by_id": user.id,
            "confidence": dish_ingredient.confidence,
            "nutritions": values,
        }
    #===== DISH INGREDIENT =====
    def get_dish_ingredient_by_uid(self, uid: UUID):
        dishingredient = self.orm.get_dish_ingredient_by_uid(uid=uid)
        if not dishingredient:
            raise DishIngredientNotFoundException
        return {
            "dish_uid": dishingredient.dish.uid,
            "ingredient_uid": dishingredient.ingredient.uid if dishingredient.ingredient else None,
            "ingredient_name": dishingredient.ingredient.name if dishingredient.ingredient else None,
            "custom_name": dishingredient.custom_name,
            "source": dishingredient.source,
            "suggestion_uid": dishingredient.suggestion.uid if dishingredient.suggestion else None,
            "approval_status": dishingredient.approval_status,
            "created_by_id": dishingredient.created_by_id,
            "updated_by_id": dishingredient.updated_by_id,
            "weight": dishingredient.weight,
            "energy": dishingredient.energy,
            "protein": dishingredient.protein,
            "lipid": dishingredient.lipid,
            "carbohydrate": dishingredient.carbohydrate,
            "fiber": dishingredient.fiber,
            "natri": dishingredient.natri,
            "kali": dishingredient.kali,
            "cholesterol": dishingredient.cholesterol,
            "retinol": dishingredient.retinol,
            "caroten": dishingredient.caroten,
            "vitamin_b_1": dishingredient.vitamin_b_1,
            "vitamin_b_2": dishingredient.vitamin_b_2,
            "vitamin_pp": dishingredient.vitamin_pp,
            "vitamin_c": dishingredient.vitamin_c,
            "calcium": dishingredient.calcium,
            "phosphorus": dishingredient.phosphorus,
            "fe": dishingredient.fe,
            "mg": dishingredient.mg,
            "zn": dishingredient.zn,
        }
        
    def update_dish_ingredient(
        self,
        user: TUser,
        uid: UUID,
        payload: DishIngredientSchema
    ):
        # ===== 1. Load DishIngredient =====
        dish_ingredient = self.orm.get_dish_ingredient_by_uid_with_select_related(uid=uid)
        if not dish_ingredient:
            raise DishIngredientNotFoundException

        dish = dish_ingredient.dish
        ingredient = dish_ingredient.ingredient
        source = payload.source or dish_ingredient.source
        suggestion = dish_ingredient.suggestion
        custom_name = self._get_custom_name(payload) or dish_ingredient.custom_name
        
        # ✅ THÊM DÒNG NÀY: Khởi tạo approval_status với giá trị hiện tại
        approval_status = dish_ingredient.approval_status

        if payload.ingredient_uid:
            ingredient = self.ingredient_orm.get_ingredient_by_uid(uid=payload.ingredient_uid)
            if not ingredient:
                raise IngredientDoesNotExist
            custom_name = None
            approval_status = IngredientImportStatusEnum.APPROVED
            source = IngredientSourceEnum.USDA
            suggestion = None
        elif ingredient is None and not custom_name:
            raise ValidationError(
                [{"loc": ["custom_name"], "msg": "custom_name la bat buoc khi ingredient_uid = null"}]
            )
        elif ingredient is None and dish_ingredient.approval_status != IngredientImportStatusEnum.PENDING:
            approval_status = IngredientImportStatusEnum.PENDING
        elif ingredient is None:
            source = source or IngredientSourceEnum.CHEF_SUGGESTION
            suggestion = self.ingredient_orm.create_ingredient_suggestion(
                user=user,
                suggested_name=custom_name,
                suggested_category=None,
            )
            # ✅ THÊM DÒNG NÀY
            approval_status = IngredientImportStatusEnum.PENDING

        # ===== 2. Pipeline (reuse) =====
        values, warnings, confidence = self._process_ingredient_pipeline(
            payload=payload,
            ingredient=ingredient,
            approval_status=approval_status,
            source=source,
        )

        # ===== 3. Update =====
        updated = self.orm.update_dish_ingredient(
            dish_ingredient=dish_ingredient,
            weight=payload.weight,
            nutrient_values=values,
            ingredient=ingredient,
            custom_name=custom_name,
            approval_status=approval_status,
            source=source,
            suggestion=suggestion,
            updated_by=user,
        )

        # ===== 4. Response =====
        return {
            "status": "success",
            "dish_uid": dish.uid,
            "ingredient_uid": ingredient.uid if ingredient else None,
            "ingredient_name": ingredient.name if ingredient else None,
            "custom_name": custom_name,
            "source": updated.source,
            "suggestion_uid": updated.suggestion.uid if updated.suggestion else None,
            "approval_status": approval_status,
            "created_by_id": updated.created_by_id,
            "updated_by_id": updated.updated_by_id,
            "nutritions": values,
            "warnings": warnings,
            "confidence": confidence,
        }
    
    def soft_delete_dish_ingredient(self, uid: UUID, user: TUser):
        dish_ingredient = self.orm.get_dish_ingredient_by_uid(uid=uid)
        if not dish_ingredient:
            raise DishIngredientNotFoundException
        return self.orm.soft_delete_dish_ingredient(dish_ingredient=dish_ingredient, user=user)

    def preview_suggest_ingredient_for_dish(self, uid: UUID, payload: DishIngredientSuggestionSchema, user: TUser):
        dish = self.orm.get_dish_by_uid(uid=uid)
        if not dish:
            raise DishNotFoundException
        
        if self.orm.dish_has_custom_ingredient(dish=dish, custom_name=payload.custom_name, user=user):
            raise DishIngredientSuggestionAlreadyExists
        
        candidates = self.ingredient_orm.find_suggestion_candidates(
            suggested_name=payload.custom_name.strip(),
            limit = payload.limit if payload.limit is not None else 10
        )

        values, warnings, confidence = self._process_ingredient_pipeline(
            payload=payload,
            ingredient=None,
            approval_status=IngredientImportStatusEnum.PENDING,
            source=IngredientSourceEnum.CHEF_SUGGESTION,
        )

        return {
            "custom_name": payload.custom_name.strip(),
            "weight": payload.weight,
            "nutrition": values,
            "candidates": candidates,
            "warnings": warnings,
            "confidence": confidence,
        }
    
    def suggest_ingredient_for_dish(self, user: TUser, uid: UUID, payload: DishIngredientSuggestionSchema):
        dish = self.orm.get_dish_by_uid(uid=uid)
        if not dish:
            raise DishNotFoundException

        if self.orm.dish_has_custom_ingredient(dish=dish, custom_name=payload.custom_name, user=user):
            raise DishIngredientSuggestionAlreadyExists
        #check var attachment
        attachment = self.attachment_service.handle_attachment(uid=payload.attachment_uid) if payload.attachment_uid else None
      
        suggestion = self.ingredient_suggestion_service.create_suggestion(
            user=user,
            payload=payload,
            attachment=attachment,
        )
        
        # compute confidence
        values, warnings, confidence = self._process_ingredient_pipeline(
            payload=payload,
            ingredient=None,
            approval_status=suggestion.status,
            source=IngredientSourceEnum.CHEF_SUGGESTION,
        )

        self.orm.create_dish_ingredient_from_suggestion(user=user,dish=dish, suggestion=suggestion, payload=payload, confidence=confidence)
        return {
            "uid": suggestion.uid,
            "name": suggestion.suggested_name,
            "category": suggestion.suggested_category,
            "status": suggestion.status,
            "created_by_id": suggestion.created_by_id,
            "verified_by_id": suggestion.verified_by_id,
            "verified_at": suggestion.verified_at,
            "resolution_note": suggestion.resolution_note
        }

    def soft_delete_dish(self, user: TUser, uid: UUID):
        dish = self.get_dish_by_uid(uid=uid)
        if self.orm.soft_delete_dish(user=user, dish=dish):
            return True
        raise DishIsReferenced

    def hard_delete_dish(self, user: TUser, uid: UUID):
        dish = self.get_dish_by_uid(uid=uid)
        if self.orm.delete_dish(dish=dish):
            return True
        raise DishIsReferenced

    def restore_dish(self, user: TUser, uid: UUID):
        print("🔄 [Backend] Attempting to restore dish with UID:", uid)
        dish = self.orm.get_dish_by_uid_including_deleted(uid=uid)
        if not dish:
            raise DishNotFoundException
        if self.orm.restore_dish(user=user, dish=dish):
            return True
        raise DishIsNotDeleted

    def get_dish_availabilities(self, uid: UUID):
        result = self.orm.get_dish_availabilities(uid=uid)
        if not result:
            raise DishNotFoundException
        return DishAvailabilityListResponse(**result)
      
    def create_dish_availabilities(self, uid: UUID, payload: DishAvailabilitySchema):
        dish = self.orm.get_dish_by_uid(uid=uid)
        if not dish:
            raise DishNotFoundException
        payload_data = payload.dict()
        self.orm.create_or_update_availability(
            dish=dish,
            available_date=payload_data.get("available_date"),
            available_quantity=payload_data.get("available_quantity"),
            note=payload_data.get("note"),
        )
        return self.orm.get_dish_availabilities(uid=uid)

    def create_dish_location(self, payload: DishLocationCreateSchema):
        parent = None
        if payload.parent_id is not None:
            parent = DishLocation.objects.filter(pk=payload.parent_id).first()
            if not parent:
                raise DishLocationNotFoundException

        location = DishLocation(
            name=payload.name,
            type=payload.type,
            parent=parent,
        )
        location.save()
        return location

    def get_dish_location_by_id(self, location_id: int):
        location = DishLocation.objects.filter(pk=location_id).first()
        if not location:
            raise DishLocationNotFoundException
        return location
    
    def get_country_locations(self):
        return self.orm.get_country_locations()
    
    def get_dish_locations(self, parent_id: int | None = None, type: str | None = None):
        query = DishLocation.objects.all().order_by("name")
        if parent_id is None:
            query = query.filter(parent__isnull=True)
        else:
            query = query.filter(parent_id=parent_id)
        if type:
            query = query.filter(type=type)
        return query

    def get_dish_location_tree(self):
        locations = DishLocation.objects.prefetch_related(
            Prefetch("children", queryset=DishLocation.objects.order_by("name"))
        ).order_by("name")
        by_parent: dict[int | None, list[DishLocation]] = {}
        for location in locations:
            by_parent.setdefault(location.parent_id, []).append(location)

        def build(parent_id: int | None):
            nodes = []
            for location in by_parent.get(parent_id, []):
                nodes.append(
                    {
                        "id": location.pk,
                        "name": location.name,
                        "slug": location.slug,
                        "type": location.type,
                        "parent_id": location.parent.pk if location.parent else None,
                        "children": build(location.pk),
                    }
                )
            return nodes

        return build(None)

    def update_dish_location(self, location_id: int, payload: DishLocationUpdateSchema):
        location = self.get_dish_location_by_id(location_id=location_id)

        if payload.parent_id is not None:
            parent = DishLocation.objects.filter(pk=payload.parent_id).first()
            if not parent:
                raise DishLocationNotFoundException
            location.parent = parent

        if payload.name is not None:
            location.name = payload.name
        if payload.type is not None:
            location.type = payload.type

        location.save()
        return location

    def delete_dish_location(self, location_id: int):
        location = self.get_dish_location_by_id(location_id=location_id)
        if location.children.exists():
            raise DishLocationHasChildrenException
        location.delete()
        return True
    
    def get_dish_ingredient_by_suggestion_uid(self, suggestion_uid: UUID):
        dish_ingredient = self.orm.get_dish_ingredient_by_suggestion_uid(suggestion_uid=suggestion_uid)
        if not dish_ingredient:
            raise DishIngredientNotFoundException
        return dish_ingredient