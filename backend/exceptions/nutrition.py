from http import HTTPStatus
from utils.router.exception import APIException


class IngredientWeightOutOfBounds(APIException):
    """Layer 1: weight của 1 ingredient vượt giới hạn category."""
    error_code = HTTPStatus.UNPROCESSABLE_ENTITY
    message_code = "INGREDIENT_WEIGHT_OUT_OF_BOUNDS"
    message = "Khối lượng nguyên liệu vượt giới hạn cho phép của danh mục này."

    def __init__(self, ingredient_name: str, weight: float, category: str, min_g: float | None, max_g: float | None):
        detail = {
            "ingredient": ingredient_name,
            "entered_weight_g": weight,
            "category": category,
        }
        if min_g is not None:
            detail["min_allowed_g"] = min_g
        if max_g is not None:
            detail["max_allowed_g"] = max_g
        super().__init__(detail=detail)


class PortionWeightOutOfBounds(APIException):
    """Layer 2: tổng khối lượng khẩu phần vượt giới hạn."""
    error_code = HTTPStatus.UNPROCESSABLE_ENTITY
    message_code = "PORTION_WEIGHT_OUT_OF_BOUNDS"
    message = "Tổng khối lượng khẩu phần không hợp lý."

    def __init__(self, total_g: float, min_g: float | None = None, max_g: float | None = None):
        detail: dict = {"total_weight_g": round(total_g, 1)}
        if min_g is not None:
            detail["min_allowed_g"] = min_g
        if max_g is not None:
            detail["max_allowed_g"] = max_g
        super().__init__(detail=detail)


class NutritionOutlierError(APIException):
    """Layer 3: kết quả dinh dưỡng per-serving vượt ngưỡng sinh học."""
    error_code = HTTPStatus.UNPROCESSABLE_ENTITY
    message_code = "NUTRITION_OUTLIER"
    message = "Kết quả dinh dưỡng của món ăn vượt ngưỡng hợp lý. Vui lòng kiểm tra lại khối lượng nguyên liệu."

    def __init__(self, violations: list[dict], serving_size: int):
        super().__init__(detail={"serving_size": serving_size, "violations": violations})
