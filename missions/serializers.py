from datetime import timedelta

from django.contrib.auth import get_user_model
from django.db.models import Q
from django.utils import timezone
from rest_framework import serializers

from accounts.permissions import get_user_role_code
from drones.models import Drone
from roles.models import COMMANDER_CODE, OPERATOR_CODE

from .models import MISSION_STATUS_TRANSITIONS, Mission, MissionDrone, Status

User = get_user_model()

TITLE_MIN_LENGTH = 3
STARTED_AT_GRACE_PERIOD = timedelta(seconds=60)
# COMMANDER_PERMISSION = "missions.command_mission"


class UserBriefSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "username", "email"]
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

        drone_ids = [item["drone"].id for item in drones_data if "drone" in item]
        operator_ids = [
            item["operator"].id for item in drones_data if item.get("operator")
        ]

        if drone_ids or operator_ids:
            time_overlap = Q(mission__started_at__lte=ended_at) if ended_at else Q()
            time_overlap &= Q(mission__ended_at__gte=started_at) | Q(
                mission__ended_at__isnull=True
            )

            conflicting_links = MissionDrone.objects.filter(
                mission__status__in=[Status.PLANNED, Status.ACTIVE]
            ).filter(time_overlap)

            busy_drones = (
                conflicting_links.filter(drone_id__in=drone_ids)
                .values_list("drone__name", flat=True)
                .distinct()
            )

            if busy_drones:
                raise serializers.ValidationError(
                    "The following drones are already booked for"
                    f"overlapping missions: {', '.join(busy_drones)}."
                )

            busy_operators = (
                conflicting_links.filter(operator_id__in=operator_ids)
                .values_list("operator__username", flat=True)
                .distinct()
            )

            if busy_operators:
                raise serializers.ValidationError(
                    f"The following operators are already assigned to "
                    f"overlapping missions: {', '.join(busy_operators)}."
                )

        return attrs


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
