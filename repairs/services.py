"""Service layer for repair operations.

Holds the transactional business logic for defect triage, repair orders,
and component replacements. Each state-changing public function takes
the necessary row locks, enforces RBAC, and writes audit logs so the API
remains consistent.
"""

import csv

from django.conf import settings
from django.db import transaction
from django.db.models import CharField, F, Value
from django.utils import timezone
from rest_framework.exceptions import PermissionDenied, ValidationError

from accounts.permissions import user_has_permission
from accounts.rbac import PERMISSION_REPAIRS_MANAGE, PERMISSION_REPAIRS_VERIFY
from accounts.tasks import send_email_task
from common.utils import EchoBuffer

from .models import (
    REPAIR_ORDER_TRANSITIONS,
    REPAIR_STATUS_TRANSITIONS,
    ComponentReplacement,
    DefectReport,
    RepairEvent,
    RepairOrder,
    RepairOrderStatus,
    RepairStatus,
)


def _get_authenticated_user(user):
    """Extract a valid user object or return None if unauthenticated.

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
    """Create a new DefectReport for a specific drone.

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
    """Safely update the status of a DefectReport and record an audit trail.

    Takes a row lock (select_for_update) to prevent race conditions where
    multiple technicians attempt concurrent updates. Validates the state
    machine and enforces RBAC (differentiating between normal progression
    and final verification). Asynchronously notifies the original reporter
    via email so they are informed of progress without blocking the request.
    """
    try:
        defect = DefectReport.objects.select_for_update().get(pk=defect_id)
    except DefectReport.DoesNotExist:
        raise ValidationError({"detail": "Defect report not found."})

    old_status = defect.status

    if old_status == new_status:
        raise ValidationError({"status": "The defect is already in this status."})

    allowed = REPAIR_STATUS_TRANSITIONS.get(old_status, [])
    if new_status not in allowed:
        raise ValidationError(
            {
                "status": f"Cannot transition from {old_status} to {new_status}. "
                f"Allowed: {[s.value for s in allowed]}"
            }
        )

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
    """Create a new actionable RepairOrder for a technician.

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
    """Safely transition a RepairOrder through its lifecycle states.

    Takes a row lock to prevent concurrent state drift. Enforces state
    machine logic and automatically stamps operational times (started_at,
    completed_at) to ensure accurate metrics.
    """
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
    """Record a physical hardware replacement on a drone.

    Used for standalone replacements not tied to a specific RepairOrder.
    Invokes model-level full_clean() to validate domain constraints
    (e.g., future dates) before saving to the database.
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
    """Record a hardware replacement as part of an active RepairOrder.

    Links the replacement to the repair order for historical grouping.
    Invokes model-level full_clean() to validate domain constraints
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
    """Aggregate a unified chronological timeline of all repair-related events.

    Queries distinct models (DefectReport, RepairEvent, RepairOrder,
    ComponentReplacement) and merges them into a single timeline sorted
    descending by timestamp. Querying separate models is more efficient
    here than creating a complex polymorphic query. Allows filtering by
    date range and event types.
    """

    allowed_types = set(event_types) if event_types else None
    querysets = []

    if not allowed_types or "defect" in allowed_types:
        qs = DefectReport.objects.filter(drone_id=drone_id)
        if date_from:
            qs = qs.filter(detected_at__gte=date_from)
        if date_to:
            qs = qs.filter(detected_at__lte=date_to)

        qs = qs.annotate(
            event_type=Value("defect", output_field=CharField()),
            timestamp=F("detected_at"),
            entity_id=F("id"),
        ).values("event_type", "timestamp", "entity_id")
        querysets.append(qs)

    if not allowed_types or "status_change" in allowed_types:
        qs = RepairEvent.objects.filter(defect_report__drone_id=drone_id)
        if date_from:
            qs = qs.filter(created_at__gte=date_from)
        if date_to:
            qs = qs.filter(created_at__lte=date_to)

        qs = qs.annotate(
            event_type=Value("status_change", output_field=CharField()),
            timestamp=F("created_at"),
            entity_id=F("id"),
        ).values("event_type", "timestamp", "entity_id")
        querysets.append(qs)

    if not allowed_types or "repair" in allowed_types:
        qs = RepairOrder.objects.filter(drone_id=drone_id)
        if date_from:
            qs = qs.filter(created_at__gte=date_from)
        if date_to:
            qs = qs.filter(created_at__lte=date_to)

        qs = qs.annotate(
            event_type=Value("repair", output_field=CharField()),
            timestamp=F("created_at"),
            entity_id=F("id"),
        ).values("event_type", "timestamp", "entity_id")
        querysets.append(qs)

    if not allowed_types or "replacement" in allowed_types:
        qs = ComponentReplacement.objects.filter(drone_id=drone_id)
        if date_from:
            qs = qs.filter(replaced_at__gte=date_from)
        if date_to:
            qs = qs.filter(replaced_at__lte=date_to)

        qs = qs.annotate(
            event_type=Value("replacement", output_field=CharField()),
            timestamp=F("replaced_at"),
            entity_id=F("id"),
        ).values("event_type", "timestamp", "entity_id")
        querysets.append(qs)

    if not querysets:
        return DefectReport.objects.none()

    return (
        querysets[0]
        .union(*querysets[1:])
        .order_by("-timestamp", "event_type", "entity_id")
    )


def hydrate_timeline_page(page_items):
    """Fetch full database records for a batch of timeline events and format them."""
    ids_by_type = {"defect": [], "status_change": [], "repair": [], "replacement": []}

    for item in page_items:
        ids_by_type[item["event_type"]].append(item["entity_id"])

    details_map = {}

    if ids_by_type["defect"]:
        for d in DefectReport.objects.filter(
            id__in=ids_by_type["defect"]
        ).select_related("reporter"):
            details_map[("defect", d.id)] = d

    if ids_by_type["status_change"]:
        for e in RepairEvent.objects.filter(
            id__in=ids_by_type["status_change"]
        ).select_related("technician"):
            details_map[("status_change", e.id)] = e

    if ids_by_type["repair"]:
        for r in RepairOrder.objects.filter(id__in=ids_by_type["repair"]):
            details_map[("repair", r.id)] = r

    if ids_by_type["replacement"]:
        for c in ComponentReplacement.objects.filter(id__in=ids_by_type["replacement"]):
            details_map[("replacement", c.id)] = c

    hydrated_data = []
    for item in page_items:
        obj = details_map.get((item["event_type"], item["entity_id"]))
        if not obj:
            continue

        if item["event_type"] == "defect":
            hydrated_data.append(
                {
                    "event_type": "defect",
                    "timestamp": item["timestamp"],
                    "summary": (
                        f"{obj.get_severity_display()} "
                        f"{obj.get_defect_type_display()} defect detected"
                    ),
                    "details": {
                        "id": obj.id,
                        "defect_type": obj.defect_type,
                        "severity": obj.severity,
                        "status": obj.status,
                        "description": obj.description,
                        "reporter": obj.reporter_id,
                    },
                }
            )
        if item["event_type"] == "status_change":
            hydrated_data.append(
                {
                    "event_type": "status_change",
                    "timestamp": item["timestamp"],
                    "summary": (
                        f"Defect #{obj.defect_report_id}: "
                        f"{obj.from_status} -> {obj.to_status}"
                    ),
                    "details": {
                        "id": obj.id,
                        "defect_report_id": obj.defect_report_id,
                        "from_status": obj.from_status,
                        "to_status": obj.to_status,
                        "action_taken": obj.action_taken,
                        "technician": obj.technician_id,
                    },
                }
            )
        if item["event_type"] == "repair":
            hydrated_data.append(
                {
                    "event_type": "repair",
                    "timestamp": item["timestamp"],
                    "summary": (
                        f"Repair order #{obj.pk} — " f"{obj.get_status_display()}"
                    ),
                    "details": {
                        "id": obj.id,
                        "status": obj.status,
                        "description": obj.description,
                        "assigned_to": obj.assigned_to_id,
                        "defect_report_id": obj.defect_report_id,
                    },
                }
            )
        if item["event_type"] == "replacement":
            old_sn = obj.old_serial_number or "N/A"
            hydrated_data.append(
                {
                    "event_type": "replacement",
                    "timestamp": item["timestamp"],
                    "summary": (
                        f"{obj.get_component_type_display()} replaced: "
                        f"{old_sn} -> {obj.new_serial_number}"
                    ),
                    "details": {
                        "id": obj.id,
                        "component_type": obj.component_type,
                        "old_serial_number": old_sn,
                        "new_serial_number": obj.new_serial_number,
                        "reason": obj.reason,
                        "repair_order_id": obj.repair_order_id,
                    },
                }
            )

    return hydrated_data


def iter_hydrated_timeline(queryset, chunk_size=1000):
    """Iterate over a timeline queryset, yielding fully hydrated events in chunks."""
    offset = 0
    while True:
        batch = list(queryset[offset : offset + chunk_size])

        if not batch:
            break

        hydrated_batch = hydrate_timeline_page(batch)

        for item in hydrated_batch:
            yield item

        offset += chunk_size


def generate_repair_history_csv(timeline_data):
    """Stream a CSV export of a drone's repair history timeline.

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
