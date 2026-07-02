import csv
from operator import itemgetter

from django.conf import settings
from django.core.mail import send_mail
from django.db import transaction
from django.utils import timezone
from rest_framework.exceptions import PermissionDenied, ValidationError

from accounts.permissions import user_has_permission
from accounts.rbac import PERMISSION_REPAIRS_MANAGE, PERMISSION_REPAIRS_VERIFY
from common.utils import EchoBuffer

from .models import (
    REPAIR_ORDER_TRANSITIONS,
    ComponentReplacement,
    DefectReport,
    RepairEvent,
    RepairOrder,
    RepairOrderStatus,
    RepairStatus,
)


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
def update_defect_status(*, defect_id: int, new_status: str, action_taken: str, user):
    try:
        defect = DefectReport.objects.select_for_update().get(pk=defect_id)
    except DefectReport.DoesNotExist:
        raise ValidationError({"detail": "Defect report not found."})
    old_status = defect.status

    if old_status == new_status:
        raise ValidationError({"status": "The defect is already in this status."})

    if new_status == RepairStatus.VERIFIED and old_status != RepairStatus.FIXED:
        raise ValidationError(
            {"status": "A defect can only be verified if its current status is FIXED."}
        )

    if new_status in [RepairStatus.IN_PROGRESS, RepairStatus.FIXED]:
        if not (
            user_has_permission(user, PERMISSION_REPAIRS_MANAGE)
            or user_has_permission(user, PERMISSION_REPAIRS_VERIFY)
        ):
            raise PermissionDenied(
                "Only Technicians or Commanders can update repair status."
            )

    if new_status == RepairStatus.VERIFIED:
        if not user_has_permission(user, PERMISSION_REPAIRS_VERIFY):
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
def create_repair_order(
    *,
    drone,
    description,
    defect_report=None,
    assigned_to=None,
    created_by=None,
):
    return RepairOrder.objects.create(
        drone=drone,
        description=description,
        defect_report=defect_report,
        assigned_to=_get_authenticated_user(assigned_to),
        created_by=_get_authenticated_user(created_by),
    )


@transaction.atomic
def update_repair_order_status(*, repair_order, new_status, user=None, notes=""):
    repair_order = RepairOrder.objects.select_for_update().get(pk=repair_order.pk)
    allowed = REPAIR_ORDER_TRANSITIONS.get(repair_order.status, [])
    if new_status not in allowed:
        raise ValueError(
            f"Cannot transition from {repair_order.status} to {new_status}. "
            f"Allowed transitions: {allowed}"
        )

    repair_order.status = new_status

    if new_status == RepairOrderStatus.IN_PROGRESS and not repair_order.started_at:
        repair_order.started_at = timezone.now()

    if new_status in (RepairOrderStatus.COMPLETED, RepairOrderStatus.CANCELLED):
        repair_order.completed_at = timezone.now()

    if notes:
        repair_order.notes = notes

    repair_order.save()
    return repair_order


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


@transaction.atomic
def add_component_replacement(
    *,
    repair_order,
    component_type,
    component_name,
    old_serial_number,
    new_serial_number,
    reason,
    replaced_at,
    replaced_by,
):
    replacement = ComponentReplacement(
        drone=repair_order.drone,
        repair_order=repair_order,
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


def get_drone_repair_history(
    drone_id,
    *,
    date_from=None,
    date_to=None,
    event_types=None,
):
    timeline = []

    allowed_types = set(event_types) if event_types else None

    if not allowed_types or "defect" in allowed_types:
        defects_qs = DefectReport.objects.filter(drone_id=drone_id)
        if date_from:
            defects_qs = defects_qs.filter(detected_at__gte=date_from)
        if date_to:
            defects_qs = defects_qs.filter(detected_at__lte=date_to)

        for d in defects_qs.select_related("reporter"):
            timeline.append(
                {
                    "event_type": "defect",
                    "timestamp": d.detected_at,
                    "summary": (
                        f"{d.get_severity_display()} "
                        f"{d.get_defect_type_display()} defect detected"
                    ),
                    "details": {
                        "id": d.id,
                        "defect_type": d.defect_type,
                        "severity": d.severity,
                        "status": d.status,
                        "description": d.description,
                        "reporter": d.reporter_id,
                    },
                }
            )

    if not allowed_types or "status_change" in allowed_types:
        events_qs = RepairEvent.objects.filter(defect_report__drone_id=drone_id)
        if date_from:
            events_qs = events_qs.filter(created_at__gte=date_from)
        if date_to:
            events_qs = events_qs.filter(created_at__lte=date_to)

        for e in events_qs.select_related("technician", "defect_report"):
            timeline.append(
                {
                    "event_type": "status_change",
                    "timestamp": e.created_at,
                    "summary": (
                        f"Defect #{e.defect_report_id}: "
                        f"{e.from_status} -> {e.to_status}"
                    ),
                    "details": {
                        "id": e.id,
                        "defect_report_id": e.defect_report_id,
                        "from_status": e.from_status,
                        "to_status": e.to_status,
                        "action_taken": e.action_taken,
                        "technician": e.technician_id,
                    },
                }
            )

    if not allowed_types or "repair" in allowed_types:
        repairs_qs = RepairOrder.objects.filter(drone_id=drone_id)
        if date_from:
            repairs_qs = repairs_qs.filter(created_at__gte=date_from)
        if date_to:
            repairs_qs = repairs_qs.filter(created_at__lte=date_to)

        for r in repairs_qs.select_related("assigned_to", "created_by"):
            timeline.append(
                {
                    "event_type": "repair",
                    "timestamp": r.created_at,
                    "summary": (f"Repair order #{r.pk} — " f"{r.get_status_display()}"),
                    "details": {
                        "id": r.id,
                        "status": r.status,
                        "description": r.description,
                        "assigned_to": r.assigned_to_id,
                        "defect_report_id": r.defect_report_id,
                    },
                }
            )

    if not allowed_types or "replacement" in allowed_types:
        replacements_qs = ComponentReplacement.objects.filter(
            drone_id=drone_id,
        )
        if date_from:
            replacements_qs = replacements_qs.filter(replaced_at__gte=date_from)
        if date_to:
            replacements_qs = replacements_qs.filter(replaced_at__lte=date_to)

        for c in replacements_qs.select_related("replaced_by"):
            old = c.old_serial_number or "N/A"
            timeline.append(
                {
                    "event_type": "replacement",
                    "timestamp": c.replaced_at,
                    "summary": (
                        f"{c.get_component_type_display()} replaced: "
                        f"{old} -> {c.new_serial_number}"
                    ),
                    "details": {
                        "id": c.id,
                        "component_type": c.component_type,
                        "old_serial_number": c.old_serial_number,
                        "new_serial_number": c.new_serial_number,
                        "reason": c.reason,
                        "repair_order_id": c.repair_order_id,
                    },
                }
            )

    timeline.sort(key=itemgetter("timestamp"), reverse=True)
    return timeline


def generate_repair_history_csv(timeline_data):
    buffer = EchoBuffer()
    writer = csv.writer(buffer)

    yield writer.writerow(
        [
            "Date",
            "Event Type",
            "Summary",
        ]
    )

    for event in timeline_data:
        yield writer.writerow(
            [
                event["timestamp"].strftime("%Y-%m-%d %H:%M:%S"),
                event["event_type"],
                event["summary"],
            ]
        )
