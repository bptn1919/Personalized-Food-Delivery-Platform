from uuid import UUID

from utils.router.controller import Controller, api, post, put
from utils.types import AuthenticatedRequest

from .schemas.requests import GeneratePresignedUrlSchema
from .schemas.responses import GeneratePresignedUrlResponse
from .services import AttachmentService


@api(prefix_or_class="attachments", tags=["Attachments"])
class AttachmentController(Controller):
    def __init__(self, service: AttachmentService) -> None:
        self.service = service

    @post("presigned-url", response=GeneratePresignedUrlResponse)
    def get_presigned_url(
        self, request: AuthenticatedRequest, payload: GeneratePresignedUrlSchema
    ):
        attachment, presigned_url = self.service.get_presigned_url(
            user=request.user,
            payload=payload,
        )

        return {"uid": attachment.uid, "url": presigned_url}

    @put("/{uid}/completed/{instance_uid}", response=bool)
    def completed_upload(
        self, request: AuthenticatedRequest, uid: UUID, instance_uid: UUID
    ):
        return self.service.completed_upload(
            user=request.user, uid=uid, instance_uid=instance_uid
        )

    @put("/{uid}/completed", response=bool)
    def completed_upload_without_instance(
        self, request: AuthenticatedRequest, uid: UUID
    ):
        """Complete upload without linking to an instance yet"""
        return self.service.completed_upload(
            user=request.user, uid=uid, instance_uid=None
        )
