from typing import Optional
from uuid import UUID

from ninja import Schema
from pydantic import field_validator, model_validator

from utils.enums import ReportCategoryEnum, SuspensionTypeEnum


class CreateReportSchema(Schema):
    order_uid: Optional[UUID] = None  # Order.uid (BaseModel UUID primary key)
    chef_id: Optional[int] = None
    dish_uid: Optional[UUID] = None
    category: ReportCategoryEnum
    description: str
    evidence_uid: Optional[UUID] = None

    ORDER_REQUIRED_CATEGORIES = frozenset(
        [
            ReportCategoryEnum.FOOD_SAFETY,
            ReportCategoryEnum.FOOD_QUALITY,
            ReportCategoryEnum.HYGIENE,
            ReportCategoryEnum.WRONG_ITEM,
            ReportCategoryEnum.MISSING_ITEM,
            ReportCategoryEnum.PAYMENT_ISSUE,
            ReportCategoryEnum.REFUND_ISSUE,
        ]
    )
    PLATFORM_CATEGORIES = frozenset(
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
    PLATFORM_EVIDENCE_REQUIRED = PLATFORM_CATEGORIES

    @model_validator(mode="after")
    def validate_target(self):
        category = self.category
        if category in self.ORDER_REQUIRED_CATEGORIES:
            if not self.order_uid:
                raise ValueError("Phản ánh loại này yêu cầu order_uid.")
        else:
            if not self.order_uid and not self.chef_id and not self.dish_uid:
                raise ValueError("Phản ánh loại này cần chef_id hoặc dish_uid.")
            if category in self.PLATFORM_EVIDENCE_REQUIRED and not self.evidence_uid:
                raise ValueError("Phản ánh loại này yêu cầu ảnh bằng chứng.")
        return self

    @field_validator("description")
    @classmethod
    def description_not_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Mô tả không được để trống.")
        if len(v.strip()) < 10:
            raise ValueError("Mô tả cần ít nhất 10 ký tự.")
        return v.strip()


class SubmitAppealSchema(Schema):
    appeal_text: str

    @field_validator("appeal_text")
    @classmethod
    def text_not_empty(cls, v: str) -> str:
        if not v or len(v.strip()) < 20:
            raise ValueError("Giải trình cần ít nhất 20 ký tự.")
        return v.strip()


class LiftSuspensionSchema(Schema):
    lift_note: str = ""


class ManualSuspensionSchema(Schema):
    chef_id: int
    suspension_type: SuspensionTypeEnum
    dish_uid: Optional[UUID] = None
    reason: str

    @model_validator(mode="after")
    def validate_target(self):
        if self.suspension_type == SuspensionTypeEnum.DISH_LOCK and not self.dish_uid:
            raise ValueError("DISH_LOCK yêu cầu dish_uid.")
        if self.suspension_type == SuspensionTypeEnum.FULL_LOCK and self.dish_uid:
            raise ValueError("FULL_LOCK không được truyền dish_uid.")
        return self

    @field_validator("reason")
    @classmethod
    def reason_not_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Lý do không được để trống.")
        return v.strip()


class DismissReportSchema(Schema):
    admin_note: str = ""


class FilterReportSchema(Schema):
    chef_id: Optional[int] = None
    status: Optional[str] = None
    category: Optional[str] = None


class FilterSuspensionSchema(Schema):
    chef_id: Optional[int] = None
    status: Optional[str] = None
