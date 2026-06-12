from typing import Optional, List
from ninja import ModelSchema, Schema
from certificate.models import Certificate, CertificateAttachment


class AttachmentDetailSchema(Schema):
    """Schema cho attachment trong certificate"""
    uid: str
    public_url: str
    original_name: str
    size: int
    content_type: str
    position: int


class CertificateResponse(ModelSchema):
    attachments: List[AttachmentDetailSchema] = []

    class Meta:
        model = Certificate
        exclude = [
            "created_at",
            "deleted",
            "name_no_accent",
        ]
    
    @staticmethod
    def resolve_attachments(obj):
        """Lấy tất cả attachments của certificate theo thứ tự"""
        cert_attachments = CertificateAttachment.objects.filter(
            certificate=obj
        ).select_related('attachment').order_by('position')
        
        return [
            {
                "uid": str(ca.attachment.uid),
                "public_url": ca.attachment.public_url,
                "original_name": ca.attachment.original_name,
                "size": ca.attachment.size,
                "content_type": ca.attachment.content_type,
                "position": ca.position,
            }
            for ca in cert_attachments
        ]
