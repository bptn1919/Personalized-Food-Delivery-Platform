"""
ReportAnalysisService — tính metrics kết hợp hai nguồn tín hiệu:

  1. ChefReport   — customer chủ động gửi phản ánh (tỉ trọng cao: 1.0–5.0)
  2. Review.issue — AI model tự động gắn nhãn issue khi review (tỉ trọng thấp: ×0.35)

Hai nguồn phản ánh cùng chiều nhưng khác độ tin cậy:
  - Report là hành động có chủ ý → tín hiệu mạnh hơn
  - Review issue là passive signal từ AI → tín hiệu yếu hơn, nhưng số lượng nhiều

Công thức:
  combined_weighted_sum = Σ report.credibility_weight
                        + REVIEW_SIGNAL_FACTOR × Σ min(review.weight, 1.0)
                              (chỉ review có issue thuộc FOOD_SAFETY_ISSUES)

  chef_ratio = combined_weighted_sum / completed_orders
"""

from datetime import timedelta

from django.utils import timezone

from utils.enums import OrderStatusEnum, ReportCategoryEnum, ReportStatusEnum

# ── Category groups — quyết định route sang handler nào ──────────────────────
FOOD_QUALITY_CATEGORIES: frozenset[str] = frozenset(
    [ReportCategoryEnum.FOOD_SAFETY, ReportCategoryEnum.FOOD_QUALITY, ReportCategoryEnum.HYGIENE]
)
DELIVERY_CATEGORIES: frozenset[str] = frozenset(
    [ReportCategoryEnum.WRONG_ITEM, ReportCategoryEnum.MISSING_ITEM]
)
PAYMENT_REQUIRED_CATEGORIES: frozenset[str] = frozenset(
    [
        ReportCategoryEnum.PAYMENT_ISSUE,
        ReportCategoryEnum.REFUND_ISSUE,
    ]
)
FINANCIAL_CATEGORIES: frozenset[str] = frozenset(
    [
        ReportCategoryEnum.FINANCIAL,
        ReportCategoryEnum.PAYMENT_ISSUE,
        ReportCategoryEnum.REFUND_ISSUE,
    ]
)
ORDER_REQUIRED_CATEGORIES: frozenset[str] = (
    FOOD_QUALITY_CATEGORIES | DELIVERY_CATEGORIES | PAYMENT_REQUIRED_CATEGORIES
)
PLATFORM_EVIDENCE_REQUIRED: frozenset[str] = frozenset(
    [
        ReportCategoryEnum.IMPERSONATION,
        ReportCategoryEnum.FAKE_BUSINESS,
        ReportCategoryEnum.INAPPROPRIATE,
        ReportCategoryEnum.FRAUD,
        ReportCategoryEnum.POLICY_VIOLATION,
        ReportCategoryEnum.ILLEGAL_ACTIVITY,
        ReportCategoryEnum.FINANCIAL,
    ]
)

# ── Food-safety issue labels (từ AI review model) ─────────────────────────────
FOOD_SAFETY_ISSUES: frozenset[str] = frozenset(
    [
        "tanh",
        "hôi",
        "hư thiu",
        "sạn",
        "mốc",
        "ôi",
        "sống",
        "dị vật",
        "bẩn",
        "chua",
    ]
)

# ── Delivery issue labels (từ AI review model) ────────────────────────────────
DELIVERY_ISSUES: frozenset[str] = frozenset(
    [
        "giao sai",
        "giao thiếu",
        "giao chậm",
        "thiếu món",
        "sai món",
    ]
)

# ── Signal weights ─────────────────────────────────────────────────────────────

# Review.weight từ AI model được nhân với hệ số này trước khi cộng vào tổng.
# Ý nghĩa: 1 review food-safety issue = REVIEW_SIGNAL_FACTOR "report equivalents"
REVIEW_SIGNAL_FACTOR = 0.35

# ── Food-quality thresholds ───────────────────────────────────────────────────

# Chef phải có đủ số đơn thì mới xét auto-lock (tránh new chef bị lock sớm)
MIN_COMPLETED_ORDERS_CHEF = 50
MIN_COMPLETED_ORDERS_DISH = 30

