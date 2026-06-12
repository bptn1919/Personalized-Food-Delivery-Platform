from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('verification', '0002_remove_chefverificationsession_business_attachment_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='ScheduledS3Deletion',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('attachment_uid', models.UUIDField(db_index=True)),
                ('s3_bucket', models.CharField(max_length=255)),
                ('s3_key', models.TextField()),
                ('delete_after', models.DateTimeField(db_index=True)),
                ('is_executed', models.BooleanField(db_index=True, default=False)),
                ('executed_at', models.DateTimeField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'verbose_name': 'Scheduled S3 Deletion',
                'verbose_name_plural': 'Scheduled S3 Deletions',
                'indexes': [
                    models.Index(fields=['is_executed', 'delete_after'], name='verification_sched_idx'),
                ],
            },
        ),
    ]
