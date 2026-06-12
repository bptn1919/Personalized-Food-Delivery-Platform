from datetime import datetime
from typing import Optional
from uuid import UUID

from ninja import Schema


class ReportSchema(Schema):
    uid: UUID
    chef_id: int
    order_id: Optional[int]
    dish_uid: Optional[UUID]
    category: str
    description: str
    credibility_weight: float
    ai_severity: Optional[str]
    ai_food_safety_risk: Optional[bool]
    ai_severity_reason: Optional[str]
    status: str
    admin_note: Optional[str]
    created_at: datetime

    @staticmethod
    def from_orm_dish_uid(report):
        return {
            "uid": report.uid,
            "chef_id": report.chef_id,
            "order_id": report.order_id,
            "dish_uid": report.dish.uid if report.dish else None,
            "category": report.category,
            "description": report.description,
            "credibility_weight": report.credibility_weight,
            "ai_severity": report.ai_severity,
            "ai_food_safety_risk": report.ai_food_safety_risk,
            "ai_severity_reason": report.ai_severity_reason,
            "status": report.status,
            "admin_note": report.admin_note,
            "created_at": report.created_at,
        }


class SuspensionSchema(Schema):
    uid: UUID
    chef_id: int
    suspension_type: str
    locked_dish_uid: Optional[UUID]
    reason: str
    trigger_source: str
    trigger_data: dict
    status: str
    appeal_text: Optional[str]
    appealed_at: Optional[datetime]
    lift_note: Optional[str]
    lifted_at: Optional[datetime]
    created_at: datetime


class WarningSchema(Schema):
    uid: UUID
    chef_id: int
    warned_dish_uid: Optional[UUID]
    metrics_snapshot: dict
    email_sent: bool
    created_at: datetime


class ChefSuspensionStatusSchema(Schema):
    """Response cho chef xem trạng thái khóa hiện tại."""
    is_accepting_orders: bool
    suspension_level: str
    active_suspension: Optional[SuspensionSchema]
