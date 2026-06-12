"""
Management command: xóa các file S3 đã đến hạn (theo ScheduledS3Deletion).

Chạy hàng ngày qua cron:
    0 3 * * * cd /app && python manage.py delete_scheduled_s3

Chạy tay:
    python manage.py delete_scheduled_s3
    python manage.py delete_scheduled_s3 --dry-run   # xem trước, không xóa thật
"""

import logging

import boto3
from django.conf import settings
from django.core.management.base import BaseCommand
from django.utils.timezone import now

logger = logging.getLogger("django")


class Command(BaseCommand):
    help = "Xóa các file S3 đã đến hạn lên lịch (ScheduledS3Deletion)"

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="In danh sách sẽ xóa mà không thực sự xóa",
        )

    def handle(self, *args, **options):
        from verification.models import ScheduledS3Deletion

        dry_run: bool = options["dry_run"]
        pending = ScheduledS3Deletion.objects.filter(
            is_executed=False,
            delete_after__lte=now(),
        )

        count = pending.count()
        if count == 0:
            self.stdout.write("Không có file nào cần xóa.")
            return

        self.stdout.write(f"Tìm thấy {count} file cần xóa{' (dry-run)' if dry_run else ''}.")

        if not getattr(settings, "USE_S3", False):
            self.stdout.write(self.style.WARNING("USE_S3=False — bỏ qua xóa S3."))
            if not dry_run:
                pending.update(is_executed=True, executed_at=now())
            return

        s3 = boto3.client(
            "s3",
            aws_access_key_id=settings.S3_ACCESS_KEY_ID,
            aws_secret_access_key=settings.S3_SECRET_ACCESS_KEY,
            region_name=settings.S3_REGION,
        )

        deleted = 0
        failed = 0

        for record in pending.iterator():
            self.stdout.write(f"  {'[DRY-RUN] Would delete' if dry_run else 'Deleting'}: "
                              f"s3://{record.s3_bucket}/{record.s3_key}")
            if dry_run:
                continue

            try:
                s3.delete_object(Bucket=record.s3_bucket, Key=record.s3_key)

                # Đánh dấu Attachment là đã xóa file
                try:
                    from attachment.models import Attachment
                    Attachment.objects.filter(uid=record.attachment_uid).update(
                        is_file_deleted=True,
                        is_deleted=True,
                    )
                except Exception as exc:
                    logger.warning("Could not mark Attachment %s as deleted: %s", record.attachment_uid, exc)

                record.is_executed = True
                record.executed_at = now()
                record.save(update_fields=["is_executed", "executed_at"])
                deleted += 1
                logger.info("Deleted scheduled S3 file: %s/%s", record.s3_bucket, record.s3_key)

            except Exception as exc:
                failed += 1
                logger.error("Failed to delete %s/%s: %s", record.s3_bucket, record.s3_key, exc)

        if not dry_run:
            self.stdout.write(self.style.SUCCESS(
                f"Hoàn thành: {deleted} đã xóa, {failed} lỗi."
            ))
