from django.contrib.auth import get_user_model
from django.db import transaction
from django.db.models import Q
from django.utils import timezone
from rest_framework import serializers

from drones.models import Drone
from drones.services import update_drone

from .models import Condition, Mission, MissionAuditLog, MissionDrone, Status

CONDITION_TO_DRONE_STATUS = {
    Condition.OK: Drone.STATUS_ACTIVE,
    Condition.DAMAGED: Drone.STATUS_DAMAGED,
    Condition.LOST: Drone.STATUS_WRITTEN_OFF,
}


User = get_user_model()


def _check_overlap(mission, operator=None, drone=None):
    """Check whether a drone or operator has a scheduling conflict
    with another PLANNED / ACTIVE mission.

    Two intervals overlap when each one starts before the other ends.
    Open-ended missions (``ended_at IS NULL``) are treated as extending
    indefinitely into the future.

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

    time_filter = Q()

    if m_end:
        time_filter &= Q(mission__started_at__lt=m_end)

    time_filter &= Q(mission__ended_at__isnull=True) | Q(
        mission__ended_at__gt=m_start,
    )

    return overlapping.filter(time_filter).exists()


def assign_drone_to_mission(
    *,
    mission,
    drone,
    operator,
    action_user=None,
    extra_fields=None,
):

    with transaction.atomic():
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
                        "Operator was just assigned to an overlapping mission."
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

        MissionAuditLog.objects.create(
            user=action_user,
            action="assignment_created",
            target_model="MissionDrone",
            target_id=instance.id,
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
    an ``MissionAuditLog`` entry tagged ``mission_outcome_recorded``.
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

        if locked_mission.result:
            raise serializers.ValidationError(
                {
                    "result": (
                        "Outcome has already been recorded for this mission "
                        "and cannot be overwritten."
                    ),
                },
            )

        previous_result = locked_mission.result
        update_fields = ["result", "updated_at"]
        locked_mission.result = result

        if notes:
            locked_mission.notes = notes
            update_fields.append("notes")
        if incident_notes:
            locked_mission.incident_notes = incident_notes
            update_fields.append("incident_notes")

        locked_mission.save(update_fields=update_fields)

        MissionAuditLog.objects.create(
            action="mission_outcome_recorded",
            target_model="Mission",
            target_id=locked_mission.id,
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
        fk_ids = MissionDrone.objects.values("mission_id", "drone_id").get(
            id=assignment.id,
        )

        locked_mission = Mission.objects.select_for_update().get(
            id=fk_ids["mission_id"],
        )
        locked_drone = Drone.objects.select_for_update().get(
            id=fk_ids["drone_id"],
        )
        locked_assignment = (
            MissionDrone.objects.select_for_update()
            .select_related("mission")
            .get(id=assignment.id)
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

        if previous_condition == Condition.LOST and condition_after != Condition.LOST:
            raise serializers.ValidationError(
                {
                    "condition_after": (
                        "Cannot reverse a 'lost' condition: a writeoff record "
                        "has been created and requires a manual reversal "
                        "process."
                    ),
                },
            )

        if (
            condition_after == Condition.LOST
            and locked_drone.status == Drone.STATUS_WRITTEN_OFF
        ):
            raise serializers.ValidationError(
                {
                    "condition_after": (
                        "Drone is already written off; cannot record "
                        "'lost' condition again."
                    ),
                },
            )

        locked_assignment.condition_after = condition_after
        update_fields = ["condition_after"]
        if condition_description is not None:
            locked_assignment.condition_description = condition_description
            update_fields.append("condition_description")
        locked_assignment.save(update_fields=update_fields)

        previous_drone_status = locked_drone.status

        writeoff_kwargs = {}
        if condition_after == Condition.LOST:
            writeoff_kwargs = {
                "writeoff_reason": "Mission outcome: drone marked as lost",
                "written_off_at": timezone.localdate(),
            }

        status_change_reason = ""

        if condition_after != Condition.LOST:
            status_change_reason = (
                condition_description
                or f"Mission condition recorded: {condition_after}"
            )

        update_drone(
            drone=locked_drone,
            drone_data={"status": target_drone_status},
            user=action_user,
            related_mission=locked_mission,
            status_change_reason=status_change_reason,
            **writeoff_kwargs,
        )

        MissionAuditLog.objects.create(
            action="drone_condition_recorded",
            target_model="MissionDrone",
            target_id=locked_assignment.id,
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

        MissionAuditLog.objects.create(
            user=action_user,
            action="assignment_deleted",
            target_model="MissionDrone",
            target_id=assignment.id,
            changes={
                "mission_id": assignment.mission_id,
                "drone_id": assignment.drone_id,
                "operator_id": assignment.operator_id,
            },
        )
        assignment.delete()
