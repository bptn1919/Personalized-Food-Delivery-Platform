from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0009_alter_authenticatetoken_token_hash'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='authenticatetoken',
            name='token_hash',
        ),
    ]
