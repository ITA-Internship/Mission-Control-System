from django.contrib.auth import get_user_model
from django.db import transaction
from django.db.models import Q
from django.utils import timezone
from rest_framework import serializers

from drones.models import Drone
from drones.services import update_drone

from .models import AuditLog, Condition, Mission, MissionDrone, Status

CONDITION_TO_DRONE_STATUS = {
    Condition.OK: Drone.STATUS_ACTIVE,
    Condition.DAMAGED: Drone.STATUS_DAMAGED,
    Condition.LOST: Drone.STATUS_WRITTEN_OFF,
}

User = get_user_model()


def _check_overlap(mission, operator=None, drone=None):
    """Check whether a drone or operator has a scheduling conflict
    with another PLANNED / ACTIVE mission.

    Requires that ``mission.started_at`` is set (the caller must
    validate this before invoking the helper).
    """
    if not operator and not drone:
        return False

    overlapping = MissionDrone.objects.filter(
        mission__status__in=[Status.ACTIVE, Status.PLANNED],
    ).exclude(mission=mission)

    if operator:
        overlapping = overlapping.filter(operator=operator)
    if drone:
        overlapping = overlapping.filter(drone=drone)

    m_start = mission.started_at
    m_end = mission.ended_at

    q_objects = Q()
    if m_end:
        q_objects &= Q(mission__started_at__lt=m_end)
    q_objects &= Q(mission__ended_at__isnull=True) | Q(
        mission__ended_at__gt=m_start,
    )

    return overlapping.filter(q_objects).exists()


def assign_drone_to_mission(
    *,
    mission,
    drone,
    operator,
    action_user=None,
    extra_fields=None,
):
    """Assign a drone + operator to a mission inside a single
    ``SELECT … FOR UPDATE`` transaction that eliminates TOCTOU races.

    Returns the created ``MissionDrone`` instance.
    """
    with transaction.atomic():
        # Lock all three rows to prevent concurrent mutations.
        locked_mission = Mission.objects.select_for_update().get(
            id=mission.id,
        )
        if locked_mission.status != Status.PLANNED:
            raise serializers.ValidationError(
                {"mission": "Assignments can only be added to planned missions."},
            )

        if not locked_mission.started_at:
            raise serializers.ValidationError(
                {
                    "mission": (
                        "Mission must have a start time before "
                        "assigning drones or operators."
                    ),
                },
            )

        locked_drone = Drone.objects.select_for_update().get(id=drone.id)
        if locked_drone.status != Drone.STATUS_ACTIVE:
            raise serializers.ValidationError(
                {"drone": "Drone is no longer active."},
            )

        locked_operator = User.objects.select_for_update().get(
            id=operator.id,
        )

        if _check_overlap(
            mission=locked_mission,
            operator=locked_operator,
        ):
            raise serializers.ValidationError(
                {
                    "operator": (
                        "Operator was just assigned to an " "overlapping mission."
                    ),
                },
            )

        if _check_overlap(mission=locked_mission, drone=locked_drone):
            raise serializers.ValidationError(
                {"drone": "Drone was just assigned to an overlapping mission."},
            )

        create_kwargs = {
            "mission": locked_mission,
            "drone": locked_drone,
            "operator": locked_operator,
        }
        if extra_fields:
            create_kwargs.update(extra_fields)

        instance = MissionDrone.objects.create(**create_kwargs)

        AuditLog.objects.create(
            action="assignment_created",
            target_model="MissionDrone",
            user=action_user,
            changes={
                "mission_id": instance.mission_id,
                "drone_id": instance.drone_id,
                "operator_id": instance.operator_id,
            },
        )
        return instance


