"""DRF serializers for the missions API.

Validate and shape mission, assignment, outcome, condition and status-update
payloads, delegating state-changing operations to the service layer.
"""

from datetime import timedelta

from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction
from django.db.models import Q
from django.utils import timezone
from rest_framework import serializers

from accounts.permissions import get_user_role_code
from common.serializers import UserBriefSerializer
from drones.models import Drone, DroneStatusHistory
from roles.models import COMMANDER_CODE, OPERATOR_CODE

from .models import (
    MISSION_STATUS_TRANSITIONS,
    Condition,
    Mission,
    MissionDrone,
    Result,
    Status,
)
from .services import (
    assign_drone_to_mission,
    record_drone_condition,
    record_mission_outcome,
)

User = get_user_model()

TITLE_MIN_LENGTH = 3
STARTED_AT_GRACE_PERIOD = timedelta(seconds=60)


class DroneBriefSerializer(serializers.ModelSerializer):
    """Read-only summary of a drone, embedded in mission/assignment responses.

    Output-only: all fields are read-only, so it never creates or updates.
    """

    class Meta:
        model = Drone
        fields = ["id", "name", "serial_number", "drone_model", "status"]
        read_only_fields = fields


class MissionDroneInputSerializer(serializers.ModelSerializer):
    """Nested write serializer for assigning a drone/operator on mission create.

    Exposes ``drone_id`` (required) and ``operator_id`` (optional, nullable),
    mapped to the ``drone`` and ``operator`` relations of :class:`MissionDrone`.
    """

    drone_id = serializers.PrimaryKeyRelatedField(
        queryset=Drone.objects.all(), source="drone"
    )
    operator_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(), source="operator", required=False, allow_null=True
    )

    class Meta:
        model = MissionDrone
        fields = ["drone_id", "operator_id"]

    def validate_operator_id(self, user):
        """Ensure the selected operator, if any, has the Operator role.

        ``None`` passes through (the field is optional). Raises ValidationError
        if the user has no role, or a role other than Operator.
        """
        if user is None:
            return user

        role = getattr(user, "role", None)
        if not role:
            raise serializers.ValidationError(
                "Selected user does not have any role assigned."
            )

        if role.code != OPERATOR_CODE:
            raise serializers.ValidationError(
                "Selected user does not have the Operator role."
            )
        return user


