from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('profile', '0003_remove_chefprofile_file_remove_customerprofile_file_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='chefpaymentinfo',
            name='bank_code',
            field=models.CharField(default='', help_text='Mã BIN/Bank code dùng cho payout', max_length=20),
            preserve_default=False,
        ),
    ]
