from datetime import timedelta

from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework import serializers

from accounts.permissions import get_user_role_code
from drones.models import Drone
from roles.models import COMMANDER_CODE, OPERATOR_CODE

from .models import Condition, Mission, MissionDrone, Result, Status
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


class MissionSerializer(serializers.ModelSerializer):
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
            "created_by",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "status",
            "result",
            "created_by",
            "created_at",
            "updated_at",
        ]

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

        return attrs


class MissionOutcomeSerializer(serializers.ModelSerializer):
    result = serializers.ChoiceField(choices=Result.choices, required=True)

    class Meta:
        model = Mission
        fields = ["id", "status", "result", "notes", "incident_notes"]
        read_only_fields = ["id", "status"]

    def validate(self, attrs):
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
        drone = attrs.get("drone")
        operator = attrs.get("operator")
        mission = self.context.get("mission")

        if not mission:
            raise serializers.ValidationError(
                {"mission": "Mission context is required for assignment validation."}
            )

        if mission.status != Status.PLANNED:
            raise serializers.ValidationError(
                {"mission": "Assignments can only be added to planned missions."}
            )

        if not mission.started_at:
            raise serializers.ValidationError(
                {
                    "mission": (
                        "Mission must have a start time before "
                        "assigning drones or operators."
                    ),
                }
            )

        if drone and drone.status != Drone.STATUS_ACTIVE:
            raise serializers.ValidationError({"drone": "Drone must be active."})

        if operator:
            if get_user_role_code(operator) != OPERATOR_CODE:
                raise serializers.ValidationError(
                    {"operator": "Selected user does not have the Operator role."}
                )

        if operator and mission:
            if _check_overlap(mission=mission, operator=operator):
                raise serializers.ValidationError(
                    {"operator": "Operator is busy during this time."}
                )

        if drone and mission:
            if _check_overlap(mission=mission, drone=drone):
                raise serializers.ValidationError(
                    {"drone": "Drone is assigned to another mission during this time."}
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
