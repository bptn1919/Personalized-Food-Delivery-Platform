from django.db import models
from utils.functions.remove_accents import remove_accents
from utils.enums import CertificateStatusEnum, CertificateTypeEnum
from utils.models import BaseModel
from utils.types import User
from django.db.models import Max

class Certificate(BaseModel):
    name = models.TextField()
    description = models.TextField(null=True, blank=True)
    issued_by = models.TextField()
    issue_date = models.DateField()
    expiration_date = models.DateField(null=True, blank=True)
    owner= models.ForeignKey(
        to=User,
        on_delete=models.SET_NULL,
        to_field="id",
        db_column="owner_id",
        related_name="certificate_fk_owner",
        db_constraint=True,
        null=True,
        blank=True,
    )  
    certificate_type = models.CharField(max_length=50, choices=CertificateTypeEnum.choices)
    status = models.CharField(max_length=50, choices=CertificateStatusEnum.choices, default=CertificateStatusEnum.PENDING)
    verified_by = models.ForeignKey(
        to=User,
        on_delete=models.SET_NULL,
        to_field="id",
        db_column="verified_by_id",
        related_name="certificate_fk_verified_by",
        db_constraint=True,
        null=True,
        blank=True,
    )

    verified_at = models.DateTimeField(null=True, blank=True)

    rejection_reason = models.TextField(null=True, blank=True)
    name_no_accent = models.TextField(blank=True, editable=False)
    deleted = models.BooleanField(default=False, null=False, blank=False)

    def save(self, *args, **kwargs):
        if self.name:
            self.name_no_accent = remove_accents(self.name)
        return super().save(*args, **kwargs)
    
    def __str__(self) -> str:
        return self.name

class CertificateAttachment(models.Model):
    certificate = models.ForeignKey(
        to=Certificate, 
        on_delete=models.CASCADE, 
        to_field="uid",
        db_column="certificate_uid",
        related_name="attachment_fk_certificate",
        db_constraint=True,
        null=False,
        blank=False,
    )
    attachment = models.ForeignKey(
        to="attachment.Attachment",
        on_delete=models.CASCADE,
        to_field="uid",
        db_column="attachment_uid",
        related_name="certificateattachment_fk_attachment",
        db_constraint=True,
        null=False,
        blank=False,
    )
    # thứ tự ảnh trong certificate
    position = models.PositiveIntegerField(default=0)
    # mỗi lần lưu là cộng thêm 1 vào position của ảnh mới, để đảm bảo ảnh mới luôn ở cuối
    def save(self, *args, **kwargs):
        if self._state.adding:  # ✅ đúng với UUID PK, vì UUID được tạo tự động khi tạo instance mới

            max_pos = CertificateAttachment.objects.filter(
                certificate=self.certificate
            ).aggregate(Max("position"))["position__max"]

            self.position = (max_pos or 0) + 1

        super().save(*args, **kwargs)
    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["certificate", "attachment"],
                name="unique_certificate_attachment"
            ),
            models.UniqueConstraint(
                fields=["certificate", "position"],
                name="unique_certificate_position"
            )
        ]