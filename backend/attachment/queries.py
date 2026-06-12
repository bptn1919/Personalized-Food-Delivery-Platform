from uuid import UUID

from utils.types import TUser

from .models import Attachment, AttachmentType


class Query:
    def create_new_instance(
        self,
        type: AttachmentType,
        original_name: str,
        hashed_name: str,
        size: int,
        content_type: str,
        owner: TUser,
        bucket: str,
    ):
        return Attachment.objects.create(
            original_name=original_name,
            hashed_name=hashed_name,
            size=size,
            type=type,
            content_type=content_type,
            owner=owner,
            is_public=True,
            bucket=bucket,
        )

    def get_instance_by_uid(self, uid: UUID):
        try:
            return Attachment.objects.get(
                uid=uid, is_deleted=False, is_file_deleted=False
            )
        except Attachment.DoesNotExist:
            return None

    def mark_as_completed(self, attachment: Attachment, user: TUser):
        attachment.is_completed = True
        attachment.updater = user
        attachment.save()
        return attachment
