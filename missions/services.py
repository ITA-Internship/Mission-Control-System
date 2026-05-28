from django.contrib.auth import get_user_model
from django.db import transaction
from django.db.models import Q
from rest_framework import serializers

from drones.models import Drone

from .models import AuditLog, Mission, MissionDrone, Status

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
