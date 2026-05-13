from django.db import migrations


def seed_default_roles(apps, schema_editor):
    Role = apps.get_model("roles", "Role")

    default_roles = [
        {
            "code": "ADMIN",
            "name": "Admin",
            "description": "Full system access, including user and role management.",
        },
        {
            "code": "COMMANDER",
            "name": "Commander",
            "description": "Oversight role with management and coordination responsibilities.",
        },
        {
            "code": "OPERATOR",
            "name": "Operator",
            "description": "Operational role responsible for mission execution workflows.",
        },
        {
            "code": "TECHNICIAN",
            "name": "Technician",
            "description": "Technical role responsible for maintenance and repair workflows.",
        },
        {
            "code": "VIEWER",
            "name": "Viewer",
            "description": "Read-only access to system data.",
        },
        {
            "code": "DISPATCHER",
            "name": "Dispatcher",
            "description": "Coordinates drone and operator assignments to missions.",
        },
    ]

    for role_data in default_roles:
        Role.objects.update_or_create(
            code=role_data["code"],
            defaults={
                "name": role_data["name"],
                "description": role_data["description"],
            },
        )


def remove_default_roles(apps, schema_editor):
    Role = apps.get_model("roles", "Role")
    Role.objects.filter(
        code__in=[
            "ADMIN",
            "COMMANDER",
            "OPERATOR",
            "TECHNICIAN",
            "VIEWER",
            "DISPATCHER",
        ]
    ).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("roles", "0002_alter_role_code"),
    ]

    operations = [
        migrations.RunPython(seed_default_roles, remove_default_roles),
    ]
