import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("drones", "0015_remove_dronestatushistory_related_repair_order_id"),
        ("repairs", "0002_componentreplacement"),
        ("repairs", "0003_componentreplacement_component_name_nullable"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="RepairOrder",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("PENDING", "Pending"),
                            ("IN_PROGRESS", "In progress"),
                            ("COMPLETED", "Completed"),
                            ("CANCELLED", "Cancelled"),
                        ],
                        db_index=True,
                        default="PENDING",
                        max_length=20,
                    ),
                ),
                ("description", models.TextField()),
                ("started_at", models.DateTimeField(blank=True, null=True)),
                ("completed_at", models.DateTimeField(blank=True, null=True)),
                ("notes", models.TextField(blank=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "assigned_to",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="assigned_repairs",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "created_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="created_repairs",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "defect_report",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="repair_orders",
                        to="repairs.defectreport",
                    ),
                ),
                (
                    "drone",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="repair_orders",
                        to="drones.drone",
                    ),
                ),
            ],
            options={
                "db_table": "repair_orders",
                "ordering": ("-created_at",),
            },
        ),
        migrations.AddIndex(
            model_name="repairorder",
            index=models.Index(
                fields=["drone", "-created_at"], name="repair_drone_created_idx"
            ),
        ),
        migrations.AddIndex(
            model_name="repairorder",
            index=models.Index(fields=["status"], name="repair_status_idx"),
        ),
    ]
