from uuid import UUID

from ninja import Schema


class GeneratePresignedUrlResponse(Schema):
    uid: UUID
    url: str


class AttachmentResponse(Schema):
    uid: UUID
    original_name: str
    public_url: str