class MissionSerializer(serializers.ModelSerializer):
    """Serialize a mission, including its nested drone assignments.

    Handles both create and update. Assignments may only be set at creation
    time; on update the nested ``drones`` field is forced read-only (see
    ``__init__``) so they are managed through the dedicated assignment endpoints
    instead.
    """

    drones = MissionDroneInputSerializer(
        source="mission_drones", many=True, required=False
    )

    commander = UserBriefSerializer(read_only=True)
    commander_id = serializers.PrimaryKeyRelatedField(
        source="commander",
        queryset=User.objects.all(),
        required=False,
        allow_null=True,
        write_only=True,
    )
    created_by = UserBriefSerializer(read_only=True)

    class Meta:
        model = Mission
        fields = [
            "id",
            "title",
            "commander",
            "commander_id",
            "status",
            "result",
            "location_description",
            "latitude",
            "longitude",
            "started_at",
            "ended_at",
            "notes",
            "incident_notes",
            "created_by",
            "created_at",
            "updated_at",
            "drones",
        ]
        read_only_fields = [
            "id",
            "status",
            "result",
            "created_by",
            "created_at",
            "updated_at",
        ]

    def __init__(self, *args, **kwargs):
        """Extend the base init to freeze ``drones`` for existing missions.

        On an update (``self.instance`` set), the nested ``drones`` field is
        made read-only so an incoming payload is ignored rather than wiping and
        recreating assignments.
        """
        super().__init__(*args, **kwargs)
        # Assignments may only be set when a mission is first created. Once the
        # mission exists, drones must be added or removed through the dedicated
        # assignment endpoints (MissionAssignment* views -> services), which
        # write audit-log entries and take row locks. Marking the nested
        # ``drones`` field read-only on update means an incoming ``drones``
        # payload is ignored here instead of silently wiping and recreating the
        # existing assignments (which would drop condition data and skip
        # auditing/locking).
        if self.instance is not None:
            self.fields["drones"].read_only = True

    def create(self, validated_data):
        """Create a mission and its initial drone assignments.

        Note: unlike the assignment service, this creation path does not take
        row locks or write audit-log entries.
        """
        drones_data = validated_data.pop("mission_drones", [])

        mission = Mission.objects.create(**validated_data)

        for drone_item in drones_data:
            MissionDrone.objects.create(
                mission=mission,
                drone=drone_item["drone"],
                operator=drone_item.get("operator"),
            )

        return mission

    def validate_title(self, value):
        """Strip the title; require it non-empty and at least TITLE_MIN_LENGTH."""
        stripped = (value or "").strip()
        if not stripped:
            raise serializers.ValidationError("Title is required.")
        if len(stripped) < TITLE_MIN_LENGTH:
            raise serializers.ValidationError(
                f"Title must be at least {TITLE_MIN_LENGTH} characters long."
            )
        return stripped

    def validate_started_at(self, value):
        """Reject a start time in the past, allowing STARTED_AT_GRACE_PERIOD.

        ``None`` passes through (the field is optional).
        """
        if value is None:
            return value
        if value < timezone.now() - STARTED_AT_GRACE_PERIOD:
            raise serializers.ValidationError("started_at cannot be in the past.")
        return value

    def validate_commander_id(self, user):
        """Ensure the selected commander, if any, has the Commander role."""
        if user is None:
            return user
        if get_user_role_code(user) != COMMANDER_CODE:
            raise serializers.ValidationError(
                "Selected user does not have the Commander role."
            )
        return user

    def validate(self, attrs):
        """Cross-field checks: location/coordinates and scheduling overlaps.

        Requires either a location description or a full latitude/longitude
        pair (and rejects a lone coordinate). Then rejects the payload if any
        assigned drone or operator is already booked on another PLANNED/ACTIVE
        mission whose time window overlaps this one. Two intervals overlap when
        each starts before the other ends; an open-ended mission
        (``ended_at IS NULL``) extends indefinitely into the future.
        """
        location = (attrs.get("location_description") or "").strip()
        latitude = attrs.get("latitude")
        longitude = attrs.get("longitude")
        has_coordinates = latitude is not None and longitude is not None

        if not location and not has_coordinates:
            raise serializers.ValidationError(
                "Either location or latitude and longitude must be provided."
            )

        latitude_missing = latitude is None
        longitude_missing = longitude is None
        if latitude_missing != longitude_missing:
            raise serializers.ValidationError(
                "latitude and longitude must be provided together."
            )

        drones_data = attrs.get("mission_drones", [])
        started_at = attrs.get("started_at")
        ended_at = attrs.get("ended_at")

        if self.instance:
            if "started_at" not in attrs:
                started_at = self.instance.started_at
            if "ended_at" not in attrs:
                ended_at = self.instance.ended_at

        if "mission_drones" in attrs:
            drones_to_check = [item["drone"] for item in drones_data if "drone" in item]
            operators_to_check = [
                item["operator"] for item in drones_data if item.get("operator")
            ]
        elif self.instance:
            existing_links = self.instance.mission_drones.select_related(
                "drone", "operator"
            ).all()
            drones_to_check = [link.drone for link in existing_links]
            operators_to_check = [
                link.operator for link in existing_links if link.operator_id
            ]
        else:
            drones_to_check, operators_to_check = [], []

        if drones_to_check or operators_to_check:

            drone_ids = [d.id for d in drones_to_check]
            operator_ids = [o.id for o in operators_to_check]
            mission_id = self.instance.id if self.instance else 0

            time_filter = Q()
            if ended_at:
                time_filter &= Q(mission__started_at__lt=ended_at)
            if started_at:
                time_filter &= Q(mission__ended_at__gt=started_at) | Q(
                    mission__ended_at__isnull=True
                )

            conflicts = (
                MissionDrone.objects.filter(
                    mission__status__in=[Status.ACTIVE, Status.PLANNED]
                )
                .exclude(mission_id=mission_id)
                .filter(time_filter)
                .filter(Q(drone_id__in=drone_ids) | Q(operator_id__in=operator_ids))
                .select_related("drone", "operator")
            )

            busy_drones = sorted(
                {md.drone.name for md in conflicts if md.drone_id in drone_ids}
            )

            if busy_drones:
                raise serializers.ValidationError(
                    "The following drones are already booked "
                    f"for overlapping missions: {', '.join(busy_drones)}."
                )

            busy_operators = sorted(
                {
                    md.operator.username
                    for md in conflicts
                    if md.operator_id in operator_ids
                }
            )

            if busy_operators:
                raise serializers.ValidationError(
                    "The following operators are already assigned"
                    f" to overlapping missions: {', '.join(busy_operators)}."
                )

        return attrs