# Chỉ tính signal trong vòng N ngày gần nhất
REPORT_WINDOW_DAYS = 30

# Warning email (chưa khóa — nhắc nhở)
WARNING_CHEF_RATIO = 0.04       # 4% combined ratio

# FULL_LOCK: khóa toàn bộ chef
FULL_LOCK_CHEF_RATIO = 0.08     # 8% combined ratio
FULL_LOCK_MIN_REPORTS = 10      # ít nhất 10 report thô (không tính review signal)
FULL_LOCK_MIN_UNIQUE_REPORTERS = 5  # ít nhất 5 người khác nhau (chỉ tính ChefReport)

# DISH_LOCK: chỉ khóa 1 món
DISH_LOCK_RATIO = 0.05          # 5% combined ratio trên đơn có món đó
DISH_LOCK_MIN_REPORTS = 3       # ít nhất 3 report thô về món đó

# Rate limit: tối đa N report mỗi 24h mỗi customer
CUSTOMER_REPORT_DAILY_LIMIT = 5

# ── Credibility weight tiers cho ChefReport ───────────────────────────────────
WEIGHT_PLAIN_REPORT  = 1.0   # chỉ text
WEIGHT_HAS_TEXT      = 1.5   # description >= 30 ký tự
WEIGHT_HAS_IMAGE     = 2.0   # có ảnh bằng chứng
WEIGHT_AI_CONFIRMED  = 3.0   # Gemini xác nhận food_safety_risk=True + HIGH/CRITICAL
WEIGHT_ADMIN         = 5.0   # admin manually confirm


def compute_initial_weight(has_evidence: bool, description: str, reporter_id: int) -> float:
    """
    Tính credibility_weight ban đầu khi ChefReport mới tạo.
    Sau khi Gemini phân tích, weight có thể được nâng lên nếu AI xác nhận.
    """
    from report.models import ChefReport

    if has_evidence:
        base = WEIGHT_HAS_IMAGE
    elif len(description.strip()) >= 30:
        base = WEIGHT_HAS_TEXT
    else:
        base = WEIGHT_PLAIN_REPORT

    # Discount nếu customer hay bị dismiss — tối đa giảm 40%
    dismissed = ChefReport.objects.filter(
        reporter_id=reporter_id, status=ReportStatusEnum.DISMISSED
    ).count()
    acted = ChefReport.objects.filter(
        reporter_id=reporter_id,
        status__in=[ReportStatusEnum.REVIEWED, ReportStatusEnum.ACTED_ON],
    ).count()
    total_closed = dismissed + acted

    if total_closed > 0:
        dismiss_rate = dismissed / total_closed
        history_factor = max(0.6, 1.0 - dismiss_rate * 0.4)
        base = round(base * history_factor, 2)

    return base


def compute_weight_after_ai(current_weight: float, ai_severity: str, ai_food_safety_risk: bool) -> float:
    """Cập nhật weight sau khi Gemini phân tích severity."""
    if ai_food_safety_risk and ai_severity in ("HIGH", "CRITICAL"):
        return max(current_weight, WEIGHT_AI_CONFIRMED)
    return current_weight


def check_customer_rate_limit(reporter_id: int) -> bool:
    """True nếu customer còn trong giới hạn (được phép report)."""
    from report.models import ChefReport
    cutoff = timezone.now() - timedelta(hours=24)
    count = ChefReport.objects.filter(
        reporter_id=reporter_id,
        created_at__gte=cutoff,
        deleted=False,
    ).count()
    return count < CUSTOMER_REPORT_DAILY_LIMIT


def _window_cutoff():
    return timezone.now() - timedelta(days=REPORT_WINDOW_DAYS)


