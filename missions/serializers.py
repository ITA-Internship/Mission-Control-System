from datetime import timedelta

from django.contrib.auth import get_user_model
from django.utils import timezone
from django.db import transaction
from rest_framework import serializers

from accounts.permissions import get_user_role_code
from drones.models import Drone
from roles.models import COMMANDER_CODE, OPERATOR_CODE
from drones.services import update_drone

from .models import (
    MISSION_STATUS_TRANSITIONS,
    Condition,
    Mission,
    MissionDrone,
    Result,
    Status,
)
from .services import (
    _check_overlap,
    assign_drone_to_mission,
    record_drone_condition,
    record_mission_outcome,
)

User = get_user_model()

TITLE_MIN_LENGTH = 3
STARTED_AT_GRACE_PERIOD = timedelta(seconds=60)


class UserBriefSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "username", "email"]
        read_only_fields = fields


class DroneBriefSerializer(serializers.ModelSerializer):
    class Meta:
        model = Drone
        fields = ["id", "name", "serial_number", "drone_model", "status"]
        read_only_fields = fields


class MissionDroneInputSerializer(serializers.ModelSerializer):
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
        stripped = (value or "").strip()
        if not stripped:
            raise serializers.ValidationError("Title is required.")
        if len(stripped) < TITLE_MIN_LENGTH:
            raise serializers.ValidationError(
                f"Title must be at least {TITLE_MIN_LENGTH} characters long."
            )
        return stripped

    def validate_started_at(self, value):
        if value is None:
            return value
        if value < timezone.now() - STARTED_AT_GRACE_PERIOD:
            raise serializers.ValidationError("started_at cannot be in the past.")
        return value

    def validate_commander_id(self, user):
        if user is None:
            return user
        if get_user_role_code(user) != COMMANDER_CODE:
            raise serializers.ValidationError(
                "Selected user does not have the Commander role."
            )
        return user

    def validate(self, attrs):
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
            # Reuse the service-layer overlap rule so the two paths cannot
            # drift. _check_overlap reads started_at/ended_at off the mission
            # and excludes ``mission`` itself, so we hand it an in-memory probe
            # carrying the resolved time window. On create there is no mission
            # yet; id=0 excludes a row that can never exist (real ids start
            # at 1), matching the "exclude nothing" behaviour we want.
            probe = Mission(
                id=self.instance.id if self.instance else 0,
                started_at=started_at,
                ended_at=ended_at,
            )

            busy_drones = sorted(
                {
                    drone.name
                    for drone in drones_to_check
                    if _check_overlap(probe, drone=drone)
                }
            )
            if busy_drones:
                raise serializers.ValidationError(
                    "The following drones are already booked "
                    f"for overlapping missions: {', '.join(busy_drones)}."
                )

            busy_operators = sorted(
                {
                    operator.username
                    for operator in operators_to_check
                    if _check_overlap(probe, operator=operator)
                }
            )
            if busy_operators:
                raise serializers.ValidationError(
                    "The following operators are already assigned"
                    f" to overlapping missions: {', '.join(busy_operators)}."
                )

        return attrs


class MissionOutcomeSerializer(serializers.ModelSerializer):
    result = serializers.ChoiceField(choices=Result.choices, required=True)

    class Meta:
        model = Mission
        fields = ["id", "status", "result", "notes", "incident_notes"]
        read_only_fields = ["id", "status"]

    def validate(self, attrs):
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
    condition_after = serializers.ChoiceField(
        choices=Condition.choices,
        required=True,
    )

    class Meta:
        model = MissionDrone
        fields = ["id", "condition_after", "condition_description"]
        read_only_fields = ["id"]

    def validate(self, attrs):
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
        request = self.context.get("request")
        action_user = request.user if request else None

        return record_drone_condition(
            assignment=instance,
            condition_after=validated_data["condition_after"],
            condition_description=validated_data.get("condition_description"),
            action_user=action_user,
        )


class MissionStatusUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Mission
        fields = ["status"]

    def validate_status(self, value):
        current_status = self.instance.status
        allowed_transitions = MISSION_STATUS_TRANSITIONS.get(current_status, [])

        if value not in allowed_transitions:
            raise serializers.ValidationError(
                f"Cannot change status from '{current_status}' to '{value}'."
            )
        return value
    
    def update(self, instance, validated_data):
        old_status = instance.status
        new_status = validated_data["status"]

        request = self.context.get("request")
        user = getattr(request, "user", None)

        with transaction.atomic():
            instance.status = new_status
            instance.save(update_fields=["status", "updated_at"])

            assignments = instance.mission_drones.select_related("drone")

            if old_status == Status.PLANNED and new_status == Status.ACTIVE:
                for assignment in assignments:
                    if assignment.drone.status == Drone.STATUS_ACTIVE:
                        update_drone(
                            drone=assignment.drone,
                            drone_data={"status": Drone.STATUS_IN_MISSION},
                            user=user,
                            related_mission=instance,
                            status_change_reason="Mission started",
                        )

            elif old_status == Status.ACTIVE and new_status in (
                Status.COMPLETED,
                Status.ABORTED,
            ):
                for assignment in assignments:
                    if assignment.drone.status == Drone.STATUS_IN_MISSION:
                        update_drone(
                            drone=assignment.drone,
                            drone_data={"status": Drone.STATUS_ACTIVE},
                            user=user,
                            related_mission=instance,
                            status_change_reason="Mission finished",
                        )

        return instance


class MissionDroneSerializer(serializers.ModelSerializer):
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
        operator = attrs.get("operator")

        if operator:
            if get_user_role_code(operator) != OPERATOR_CODE:
                raise serializers.ValidationError(
                    {"operator": "Selected user does not have the Operator role."}
                )

        return attrs

    def create(self, validated_data):
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
