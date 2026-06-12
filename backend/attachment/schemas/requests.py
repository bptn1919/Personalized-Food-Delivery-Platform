from ninja import Schema

from attachment.models import AttachmentType


class GeneratePresignedUrlSchema(Schema):
    file_name: str
    file_size: int
    attachment_type: AttachmentType