def _compute_review_signal(chef_id: int, dish_uid=None, cutoff=None) -> tuple[float, int]:
    """
    Tổng hợp tín hiệu từ Review.issue (AI-labeled) trong cửa sổ thời gian.

    Dedup bằng order_id: 1 đơn đóng góp tối đa 1 signal (review weight cao nhất).
    Ngăn việc 1 đơn nhiều món hoặc customer edit nhiều lần inflate signal.

    Returns:
        (weighted_sum, order_count)
        weighted_sum = REVIEW_SIGNAL_FACTOR × Σ min(max_weight_per_order, 1.0)
    """
    from django.db.models import Max
    from review.models import Review

    qs = Review.objects.filter(
        dish__owner_id=chef_id,
        deleted=False,
        weight__gt=0,
        issue__in=list(FOOD_SAFETY_ISSUES),
        created_at__gte=cutoff,
    )

    if dish_uid:
        qs = qs.filter(dish__uid=dish_uid)

    # Group by order → lấy max weight để dedup (1 order = 1 signal)
    order_groups = (
        qs
        .values("order_id")
        .annotate(max_weight=Max("weight"))
    )

    total_review_weight = sum(
        min(float(g["max_weight"]), 1.0) for g in order_groups
    )
    order_count = order_groups.count()

    return round(total_review_weight * REVIEW_SIGNAL_FACTOR, 4), order_count


def compute_chef_metrics(chef_id: int, dish_uid=None) -> dict | None:
    """
    Tính combined metrics trong cửa sổ REPORT_WINDOW_DAYS.

    Hai nguồn tín hiệu:
      - ChefReport: report chủ động từ customer, weight 1.0–5.0
      - Review.issue: passive signal từ AI, scaled ×REVIEW_SIGNAL_FACTOR

    Returns None nếu chưa đủ MIN_COMPLETED_ORDERS_CHEF đơn hoàn thành.

    Nếu dish_uid được cung cấp → cũng tính dish-level metrics.
    """
    from order.models import Order, OrderItem
    from report.models import ChefReport

    cutoff = _window_cutoff()

    # Đồng bộ cùng cửa sổ 30 ngày với report/review signal.
    # Dùng created_at vì Order không có completed_at riêng;
    # các đơn tạo trong window hầu như đều hoàn thành trong window.
    completed_orders = Order.objects.filter(
        chef_id=chef_id,
        status=OrderStatusEnum.COMPLETED,
        created_at__gte=cutoff,
    ).count()

    if completed_orders < MIN_COMPLETED_ORDERS_CHEF:
        return None

    # ── Chef-level: ChefReport signal ─────────────────────────────────────────
    chef_reports_qs = ChefReport.objects.filter(
        chef_id=chef_id,
        category__in=list(ORDER_REQUIRED_CATEGORIES),
        created_at__gte=cutoff,
        deleted=False,
        status__in=[
            ReportStatusEnum.PENDING,
            ReportStatusEnum.REVIEWED,
            ReportStatusEnum.ACTED_ON,
        ],
    )

    chef_report_count = chef_reports_qs.count()
    report_weighted_sum = sum(r.credibility_weight for r in chef_reports_qs)
    unique_reporters = chef_reports_qs.values("reporter_id").distinct().count()

    # ── Chef-level: Review signal ──────────────────────────────────────────────
    review_signal_sum, review_count = _compute_review_signal(
        chef_id=chef_id, cutoff=cutoff
    )

    combined_weighted_sum = report_weighted_sum + review_signal_sum
    chef_ratio = combined_weighted_sum / completed_orders if completed_orders else 0.0

    result = {
        "completed_orders": completed_orders,
        # ChefReport-only signals (dùng để check unique_reporters + FULL_LOCK min count)
        "chef_report_count": chef_report_count,
        "unique_reporters": unique_reporters,
        "report_weighted_sum": round(report_weighted_sum, 4),
        # Review signal (scaled)
        "review_count": review_count,
        "review_signal_sum": review_signal_sum,
        # Combined
        "combined_weighted_sum": round(combined_weighted_sum, 4),
        "chef_ratio": round(chef_ratio, 4),
        "window_days": REPORT_WINDOW_DAYS,
    }

    if dish_uid:
        # Số đơn COMPLETED có chứa món này — đồng bộ cùng window 30 ngày
        dish_orders = (
            OrderItem.objects.filter(
                dish__uid=dish_uid,
                order__chef_id=chef_id,
                order__status=OrderStatusEnum.COMPLETED,
                order__created_at__gte=cutoff,
            )
            .values("order_id")
            .distinct()
            .count()
        )

        # ChefReport signal cho dish
        dish_reports_qs = chef_reports_qs.filter(dish__uid=dish_uid)
        dish_report_count = dish_reports_qs.count()
        dish_report_sum = sum(r.credibility_weight for r in dish_reports_qs)

        # Review signal cho dish
        dish_review_sum, dish_review_count = _compute_review_signal(
            chef_id=chef_id, dish_uid=dish_uid, cutoff=cutoff
        )

        dish_combined = dish_report_sum + dish_review_sum
        dish_ratio = dish_combined / dish_orders if dish_orders else 0.0

        result.update(
            {
                "dish_uid": str(dish_uid),
                "dish_orders": dish_orders,
                "dish_report_count": dish_report_count,
                "dish_report_sum": round(dish_report_sum, 4),
                "dish_review_count": dish_review_count,
                "dish_review_sum": round(dish_review_sum, 4),
                "dish_combined": round(dish_combined, 4),
                "dish_ratio": round(dish_ratio, 4),
            }
        )

    return result