def record_mission_outcome(
    *,
    mission,
    result,
    notes=None,
    incident_notes=None,
    action_user=None,
):
    """Record outcome (result + notes) on a completed/aborted mission.

    Locks the mission row to avoid races with status mutations, then writes
    an ``AuditLog`` entry tagged ``mission_outcome_recorded``.
    """
    with transaction.atomic():
        locked_mission = Mission.objects.select_for_update().get(id=mission.id)

        if locked_mission.status not in (Status.COMPLETED, Status.ABORTED):
            raise serializers.ValidationError(
                {
                    "status": (
                        "Outcome can only be recorded for missions with "
                        "status 'completed' or 'aborted'."
                    ),
                },
            )

        previous_result = locked_mission.result
        update_fields = ["result", "updated_at"]
        locked_mission.result = result

        if notes is not None:
            locked_mission.notes = notes
            update_fields.append("notes")
        if incident_notes is not None:
            locked_mission.incident_notes = incident_notes
            update_fields.append("incident_notes")

        locked_mission.save(update_fields=update_fields)

        AuditLog.objects.create(
            action="mission_outcome_recorded",
            target_model="Mission",
            user=action_user,
            changes={
                "mission_id": locked_mission.id,
                "previous_result": previous_result,
                "new_result": locked_mission.result,
                "notes": locked_mission.notes,
                "incident_notes": locked_mission.incident_notes,
            },
        )
        return locked_mission


def record_drone_condition(
    *,
    assignment,
    condition_after,
    condition_description=None,
    action_user=None,
):
    """Record drone condition after a mission and propagate it to the drone.

    Locks the assignment, mission and drone rows. The mission must be in
    ``completed`` or ``aborted`` state. Drone status is mapped via
    ``CONDITION_TO_DRONE_STATUS`` and applied through ``drones.services
    .update_drone`` so that ``DroneStatusHistory`` and (for write-off)
    ``WriteOffRecord`` are created consistently with the rest of the system.
    """
    if condition_after not in CONDITION_TO_DRONE_STATUS:
        raise serializers.ValidationError(
            {"condition_after": "Invalid condition value."},
        )

    target_drone_status = CONDITION_TO_DRONE_STATUS[condition_after]

    with transaction.atomic():
        locked_assignment = (
            MissionDrone.objects.select_for_update()
            .select_related("drone", "mission")
            .get(id=assignment.id)
        )
        locked_mission = Mission.objects.select_for_update().get(
            id=locked_assignment.mission_id,
        )

        if locked_mission.status not in (Status.COMPLETED, Status.ABORTED):
            raise serializers.ValidationError(
                {
                    "mission": (
                        "Drone condition can only be recorded for missions "
                        "with status 'completed' or 'aborted'."
                    ),
                },
            )

        previous_condition = locked_assignment.condition_after
        previous_drone_status = locked_assignment.drone.status

        locked_assignment.condition_after = condition_after
        update_fields = ["condition_after"]
        if condition_description is not None:
            locked_assignment.condition_description = condition_description
            update_fields.append("condition_description")
        locked_assignment.save(update_fields=update_fields)

        locked_drone = Drone.objects.select_for_update().get(
            id=locked_assignment.drone_id,
        )

        is_lost = condition_after == Condition.LOST
        writeoff_reason = (
            "Mission outcome: drone marked as lost"
            if is_lost
            else f"Mission outcome: condition_after={condition_after}"
        )

        update_drone(
            drone=locked_drone,
            drone_data={"status": target_drone_status},
            user=action_user,
            related_mission=locked_mission,
            writeoff_reason=writeoff_reason,
            written_off_at=timezone.localdate() if is_lost else None,
        )

        AuditLog.objects.create(
            action="drone_condition_recorded",
            target_model="MissionDrone",
            user=action_user,
            changes={
                "assignment_id": locked_assignment.id,
                "mission_id": locked_mission.id,
                "drone_id": locked_drone.id,
                "previous_condition": previous_condition,
                "new_condition": condition_after,
                "condition_description": locked_assignment.condition_description,
                "previous_drone_status": previous_drone_status,
                "new_drone_status": target_drone_status,
            },
        )
        return locked_assignment


def unassign_drone_from_mission(*, assignment, action_user=None):
    """Remove a drone assignment from a mission.

    Locks the mission row to ensure the status hasn't changed
    between the check and the delete.
    """
    with transaction.atomic():
        locked_mission = Mission.objects.select_for_update().get(
            id=assignment.mission_id,
        )
        if locked_mission.status != Status.PLANNED:
            raise serializers.ValidationError(
                "Cannot delete assignment unless mission is planned.",
            )

        AuditLog.objects.create(
            action="assignment_deleted",
            target_model="MissionDrone",
            user=action_user,
            changes={
                "mission_id": assignment.mission_id,
                "drone_id": assignment.drone_id,
                "operator_id": assignment.operator_id,
            },
        )
        assignment.delete()
