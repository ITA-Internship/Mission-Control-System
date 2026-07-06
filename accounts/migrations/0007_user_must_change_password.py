from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0006_alter_userprofile_profile_picture"),
    ]

    operations = [
        migrations.AddField(
            model_name="user",
            name="must_change_password",
            field=models.BooleanField(default=False),
        ),
    ]
