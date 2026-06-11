from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("missions", "0007_mission_incident_notes"),
    ]

    operations = [
        migrations.AlterField(
            model_name="missiondrone",
            name="condition_after",
            field=models.CharField(
                blank=True,
                choices=[
                    ("ok", "Ok"),
                    ("damaged", "Damaged"),
                    ("lost", "Lost"),
                ],
                max_length=20,
                null=True,
            ),
        ),
    ]
