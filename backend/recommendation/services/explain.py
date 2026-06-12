def build_reasons(item: dict) -> list[str]:
    reasons: list[str] = []

    favorite_score = float(item.get("favorite_score", 0.0))
    history_score = float(item.get("history_score", 0.0))
    ingredient_match_ratio = float(item.get("ingredient_match_ratio", 0.0))
    issue_penalty = float(item.get("issue_penalty", 0.0))
    preference_nutrition_mismatch_penalty = float(
        item.get(
            "preference_nutrition_mismatch_penalty",
            item.get("nutrition_penalty", 0.0),
        )
    )
    diet_alignment = float(item.get("diet_alignment", 0.0))
    base_score = float(item.get("base_score", 0.0))

    if favorite_score >= 0.7:
        reasons.append("Phù hợp với sở thích của bạn")

    if history_score >= 0.6:
        reasons.append("Được đề xuất dựa trên lịch sử gần đây của bạn")

    if ingredient_match_ratio >= 0.5:
        reasons.append("Nguyên liệu tương đồng với nhóm bạn yêu thích")

    if issue_penalty <= 0.2:
        reasons.append("Mức độ nhạy cảm với vấn đề liên quan thấp")

    if preference_nutrition_mismatch_penalty <= 0.3:
        reasons.append("Cân bằng dinh dưỡng tương đối tốt với xu hướng ăn uống của bạn")

    if diet_alignment >= 0.65:
        reasons.append("Phù hợp với chế độ ăn uống của bạn")

    if base_score >= 0.6:
        reasons.append("Món ăn có chất lượng nền tảng tốt (đánh giá, phổ biến, độ mới)")

    if not reasons:
        reasons.append("Đề xuất theo độ phổ biến và hành vi tương đồng")

    return reasons[:3]
