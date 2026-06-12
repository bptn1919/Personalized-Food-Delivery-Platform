from django.test import TestCase

from types import SimpleNamespace
from unittest.mock import Mock
from uuid import uuid4

from ninja.errors import ValidationError

from dish.schemas.requests import DishIngredientSchema
from dish.services import DishService



class DishServicePreviewTests(TestCase):
	def setUp(self):
		self.service = DishService()
		self.service.orm = Mock()
		self.service.ingredient_orm = Mock()
		self.dish_uid = uuid4()
		self.ingredient_uid = uuid4()
		self.service.orm.get_dish_by_uid.return_value = SimpleNamespace(uid=self.dish_uid, name="Dish")

	def test_preview_ingredient_for_dish_raises_hard_validation_for_negative_nutrition(self):
		ingredient = SimpleNamespace(name="Gao", weight=100, energy=130)
		self.service.ingredient_orm.get_ingredient_by_uid.return_value = ingredient
		payload = DishIngredientSchema(
			ingredient_uid=self.ingredient_uid,
			weight=150,
			energy=-1,
		)

		with self.assertRaises(ValidationError):
			self.service.preview_ingredient_for_dish(uid=self.dish_uid, payload=payload)

	def test_preview_ingredient_for_dish_returns_warning_and_confidence(self):
		ingredient = SimpleNamespace(
			name="Gao",
			weight=50,
			energy=130,
			protein=10,
			lipid=5,
			carbohydrate=20,
			fiber=None,
			natri=None,
			kali=None,
			cholesterol=None,
			retinol=None,
			caroten=None,
			vitamin_b_1=None,
			vitamin_b_2=None,
			vitamin_pp=None,
			vitamin_c=None,
			calcium=None,
			phosphorus=None,
			fe=None,
			mg=None,
			zn=None,
		)
		self.service.ingredient_orm.get_ingredient_by_uid.return_value = ingredient
		payload = DishIngredientSchema(
			ingredient_uid=self.ingredient_uid,
			weight=150,
			energy=300,
			protein=30,
			lipid=15,
			carbohydrate=60,
		)

		result = self.service.preview_ingredient_for_dish(uid=self.dish_uid, payload=payload)

		self.assertEqual(result["nutrition"]["energy"], 300)
		self.assertIn("Energy không nhất quán với macro", result["warnings"])
		self.assertEqual(result["confidence"], 0.8)

	def test_preview_ingredient_for_dish_rejects_extreme_ratio_overrides(self):
		ingredient = SimpleNamespace(
			name="Gao",
			weight=100,
			energy=130,
			protein=10,
			lipid=5,
			carbohydrate=20,
			fiber=None,
			natri=None,
			kali=None,
			cholesterol=None,
			retinol=None,
			caroten=None,
			vitamin_b_1=None,
			vitamin_b_2=None,
			vitamin_pp=None,
			vitamin_c=None,
			calcium=None,
			phosphorus=None,
			fe=None,
			mg=None,
			zn=None,
		)
		self.service.ingredient_orm.get_ingredient_by_uid.return_value = ingredient
		payload = DishIngredientSchema(
			ingredient_uid=self.ingredient_uid,
			weight=100,
			energy=100000000000,
		)

		with self.assertRaises(ValidationError):
			self.service.preview_ingredient_for_dish(uid=self.dish_uid, payload=payload)