class MissionOutcomeSerializer(serializers.ModelSerializer):
    """Record the result and notes of a completed/aborted mission.

    Update-only; ``update`` delegates persistence to the service layer.
    """

    result = serializers.ChoiceField(choices=Result.choices, required=True)

    class Meta:
        model = Mission
        fields = ["id", "status", "result", "notes", "incident_notes"]
        read_only_fields = ["id", "status"]

    def validate(self, attrs):
        """Guard status, block overwrites, and require notes on failure.

        Fast-path checks on the unlocked instance: the mission must be completed
        or aborted, must not already have a result, ``result`` is required, and
        ``incident_notes`` is required when the result is FAILURE. The
        authoritative status/overwrite checks run under ``select_for_update`` in
        ``record_mission_outcome``; keep the two in sync.
        """
        # Fast-path guards on the unlocked instance. The authoritative status
        # and overwrite checks run inside record_mission_outcome under
        # select_for_update(); keep the rules in both layers in sync.
        instance = self.instance
        if instance and instance.status not in (Status.COMPLETED, Status.ABORTED):
            raise serializers.ValidationError(
                {
                    "status": (
                        "Outcome can only be recorded for missions with "
                        "status 'completed' or 'aborted'."
                    ),
                },
            )
        if instance and instance.result:
            raise serializers.ValidationError(
                {
                    "result": (
                        "Outcome has already been recorded for this mission "
                        "and cannot be overwritten."
                    ),
                },
            )
        if "result" not in attrs:
            raise serializers.ValidationError(
                {"result": "This field is required."},
            )
        if attrs["result"] == Result.FAILURE:
            incident_notes = (attrs.get("incident_notes") or "").strip()
            if not incident_notes:
                raise serializers.ValidationError(
                    {
                        "incident_notes": (
                            "Incident notes are required when result is 'failure'."
                        ),
                    },
                )
        return attrs

    def update(self, instance, validated_data):
        """Persist the outcome via the ``record_mission_outcome`` service.

        The service locks the mission row, saves the fields and writes an audit
        entry; it may raise ValidationError if its authoritative guards fail.
        """
        request = self.context.get("request")
        action_user = request.user if request else None

        return record_mission_outcome(
            mission=instance,
            result=validated_data["result"],
            notes=validated_data.get("notes"),
            incident_notes=validated_data.get("incident_notes"),
            action_user=action_user,
        )


