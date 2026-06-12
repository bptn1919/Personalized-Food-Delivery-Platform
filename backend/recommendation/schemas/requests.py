from ninja import Schema
from typing import Literal
from utils.enums import MealTimeEnum


class DailyNutritionInitRequest(Schema):
	age: int
	gender: str = "OTHER"
	height_cm: float
	weight_kg: float
	activity_level: str = "LIGHT"
	goal: str = "MAINTAIN"


class DailyNutritionProfileUpdateRequest(Schema):
	"""
	Update daily nutrition profile. Only provided fields are updated.
	TDEE and macro targets are recalculated based on new profile.
	"""
	age: int | None = None
	gender: str | None = None
	height_cm: float | None = None
	weight_kg: float | None = None
	activity_level: str | None = None
	goal: str | None = None


class DailyNutritionParseMealRequest(Schema):
	text: str
	meal_time: Literal["BREAKFAST", "LUNCH", "DINNER", "SNACK", "UNKNOWN"] = "UNKNOWN"


class DailyMealLogUpdateRequest(Schema):
	meal_name: str | None = None
	meal_time: Literal["BREAKFAST", "LUNCH", "DINNER", "SNACK", "UNKNOWN"] | None = None
	quantity_multiplier: float | None = None
	dish_uid: str | None = None
