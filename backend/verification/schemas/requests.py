from uuid import UUID
from typing import Annotated
from ninja import Schema
from pydantic import field_validator


class AnalyzeDocumentRequest(Schema):
    """Dùng cho ĐKKD, ATTP (có thể nhiều trang)."""
    attachment_uids: list[UUID]

    @field_validator("attachment_uids")
    @classmethod
    def validate_uids(cls, v):
        if not v:
            raise ValueError("Cần ít nhất 1 ảnh.")
        if len(v) > 10:
            raise ValueError("Tối đa 10 ảnh mỗi lần upload.")
        return v


class AnalyzeCCCDRequest(Schema):
    """CCCD bắt buộc đúng 2 ảnh: [mặt trước, mặt sau]."""
    attachment_uids: list[UUID]

    @field_validator("attachment_uids")
    @classmethod
    def validate_cccd(cls, v):
        if len(v) != 2:
            raise ValueError("CCCD yêu cầu đúng 2 ảnh: ảnh mặt trước và ảnh mặt sau.")
        return v


class AnalyzeSelfieRequest(Schema):
    """Selfie luôn là 1 ảnh duy nhất."""
    attachment_uid: UUID