def decide_action(metrics: dict | None) -> dict:
    """
    Trả về quyết định: action (NONE/WARNING/DISH_LOCK/FULL_LOCK) + reason.

    Ưu tiên: FULL_LOCK > DISH_LOCK > WARNING > NONE.
    Điều kiện FULL_LOCK vẫn yêu cầu minimum ChefReport (không đủ chỉ bằng review signal).
    """
    if metrics is None:
        return {"action": "NONE", "reason": "Chưa đủ dữ liệu"}

    chef_ratio = metrics.get("chef_ratio", 0)
    chef_count = metrics.get("chef_report_count", 0)
    unique_reporters = metrics.get("unique_reporters", 0)
    review_count = metrics.get("review_count", 0)

    dish_ratio = metrics.get("dish_ratio", 0)
    dish_count = metrics.get("dish_report_count", 0)
    dish_orders = metrics.get("dish_orders", 0)

    if (
        chef_ratio >= FULL_LOCK_CHEF_RATIO
        and chef_count >= FULL_LOCK_MIN_REPORTS
        and unique_reporters >= FULL_LOCK_MIN_UNIQUE_REPORTERS
    ):
        return {
            "action": "FULL_LOCK",
            "reason": (
                f"Tỷ lệ phản ánh kết hợp {chef_ratio:.1%} vượt ngưỡng "
                f"{FULL_LOCK_CHEF_RATIO:.0%} — gồm {chef_count} phản ánh trực tiếp "
                f"từ {unique_reporters} khách khác nhau và {review_count} đánh giá "
                f"an toàn thực phẩm từ AI trong {REPORT_WINDOW_DAYS} ngày."
            ),
        }

    if (
        dish_orders >= MIN_COMPLETED_ORDERS_DISH
        and dish_ratio >= DISH_LOCK_RATIO
        and dish_count >= DISH_LOCK_MIN_REPORTS
    ):
        return {
            "action": "DISH_LOCK",
            "reason": (
                f"Tỷ lệ phản ánh kết hợp cho món này {dish_ratio:.1%} vượt ngưỡng "
                f"{DISH_LOCK_RATIO:.0%} — gồm {dish_count} phản ánh trực tiếp "
                f"trên {dish_orders} đơn trong {REPORT_WINDOW_DAYS} ngày."
            ),
        }

    if chef_ratio >= WARNING_CHEF_RATIO:
        return {
            "action": "WARNING",
            "reason": (
                f"Tỷ lệ phản ánh kết hợp {chef_ratio:.1%} chạm ngưỡng cảnh báo "
                f"{WARNING_CHEF_RATIO:.0%}. Vui lòng kiểm tra quy trình chế biến "
                f"và bảo quản thực phẩm."
            ),
        }

    return {"action": "NONE", "reason": ""}


# ── Delivery metrics ──────────────────────────────────────────────────────────

# Thresholds giao hàng — dùng cùng REPORT_WINDOW_DAYS
DELIVERY_MIN_COMPLETED_ORDERS = 20   # Cần ít nhất 20 đơn trước khi xét
DELIVERY_WARNING_RATIO = 0.05        # 5% → warning email chef
DELIVERY_ADMIN_ALERT_RATIO = 0.10    # 10% → admin alert + email chef

