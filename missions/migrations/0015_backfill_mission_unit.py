from django.db import migrations


def backfill_mission_unit(apps, schema_editor):
    Mission = apps.get_model("missions", "Mission")

    missions_to_update = []
    for mission in Mission.objects.select_related("created_by", "commander").all():
        if mission.unit_id is not None:
            continue

        created_by = getattr(mission, "created_by", None)
        commander = getattr(mission, "commander", None)
        created_by_unit_id = getattr(created_by, "unit_id", None)
        commander_unit_id = getattr(commander, "unit_id", None)

        if (
            created_by_unit_id is not None
            and created_by_unit_id == commander_unit_id
        ):
            mission.unit_id = created_by_unit_id
            missions_to_update.append(mission)

    if missions_to_update:
        Mission.objects.bulk_update(missions_to_update, ["unit"])


class Migration(migrations.Migration):

    dependencies = [
        ("missions", "0014_mission_unit"),
    ]

    operations = [
        migrations.RunPython(
            backfill_mission_unit,
            reverse_code=migrations.RunPython.noop,
        ),
    ]
