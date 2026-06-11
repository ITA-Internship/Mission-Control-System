from django.db import transaction

from .models import DefectReport


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
