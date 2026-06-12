"""
Three-layer validation cho DishIngredient.weight.

Layer 1 — validate_ingredient_weight():
  Gọi mỗi khi tạo/sửa DishIngredient.
  Hard fail — không lưu nếu weight vượt CATEGORY_BOUNDS.

Layer 2 — validate_portion_weight():
  Gọi khi chef publish dish.
  Hard fail — không publish nếu tổng vượt [MIN, MAX]_PORTION_WEIGHT.

Layer 3 — validate_nutrition_outcome():
  Gọi khi chef publish dish.
  Hard fail — không publish nếu nutrition per-serving vượt NUTRITION_BOUNDS.
  Skip nếu bất kỳ ingredient nào thiếu nutrition data.
"""

from django.db.models import Sum

from dish.constants.ingredient_bounds import (
    CATEGORY_BOUNDS,
    MAX_PORTION_WEIGHT,
    MIN_PORTION_WEIGHT,
    NUTRIENT_FIELD_MAP,
    NUTRITION_BOUNDS,
)
from exceptions.nutrition import (
    IngredientWeightOutOfBounds,
    NutritionOutlierError,
    PortionWeightOutOfBounds,
)


def validate_ingredient_weight(
    weight: float,
    ingredient_category: str | None,
    ingredient_name: str = "",
) -> None:
    """
    Layer 1: kiểm tra weight của 1 DishIngredient.

    Raises IngredientWeightOutOfBounds nếu:
      - weight <= 0
      - weight < min (theo category)
      - weight > max (theo category)
    """
    if weight <= 0:
        raise IngredientWeightOutOfBounds(
            ingredient_name=ingredient_name or "?",
            weight=weight,
            category=ingredient_category or "UNKNOWN",
            min_g=0.001,
            max_g=None,
        )

    if ingredient_category and ingredient_category in CATEGORY_BOUNDS:
        min_g, max_g = CATEGORY_BOUNDS[ingredient_category]
        if weight < min_g or weight > max_g:
            raise IngredientWeightOutOfBounds(
                ingredient_name=ingredient_name or "?",
                weight=weight,
                category=ingredient_category,
                min_g=min_g,
                max_g=max_g,
            )


def validate_portion_weight(dish_uid) -> None:
    """
    Layer 2: kiểm tra tổng khối lượng khẩu phần của dish.

    Gọi khi publish. Raises PortionWeightOutOfBounds nếu nằm ngoài [MIN, MAX].
    """
    from dish.models import DishIngredient

    total = (
        DishIngredient.objects.filter(dish__uid=dish_uid, deleted=False)
        .aggregate(total=Sum("weight"))["total"]
        or 0.0
    )
    total = float(total)

    if total < MIN_PORTION_WEIGHT:
        raise PortionWeightOutOfBounds(total_g=total, min_g=MIN_PORTION_WEIGHT)
    if total > MAX_PORTION_WEIGHT:
        raise PortionWeightOutOfBounds(total_g=total, max_g=MAX_PORTION_WEIGHT)


def validate_nutrition_outcome(dish_uid, serving_size: int = 1) -> None:
    """
    Layer 3: kiểm tra kết quả dinh dưỡng per-serving.

    Gọi khi publish. Skip hoàn toàn nếu bất kỳ ingredient nào thiếu nutrition data.
    Raises NutritionOutlierError nếu bất kỳ chỉ số nào vượt NUTRITION_BOUNDS.

    serving_size: dish.serving_size (mặc định 1 nếu không khai báo).
    """
    from dish.models import DishIngredient

    serving_size = max(serving_size, 1)

    items = list(
        DishIngredient.objects.filter(
            dish__uid=dish_uid, deleted=False
        ).values(*NUTRIENT_FIELD_MAP.values())
    )

    if not items:
        return

    totals: dict[str, float] = {key: 0.0 for key in NUTRITION_BOUNDS}

    for row in items:
        for bound_key, field_name in NUTRIENT_FIELD_MAP.items():
            val = row.get(field_name)
            if val is None:
                # Thiếu data cho 1 ingredient → skip toàn bộ Layer 3
                return
            totals[bound_key] += float(val)

    # Chia cho serving_size để ra per-serving
    per_serving = {k: v / serving_size for k, v in totals.items()}

    violations = []
    for nutrient, max_val in NUTRITION_BOUNDS.items():
        value = per_serving[nutrient]
        if value > max_val:
            violations.append({
                "nutrient": nutrient,
                "per_serving": round(value, 1),
                "total_dish": round(totals[nutrient], 1),
                "max_allowed_per_serving": max_val,
            })

    if violations:
        raise NutritionOutlierError(violations=violations, serving_size=serving_size)


def validate_on_publish(dish_uid) -> None:
    """
    Convenience: chạy Layer 2 + Layer 3 khi chef publish dish.
    Layer 1 được gọi riêng khi tạo/sửa từng DishIngredient.
    """
    from dish.models import Dish

    dish = Dish.objects.filter(uid=dish_uid).first()
    if dish is None:
        return

    validate_portion_weight(dish_uid)
    validate_nutrition_outcome(dish_uid, serving_size=dish.serving_size)
