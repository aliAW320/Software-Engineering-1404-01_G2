from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("tourism", "0003_populate_places"),
    ]

    operations = [
        migrations.AddField(
            model_name="user",
            name="core_user_id",
            field=models.CharField(max_length=64, unique=True, null=True, blank=True),
        ),
    ]
