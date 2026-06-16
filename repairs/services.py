from django.db import transaction

from .models import ComponentReplacement, DefectReport


def _get_authenticated_user(user):
    if user and getattr(user, "is_authenticated", False):
        return user
    return None


@transaction.atomic
def create_defect_report(
    *,
    drone,
    reporter,
    defect_type,
    severity,
    description,
    detected_at,
):
    return DefectReport.objects.create(
        drone=drone,
        reporter=_get_authenticated_user(reporter),
        defect_type=defect_type,
        severity=severity,
        description=description,
        detected_at=detected_at,
    )


@transaction.atomic
def create_component_replacement(
    *,
    drone,
    component_type,
    component_name,
    old_serial_number,
    new_serial_number,
    reason,
    replaced_at,
    replaced_by,
):
    replacement = ComponentReplacement(
        drone=drone,
        component_type=component_type,
        component_name=component_name,
        old_serial_number=old_serial_number,
        new_serial_number=new_serial_number,
        reason=reason,
        replaced_at=replaced_at,
        replaced_by=_get_authenticated_user(replaced_by),
    )
    replacement.full_clean()
    replacement.save()
    return replacement
