from __future__ import annotations

import datetime as dt
from typing import Optional

from django.db.models import Count, Q
from django.db.models.functions import TruncDate
from django.utils import timezone

from review.schemas.responses import ReviewResponse
from review.schemas.requests import FilterIssueReviewSchema
from review.models import Review
from utils.types import TUser


class AnalyticsService:
    TREND_DAYS = 14
    TOP_DISH_DAYS = 30
    HEATMAP_DAYS = 30
    TOP_DISH_LIMIT = 5

    def issue_trend(
        self,
        user: TUser,
        range_start: dt.date | None = None,
        range_end: dt.date | None = None,
        filter: Optional[FilterIssueReviewSchema] = None,
    ):
        """Biểu đồ issue theo thời gian cho chef."""
        chef_id = self._get_user_id(user)
        start_date, end_date = self._resolve_date_range(range_start, range_end, self.TREND_DAYS)
        start_at = timezone.make_aware(dt.datetime.combine(start_date, dt.time.min))
        end_at = timezone.make_aware(dt.datetime.combine(end_date, dt.time.max))

        rows = list(
            self._base_issue_queryset(chef_id, start_at, end_at, filter=filter)
            .annotate(day=TruncDate("created_at"))
            .values("issue", "day")
            .annotate(count=Count("uid"))
            .order_by("day", "issue")
        )

        date_points = self._date_range(start_date, end_date)
        issues = sorted({row["issue"] for row in rows}, key=str.lower)
        counts = {(row["issue"], row["day"]): row["count"] for row in rows}

        trend: dict[str, list[dict[str, int | str]]] = {}
        for issue in issues:
            trend[issue] = [
                {
                    "date": day.isoformat(),
                    "count": int(counts.get((issue, day), 0)),
                }
                for day in date_points
            ]

        return {
            "range_start": start_date,
            "range_end": end_date,
            "issues": trend,
        }

    def top_complained_dishes(self, user: TUser, range_start: dt.date | None = None, range_end: dt.date | None = None, limit: int | None = None):
        """Top món bị complain nhiều nhất cho chef."""
        chef_id = self._get_user_id(user)
        start_date, end_date = self._resolve_date_range(range_start, range_end, self.TOP_DISH_DAYS)
        end_at = timezone.make_aware(dt.datetime.combine(end_date, dt.time.max))
        start_at = timezone.make_aware(dt.datetime.combine(start_date, dt.time.min))
        top_limit = limit or self.TOP_DISH_LIMIT

        rows = list(
            self._base_issue_queryset(chef_id, start_at, end_at)
            .values("dish__uid", "dish__name")
            .annotate(count=Count("uid"))
            .order_by("-count", "dish__name")[: top_limit]
        )

        return {
            "range_start": start_date,
            "range_end": end_date,
            "limit": top_limit,
            "items": [
                {
                    "dish_uid": row["dish__uid"],
                    "dish_name": row["dish__name"],
                    "count": int(row["count"]),
                }
                for row in rows
            ],
        }

    def issue_heatmap(
        self,
        user: TUser,
        range_start: dt.date | None = None,
        range_end: dt.date | None = None,
        filter: Optional[FilterIssueReviewSchema] = None,
    ):
        """Heatmap issue theo món và loại issue cho chef."""
        chef_id = self._get_user_id(user)
        start_date, end_date = self._resolve_date_range(range_start, range_end, self.HEATMAP_DAYS)
        start_at = timezone.make_aware(dt.datetime.combine(start_date, dt.time.min))
        end_at = timezone.make_aware(dt.datetime.combine(end_date, dt.time.max))

        rows = list(
            self._base_issue_queryset(chef_id, start_at, end_at, filter=filter)
            .values("dish__name", "issue")
            .annotate(count=Count("uid"))
            .order_by("dish__name", "issue")
        )

        heatmap: dict[str, dict[str, int]] = {}
        for row in rows:
            dish_name = row["dish__name"]
            issue = row["issue"]
            heatmap.setdefault(dish_name, {})[issue] = int(row["count"])

        return {
            "range_start": start_date,
            "range_end": end_date,
            "heatmap": heatmap,
        }

    @staticmethod
    def _get_user_id(user: TUser) -> int:
        return user.id if hasattr(user, "id") else user.pk

    @staticmethod
    def _base_issue_queryset(
        chef_id: int,
        start_at,
        end_at,
        filter: Optional[FilterIssueReviewSchema] = None,
    ):
        qs = Review.objects.filter(
            dish__owner_id=chef_id,
            deleted=False,
            weight__gt=0,
            issue__isnull=False,
            created_at__gte=start_at,
            created_at__lt=end_at,
        ).exclude(issue="")

        if filter:
            qs = qs.filter(filter.get_filter_expression())
        return qs

    # @staticmethod
    # def _build_filter_q(filter: FilterIssueReviewSchema) -> Q:
    #     q = Q()

    #     q &= filter.filter_dish_uid(filter.dish_uid)
    #     q &= filter.filter_menu_uid(filter.menu_uid)
    #     q &= filter.filter_search(filter.search)
    #     q &= filter.filter_categories(filter.categories)

    #     return q

    @staticmethod
    def _date_range(start_date, end_date):
        days = (end_date - start_date).days
        return [start_date + dt.timedelta(days=index) for index in range(days + 1)]

    @staticmethod
    def _resolve_date_range(range_start: dt.date | None, range_end: dt.date | None, default_days: int):
        end_date = range_end or timezone.localdate()
        start_date = range_start or (end_date - dt.timedelta(days=default_days))
        if start_date > end_date:
            raise ValueError("range_start must be less than or equal to range_end")
        return start_date, end_date
    
    def get_reviews_by_issue_for_chef(
        self,
        *,
        user: TUser,
        issue: str,
        filter: Optional[FilterIssueReviewSchema] = None,
        range_start: dt.date | None = None,
        range_end: dt.date | None = None,
    ):
        chef_id = self._get_user_id(user)

        start_date, end_date = self._resolve_date_range(
            range_start, range_end, self.HEATMAP_DAYS
        )

        start_at = timezone.make_aware(dt.datetime.combine(start_date, dt.time.min))
        end_at = timezone.make_aware(dt.datetime.combine(end_date, dt.time.max))

        from review.orm.review import ReviewORM

        qs = ReviewORM().get_reviews_from_issue(
            chef_id=chef_id,
            issue=issue,
            start_at=start_at,
            end_at=end_at,
            filter=filter,
        )

        # 🚀 GROUP THEO DISH (quan trọng)
        dish_map: dict[str, dict] = {}
        total_reviews = 0

        for review in qs:
            dish = review.dish
            dish_uid = str(dish.uid)

            if dish_uid not in dish_map:
                dish_map[dish_uid] = {
                    "dish_info": {
                        "uid": dish.uid,
                        "name": dish.name,
                        "category": dish.category,
                        "price": float(dish.price),
                    },
                    "reviews": [],
                }

            dish_map[dish_uid]["reviews"].append(review)
            total_reviews += 1

        return {
            "range_start": start_date,
            "range_end": end_date,
            "issue": issue,
            "total_reviews": total_reviews,
            "reviews": list(dish_map.values()),
        }