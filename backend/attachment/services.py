from uuid import UUID

import boto3
from botocore.client import Config
from django.conf import settings
from django.core.files import File
from django.db import transaction

from attachment.models import AttachmentType
from dish.orm import DishORM
from exceptions.attachments import AttachmentAlreadyCompleted, AttachmentNotFound, AttachmentIsNotCompleted
from exceptions.dishes import DishNotFoundException
from utils.services import BaseService
from utils.types import TUser

from .queries import Query
from .schemas.requests import GeneratePresignedUrlSchema
from .utils import Utils


class AttachmentService(BaseService):
    def __init__(self) -> None:
        self.query = Query()
        self.utils = Utils()
        self.dish_orm = DishORM()
        
        # Validate S3 configuration
        if not settings.USE_S3:
            raise RuntimeError("USE_S3 must be enabled for AttachmentService")
        
        required_settings = {
            'S3_ACCESS_KEY_ID': settings.S3_ACCESS_KEY_ID,
            'S3_SECRET_ACCESS_KEY': settings.S3_SECRET_ACCESS_KEY,
            'S3_BUCKET_NAME': settings.S3_BUCKET_NAME,
            'S3_REGION': settings.S3_REGION,
            'S3_PUBLIC_URL': settings.S3_PUBLIC_URL,
        }
        
        missing = [key for key, value in required_settings.items() if not value]
        if missing:
            raise RuntimeError(f"Missing S3 configuration: {', '.join(missing)}")
        
        # Initialize S3 client
        self.region = settings.S3_REGION
        self.bucket_name = settings.S3_BUCKET_NAME
        self.public_url = settings.S3_PUBLIC_URL.rstrip("/")
        self.expires_in = settings.S3_EXPIRES_IN
        
        self.s3_client = boto3.client(
            "s3",
            aws_access_key_id=settings.S3_ACCESS_KEY_ID,
            aws_secret_access_key=settings.S3_SECRET_ACCESS_KEY,
            region_name=self.region,
            config=Config(
                signature_version='s3v4',
                region_name=self.region
            )
        )

    def get_presigned_url(self, user: TUser, payload: GeneratePresignedUrlSchema):
        attachment = self.query.create_new_instance(
            type=payload.attachment_type,
            original_name=payload.file_name,
            hashed_name=self.utils.generate_hashed_name(payload.file_name),
            size=payload.file_size,
            content_type=self.utils.get_content_type(payload.file_name) or "",
            owner=user,
            bucket=self.bucket_name,
        )

        attachment.is_public = True
        attachment.public_url = (
            f"{self.public_url}/{attachment.directory}/{attachment.hashed_name}"
        )
        attachment.save()

        # Generate presigned URL for PUT (ACL will be set after upload)
        key = f"{attachment.directory}/{attachment.hashed_name}"
        presigned_url = self.s3_client.generate_presigned_url(
            ClientMethod="put_object",
            Params={
                "Bucket": self.bucket_name,
                "Key": key,
            },
            ExpiresIn=self.expires_in,
            HttpMethod="PUT",
        )

        return attachment, presigned_url

    @transaction.atomic
    def completed_upload(self, user: TUser, uid: UUID, instance_uid: UUID | None = None):
        attachment = self.query.get_instance_by_uid(uid=uid)

        if not attachment:
            raise AttachmentNotFound

        if attachment.is_completed:
            raise AttachmentAlreadyCompleted

        # Verify file exists on S3 before marking as completed
        key = f"{attachment.directory}/{attachment.hashed_name}"
        try:
            self.s3_client.head_object(Bucket=self.bucket_name, Key=key)
        except self.s3_client.exceptions.NoSuchKey:
            raise AttachmentNotFound("File not found on S3")
        except Exception as e:
            raise Exception(f"Error verifying file on S3: {str(e)}")

        # Note: Files are public via Bucket Policy, no need to set ACL
        # Bucket Policy should allow s3:GetObject for all objects

        # If instance_uid is provided, link attachment to the instance
        if instance_uid:
            if attachment.type == AttachmentType.DISH:
                dish = self.dish_orm.get_dish_by_uid(uid=instance_uid)

                if not dish:
                    raise DishNotFoundException

                if dish.attachment:
                    # TODO: remove old attachment
                    pass

                self.dish_orm.add_attachment(dish=dish, attachment=attachment)

        self.query.mark_as_completed(attachment=attachment, user=user)

        return True

    def post_file(self, user: TUser, file: File, type: AttachmentType):
        file_name = file.name or ""
        attachment = self.query.create_new_instance(
            type=type,
            original_name=file_name,
            hashed_name=self.utils.generate_hashed_name(file_name),
            size=file.size,
            content_type=self.utils.get_content_type(file_name) or "",
            owner=user,
            bucket=self.bucket_name,
        )
        attachment.is_public = True
        attachment.public_url = (
            f"{self.public_url}/{attachment.directory}/{attachment.hashed_name}"
        )
        attachment.save()

        self.s3_client.put_object(
            Bucket=self.bucket_name,
            Key=f"{attachment.directory}/{attachment.hashed_name}",
            Body=file,
            ContentType=attachment.content_type,
        )

        return attachment
    
    def handle_attachment(self, uid: UUID):
        attachment = self.query.get_instance_by_uid(uid=uid)

        if not attachment:
            raise AttachmentNotFound

        if not attachment.is_completed:
            raise AttachmentIsNotCompleted("Attachment upload chưa hoàn tất. Vui lòng gọi PUT /attachments/{uid}/completed trước.")
        
        return attachment
   