# Review delivery signal factor (thấp hơn food-safety vì ít nghiêm trọng hơn)
DELIVERY_REVIEW_SIGNAL_FACTOR = 0.25


def compute_delivery_metrics(chef_id: int) -> dict | None:
    """
    Tính tỉ lệ giao hàng sai/thiếu trong cửa sổ REPORT_WINDOW_DAYS.

    Kết hợp 2 nguồn:
      - ChefReport với category WRONG_ITEM / MISSING_ITEM
      - Review.issue thuộc DELIVERY_ISSUES ("giao sai", "giao thiếu", ...)
        dedup by order (1 đơn = 1 signal tối đa)

    Returns None nếu chưa đủ DELIVERY_MIN_COMPLETED_ORDERS đơn.
    """
    from django.db.models import Max
    from order.models import Order
    from report.models import ChefReport
    from review.models import Review

    cutoff = _window_cutoff()

    completed_orders = Order.objects.filter(
        chef_id=chef_id,
        status=OrderStatusEnum.COMPLETED,
        created_at__gte=cutoff,
    ).count()

    if completed_orders < DELIVERY_MIN_COMPLETED_ORDERS:
        return None

    # ChefReport signal (WRONG_ITEM + MISSING_ITEM)
    delivery_reports_qs = ChefReport.objects.filter(
        chef_id=chef_id,
        category__in=list(DELIVERY_CATEGORIES),
        created_at__gte=cutoff,
        deleted=False,
        status__in=[
            ReportStatusEnum.PENDING,
            ReportStatusEnum.REVIEWED,
            ReportStatusEnum.ACTED_ON,
        ],
    )
    report_count = delivery_reports_qs.count()
    report_weighted_sum = sum(r.credibility_weight for r in delivery_reports_qs)

    # Review signal — dedup by order
    review_qs = Review.objects.filter(
        dish__owner_id=chef_id,
        deleted=False,
        weight__gt=0,
        issue__in=list(DELIVERY_ISSUES),
        created_at__gte=cutoff,
    )
    order_groups = review_qs.values("order_id").annotate(max_weight=Max("weight"))
    review_signal_sum = sum(
        min(float(g["max_weight"]), 1.0) for g in order_groups
    ) * DELIVERY_REVIEW_SIGNAL_FACTOR
    review_order_count = order_groups.count()

    combined = report_weighted_sum + review_signal_sum
    delivery_ratio = combined / completed_orders if completed_orders else 0.0

    return {
        "completed_orders": completed_orders,
        "report_count": report_count,
        "report_weighted_sum": round(report_weighted_sum, 4),
        "review_order_count": review_order_count,
        "review_signal_sum": round(review_signal_sum, 4),
        "combined_weighted_sum": round(combined, 4),
        "delivery_ratio": round(delivery_ratio, 4),
        "window_days": REPORT_WINDOW_DAYS,
    }


def decide_delivery_action(metrics: dict | None) -> dict:
    """Quyết định hành động cho delivery metrics."""
    if metrics is None:
        return {"action": "NONE", "reason": "Chưa đủ dữ liệu"}

    ratio = metrics.get("delivery_ratio", 0)
    report_count = metrics.get("report_count", 0)

    if ratio >= DELIVERY_ADMIN_ALERT_RATIO and report_count >= 3:
        return {
            "action": "ADMIN_ALERT",
            "reason": (
                f"Tỷ lệ giao hàng sai/thiếu {ratio:.1%} vượt ngưỡng "
                f"{DELIVERY_ADMIN_ALERT_RATIO:.0%} — {report_count} phản ánh "
                f"trong {REPORT_WINDOW_DAYS} ngày."
            ),
        }

    if ratio >= DELIVERY_WARNING_RATIO:
        return {
            "action": "WARNING",
            "reason": (
                f"Tỷ lệ giao hàng sai/thiếu {ratio:.1%} chạm ngưỡng cảnh báo "
                f"{DELIVERY_WARNING_RATIO:.0%}. Vui lòng kiểm tra quy trình đóng gói."
            ),
        }

    return {"action": "NONE", "reason": ""}