class MissionDroneConditionSerializer(serializers.ModelSerializer):
    """Record a drone's condition after a mission for a single assignment.

    Update-only; ``update`` delegates persistence and drone-status propagation
    to the service layer.
    """

    condition_after = serializers.ChoiceField(
        choices=Condition.choices,
        required=True,
    )

    class Meta:
        model = MissionDrone
        fields = ["id", "condition_after", "condition_description"]
        read_only_fields = ["id"]

    def validate(self, attrs):
        """Guard that the assignment's mission is completed or aborted.

        Fast-path check on the unlocked instance; the authoritative check runs
        under ``select_for_update`` in ``record_drone_condition``.
        """
        # Fast-path guard on the unlocked instance. The authoritative check
        # runs inside record_drone_condition under select_for_update();
        # keep the rules in both layers in sync.
        instance = self.instance
        if instance and instance.mission.status not in (
            Status.COMPLETED,
            Status.ABORTED,
        ):
            raise serializers.ValidationError(
                {
                    "mission": (
                        "Drone condition can only be recorded for missions "
                        "with status 'completed' or 'aborted'."
                    ),
                },
            )
        return attrs

    def update(self, instance, validated_data):
        """Persist the condition via the ``record_drone_condition`` service.

        The service locks the rows, propagates the drone's status (recording
        history and, for a lost drone, a write-off) and writes an audit entry.
        May raise ValidationError from its authoritative guards.
        """
        request = self.context.get("request")
        action_user = request.user if request else None

        return record_drone_condition(
            assignment=instance,
            condition_after=validated_data["condition_after"],
            condition_description=validated_data.get("condition_description"),
            action_user=action_user,
        )


class MissionStatusUpdateSerializer(serializers.ModelSerializer):
    """Drive a mission through its lifecycle and propagate drone statuses.

    Exposes only ``status``; ``update`` applies the change transactionally and
    cascades the assigned drones' statuses.
    """

    status = serializers.ChoiceField(
        choices=Status.choices, required=False, allow_blank=False, allow_null=False
    )

    class Meta:
        model = Mission
        fields = ["status"]

    def validate_status(self, value):
        """Reject transitions not allowed by MISSION_STATUS_TRANSITIONS."""
        if not value:
            raise serializers.ValidationError("Status field cannot be empty.")

        current_status = self.instance.status
        allowed_transitions = MISSION_STATUS_TRANSITIONS.get(current_status, [])

        if value not in allowed_transitions:
            raise serializers.ValidationError(
                f"Cannot change status from '{current_status}' to '{value}'."
            )

        return value

    def validate(self, attrs):
        """Block PLANNED -> ACTIVE when any assigned drone is not active.

        Other transitions pass through unchanged.
        """
        request = self.context.get("request")

        if request and request.method in ["PATCH", "PUT"]:
            if "status" not in attrs or not attrs.get("status"):
                raise serializers.ValidationError({"status": "This field is required."})

        new_status = attrs.get("status")

        if not new_status:
            return attrs

        old_status = self.instance.status
        if old_status == Status.PLANNED and new_status == Status.ACTIVE:

            invalid_assignments = [
                assignment
                for assignment in self.instance.mission_drones.select_related("drone")
                if assignment.drone.status != Drone.STATUS_ACTIVE
            ]

            if invalid_assignments:
                invalid_drones = ", ".join(
                    f"{assignment.drone.name} ({assignment.drone.status})"
                    for assignment in invalid_assignments
                )

                raise serializers.ValidationError(
                    {
                        "status": (
                            "Mission cannot be activated because the following "
                            f"assigned drones are not active: {invalid_drones}."
                        )
                    }
                )

        return attrs

    def update(self, instance, validated_data):
        """Apply the status change and cascade the drones' statuses.

        Runs in one transaction: PLANNED -> ACTIVE moves each assigned drone to
        IN_MISSION; ACTIVE -> COMPLETED/ABORTED returns drones still in mission
        to ACTIVE. Both cascades go through ``_bulk_update_drones``, which
        updates the drones and records their status history in bulk. A database
        IntegrityError is converted into a ValidationError.
        """
        old_status = instance.status
        new_status = validated_data["status"]

        request = self.context.get("request")
        user = getattr(request, "user", None)

        try:
            with transaction.atomic():
                instance.status = new_status
                instance.save(update_fields=["status", "updated_at"])

                assignments = instance.mission_drones.all().select_related("drone")

                if old_status == Status.PLANNED and new_status == Status.ACTIVE:

                    drones_to_update = [
                        {
                            "id": a.drone_id,
                            "old_status": a.drone.status,
                            "new_status": Drone.STATUS_IN_MISSION,
                        }
                        for a in assignments
                    ]

                    if drones_to_update:
                        self._bulk_update_drones(
                            drones_data=drones_to_update,
                            user=user,
                            mission=instance,
                            reason="Mission started",
                        )

                elif old_status == Status.ACTIVE and new_status in (
                    Status.COMPLETED,
                    Status.ABORTED,
                ):
                    drones_to_update = [
                        {
                            "id": a.drone_id,
                            "old_status": a.drone.status,
                            "new_status": Drone.STATUS_ACTIVE,
                        }
                        for a in assignments
                        if a.drone.status == Drone.STATUS_IN_MISSION
                    ]

                    if drones_to_update:
                        self._bulk_update_drones(
                            drones_data=drones_to_update,
                            user=user,
                            mission=instance,
                            reason="Mission finished",
                        )

        except IntegrityError as exc:
            raise serializers.ValidationError(
                {
                    "detail": (
                        "Could not update mission status due to a data integrity error."
                    )
                }
            ) from exc

        return instance

    def _bulk_update_drones(self, drones_data, user, mission, reason):
        """Update the given drones to a shared status and log the history.

        Applies the status in a single ``UPDATE`` and bulk-creates the matching
        ``DroneStatusHistory`` rows, avoiding a query per drone. Assumes every
        entry in ``drones_data`` moves to the same ``new_status`` (the value is
        taken from the first entry); callers always pass a uniform target.
        """
        drone_ids = [d["id"] for d in drones_data]

        Drone.objects.filter(id__in=drone_ids).update(
            status=drones_data[0]["new_status"], updated_at=timezone.now()
        )

        history_records = [
            DroneStatusHistory(
                drone_id=d["id"],
                from_status=d["old_status"],
                to_status=d["new_status"],
                changed_by=user,
                reason=reason,
                related_mission=mission,
                related_writeoff=None,
            )
            for d in drones_data
        ]
        DroneStatusHistory.objects.bulk_create(history_records)


