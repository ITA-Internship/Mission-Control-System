"""Service layer for repair operations.

Holds the transactional business logic for defect triage, repair orders,
and component replacements. Each state-changing public function takes
the necessary row locks, enforces RBAC, and writes audit logs so the API
remains consistent.
"""

import csv
from operator import itemgetter

from django.conf import settings
from django.db import transaction
from django.utils import timezone
from rest_framework.exceptions import PermissionDenied, ValidationError

from accounts.permissions import user_has_permission
from accounts.rbac import PERMISSION_REPAIRS_MANAGE, PERMISSION_REPAIRS_VERIFY
from accounts.tasks import send_email_task
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
    """
    Extract a valid user object or return None if unauthenticated.

    Prevents AnonymousUser instances from being incorrectly assigned
    to ForeignKey fields in the database.
    """
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
    """
    Create a new DefectReport for a specific drone.

    Acts as the entry point for the repair lifecycle. Automatically links
    the reporter if they are an authenticated user.
    """
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
    """
    Safely update the status of a DefectReport and record an audit trail.

    Takes a row lock to prevent concurrent updates, validates the state
    machine, enforces RBAC, and triggers email notifications.
    """
    try:
        # Lock the row to prevent race conditions where two technicians
        # try to transition the same defect simultaneously.
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

    # RBAC Enforcement: Differentiate between normal progression and final verification.
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

    # Asynchronously notify the original reporter so they aren't left in the dark,
    # without blocking the HTTP response for the technician.
    if new_status in [RepairStatus.IN_PROGRESS, RepairStatus.FIXED]:
        if defect.reporter and getattr(defect.reporter, "email", None):
            send_email_task.delay(
                subject=f"Status Update: Defect on {defect.drone}",
                message=(
                    f"The status of the defect you reported"
                    f" has changed to '{new_status}'.\n\n"
                    f"Action taken: {action_taken}"
                ),
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[defect.reporter.email],
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
    """
    Create a new actionable RepairOrder for a technician.

    Can be created standalone for routine maintenance or linked to an
    existing DefectReport.
    """
    return RepairOrder.objects.create(
        drone=drone,
        description=description,
        defect_report=defect_report,
        assigned_to=_get_authenticated_user(assigned_to),
        created_by=_get_authenticated_user(created_by),
    )


@transaction.atomic
def update_repair_order_status(*, repair_order, new_status, user=None, notes=""):
    """
    Safely transition a RepairOrder through its lifecycle states.

    Enforces state machine logic and automatically handles timestamps.
    """
    # Lock the row to prevent concurrent state drift.
    repair_order = RepairOrder.objects.select_for_update().get(pk=repair_order.pk)

    allowed = REPAIR_ORDER_TRANSITIONS.get(repair_order.status, [])
    if new_status not in allowed:
        raise ValueError(
            f"Cannot transition from {repair_order.status} to {new_status}. "
            f"Allowed transitions: {allowed}"
        )

    repair_order.status = new_status

    # Automatically stamp operational times to ensure accurate metrics.
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
    """
    Record a physical hardware replacement on a drone.

    Used for standalone replacements not tied to a specific RepairOrder.
    Invokes model-level `full_clean()` to validate domain constraints
    before saving to the database.
    """
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
    # Explicitly call full_clean to trigger model-level validation (e.g. future dates).
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
    """
    Record a hardware replacement as part of an active RepairOrder.

    Links the replacement to the repair order for historical grouping.
    Invokes model-level `full_clean()` to validate domain constraints
    before saving to the database.
    """
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
    """
    Aggregate a unified chronological timeline of all repair-related events.

    Queries four different models (DefectReport, RepairEvent, RepairOrder,
    ComponentReplacement) and merges them into a single timeline sorted
    descending by timestamp. Allows filtering by date range and event types.
    """
    timeline = []

    allowed_types = set(event_types) if event_types else None

    # Querying separate models to build a unified timeline is more efficient here
    # than creating a complex polymorphic query, as each event type has unique details.

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
    """
    Stream a CSV export of a drone's repair history timeline.

    Uses a generator pattern with EchoBuffer to allow efficient streaming
    of large timelines over HTTP without loading the entire file in memory.
    """
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
