from django.conf import settings
from django.core.mail import send_mail
from django.db import transaction
from rest_framework.exceptions import PermissionDenied, ValidationError

from roles.models import ADMIN_CODE, COMMANDER_CODE, TECHNICIAN_CODE

from .models import ComponentReplacement, DefectReport, RepairEvent, RepairStatus


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
def update_defect_status(
    *, defect: DefectReport, new_status: str, action_taken: str, user
):
    old_status = defect.status

    if old_status == new_status:
        raise ValidationError({"status": "The defect is already in this status."})

    if new_status == RepairStatus.VERIFIED and old_status != RepairStatus.FIXED:
        raise ValidationError(
            {"status": "A defect can only be verified if its current status is FIXED."}
        )

    role_code = (
        getattr(user.role, "code", None) if user and hasattr(user, "role") else None
    )

    if new_status in [RepairStatus.IN_PROGRESS, RepairStatus.FIXED]:
        if role_code not in [TECHNICIAN_CODE, COMMANDER_CODE, ADMIN_CODE]:
            raise PermissionDenied(
                "Only Technicians or Commanders can update repair status."
            )

    if new_status == RepairStatus.VERIFIED:
        if role_code not in [COMMANDER_CODE, ADMIN_CODE]:
            raise PermissionDenied("Only Commanders can verify repairs.")

    defect.status = new_status
    defect.save(update_fields=["status", "updated_at"])

    event = RepairEvent.objects.create(
        defect_report=defect,
        from_status=old_status,
        to_status=new_status,
        action_taken=action_taken,
        technician=_get_authenticated_user(user),
    )

    if new_status in [RepairStatus.IN_PROGRESS, RepairStatus.FIXED]:
        if defect.reporter and getattr(defect.reporter, "email", None):
            send_mail(
                subject=f"Status Update: Defect on {defect.drone}",
                message=(
                    f"The status of the defect you reported"
                    f" has changed to '{new_status}'.\n\n"
                    f"Action taken: {action_taken}"
                ),
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[defect.reporter.email],
                fail_silently=True,
            )

    return event


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