class MissionDroneSerializer(serializers.ModelSerializer):
    """Serialize a mission-drone assignment with drone and operator details.

    Used to list assignments and to create new ones; ``create`` delegates to
    the service layer so locking and auditing stay consistent.
    """

    drone_details = DroneBriefSerializer(source="drone", read_only=True)
    operator_details = UserBriefSerializer(source="operator", read_only=True)

    class Meta:
        model = MissionDrone
        fields = [
            "id",
            "mission",
            "drone",
            "drone_details",
            "operator",
            "operator_details",
            "condition_after",
            "condition_description",
            "flight_started_at",
            "flight_ended_at",
            "created_at",
        ]
        read_only_fields = ["id", "mission", "created_at"]

    def validate(self, attrs):
        """Ensure the operator, if set, has the Operator role."""
        operator = attrs.get("operator")

        if operator:
            if get_user_role_code(operator) != OPERATOR_CODE:
                raise serializers.ValidationError(
                    {"operator": "Selected user does not have the Operator role."}
                )

        return attrs

    def create(self, validated_data):
        """Create the assignment via the ``assign_drone_to_mission`` service.

        The mission comes from ``validated_data`` or, failing that, the
        serializer context (set by the view on POST). The service enforces the
        assignment preconditions, locks rows and writes an audit entry, and may
        raise ValidationError.
        """
        request = self.context.get("request")
        action_user = request.user if request else None

        mission = validated_data.pop("mission", None) or self.context.get("mission")
        drone = validated_data.pop("drone")
        operator = validated_data.pop("operator")

        return assign_drone_to_mission(
            mission=mission,
            drone=drone,
            operator=operator,
            action_user=action_user,
            extra_fields=validated_data if validated_data else None,
        )
