from typing import Optional, List

from django.db.models import Q
from ninja import FilterSchema

from utils.enums import CertificateTypeEnum, CertificateStatusEnum
from utils.functions.remove_accents import remove_accents
from utils.schemas.fields import FilterField
from uuid import UUID
from ninja import Schema


class CertificateSchema(Schema):
    """Schema cho tạo/update certificate - KHÔNG có attachment_uids (quản lý ảnh riêng qua endpoints khác)"""
    name: str
    description: Optional[str] = None
    issued_by: str
    issue_date: str  # ISO format date string
    expiration_date: Optional[str] = None  # ISO format date string
    certificate_type: CertificateTypeEnum


class CertificateAttachmentSchema(Schema):
    """Schema cho thêm attachments vào certificate"""
    attachment_uids: List[UUID]


class CertificateAttachmentReorderSchema(Schema):
    attachment_uid: UUID
    position: int

# class CertificateAttachmentReorderSchema(Schema):
#     items: list[CertificateAttachmentReorderItem]

class SetCertificateStatusSchema(Schema):
    """Schema cho việc set status của certificate"""
    status: CertificateStatusEnum
    rejection_reason: Optional[str] = None  # Bắt buộc khi status = REVOKED

class BaseCertificateFilterSchema(FilterSchema):
    search: Optional[str] = FilterField(default=None)
    status: Optional[str] = FilterField(
        default=None,
        description="Certificate status",
        json_schema_extra={"enum": [e.value for e in CertificateStatusEnum]},
    )
    categories: Optional[str] = FilterField(
        default=None,
        description="Comma-separated list of categories",
        json_schema_extra={"enum": [e.value for e in CertificateTypeEnum]},
    )

    def filter_search(self, value: Optional[str]):
        if value is None:
            return Q()
        return Q(name_no_accent__icontains=remove_accents(value))

    def filter_status(self, value: Optional[str]):
        if value is None or value == "all":
            return Q()
        return Q(status=value)

    def filter_categories(self, value: Optional[str]):
        if value is None:
            return Q()
        return Q(certificate_type__in=value.split(","))

class AdminFilterCertificateSchema(BaseCertificateFilterSchema):
    chef_id: Optional[int] = FilterField(default=None, description="Filter by chef id")

    def filter_chef_id(self, value: Optional[int]):
        if value is None:
            return Q()
        return Q(owner_id=value)
