"""
Giới hạn validation cho DishIngredient.weight.

Layer 1 — Per-ingredient-category bounds:
  Mục đích: chặn dữ liệu rác (typo, đơn vị sai).
  Nguồn: common sense + thực tế ẩm thực Việt Nam.
  Không phải chuẩn dinh dưỡng — không phân biệt "phở bò phải có bao nhiêu thịt".

Layer 2 — Portion total bounds:
  Mục đích: chặn tổng khối lượng vô lý.
  Hỗ trợ combo/lẩu/set meal (MAX=5000g).

Layer 3 — Nutritional outcome bounds (per serving):
  Mục đích: phát hiện kết quả dinh dưỡng vô lý về mặt sinh học.
  Áp dụng per-serving (tổng / dish.serving_size).
  Nguồn tham chiếu: WHO Dietary Reference Intakes.
  Skip nếu thiếu nutrition data — không reject vì thiếu thông tin.
"""

# ── Layer 1 ────────────────────────────────────────────────────────────────────
# (min_g, max_g) per single DishIngredient.weight entry

CATEGORY_BOUNDS: dict[str, tuple[float, float]] = {
    "SPICE":        (0.1,  60),    # Muối, đường, tiêu, nước mắm (~50ml)
    "OILFATBUTTER": (1,    150),   # Dầu ăn, bơ, mỡ
    "PROTEIN":      (5,    1000),  # Thịt, cá, hải sản, đậu phụ, trứng
    "GRAIN":        (5,    1500),  # Cơm, bún, mì, bánh mì, khoai
    "VEGETABLE":    (2,    1500),  # Rau, củ — rau xào số lượng lớn hợp lý
    "FRUIT":        (2,    1000),  # Trái cây trong món, sinh tố
    "MILK":         (5,    1000),  # Sữa, kem, phô mai
}

# Category không có trong CATEGORY_BOUNDS → chỉ check min > 0, không check max

# ── Layer 2 ────────────────────────────────────────────────────────────────────
MIN_PORTION_WEIGHT = 10      # gram — nhỏ nhất (nước chấm, sauce side)
MAX_PORTION_WEIGHT = 5000    # gram — hỗ trợ lẩu/combo gia đình (~4 người)

# ── Layer 3 ────────────────────────────────────────────────────────────────────
# Per-serving (tổng / dish.serving_size)

NUTRITION_BOUNDS: dict[str, float] = {
    "calories":  5000,   # kcal  — WHO RDI ~2000-2500; 5000 là ceiling rõ
    "protein_g": 300,    # g     — giới hạn hấp thụ sinh học ~200-300g/ngày
    "fat_g":     300,    # g     — 300g fat = 2700 kcal chỉ từ fat
    "carb_g":    600,    # g     — max carbs WHO; 600 là ceiling rõ
    "sodium_mg": 10000,  # mg    — WHO max 2000mg/ngày; 10000 là bất thường rõ
}

# Nutrient field mapping: NUTRITION_BOUNDS key → DishIngredient field
NUTRIENT_FIELD_MAP: dict[str, str] = {
    "calories":  "energy",
    "protein_g": "protein",
    "fat_g":     "lipid",
    "carb_g":    "carbohydrate",
    "sodium_mg": "natri",
}
