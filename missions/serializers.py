from datetime import timedelta

from django.apps import apps
from django.contrib.auth import get_user_model
from django.db import transaction
from django.db.models import Q
from django.utils import timezone
from rest_framework import serializers

from accounts.permissions import get_user_role_code
from roles.models import COMMANDER_CODE, OPERATOR_CODE

from .models import Mission, MissionDrone, Status, AuditLog

User = get_user_model()

TITLE_MIN_LENGTH = 3
STARTED_AT_GRACE_PERIOD = timedelta(seconds=60)
# COMMANDER_PERMISSION = "missions.command_mission"


class UserBriefSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "username", "email"]
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

class MissionDroneSerializer(serializers.ModelSerializer):
    class Meta:
        model = MissionDrone
        fields = ['id', 'mission', 'drone', 'operator', 'created_at']
        read_only_fields = ['id', 'mission', 'created_at']

    def _check_operator_overlap(self, operator, mission):
        overlapping = MissionDrone.objects.filter(
            operator=operator,
            mission__status__in=[Status.ACTIVE, Status.PLANNED]
        ).exclude(mission=mission)

        m_start = mission.started_at
        m_end = mission.ended_at

        q_objects = Q()
        if m_end:
            q_objects &= Q(mission__started_at__lt=m_end)
        q_objects &= (Q(mission__ended_at__isnull=True) | Q(mission__ended_at__gt=m_start))

        return overlapping.filter(q_objects).exists()

    def validate(self, attrs):
        drone = attrs.get('drone')
        operator = attrs.get('operator')
        mission = self.context.get('mission')

        if mission and mission.status != Status.PLANNED:
            raise serializers.ValidationError({"mission": "Assignments can only be added to planned missions."})

        if drone and drone.status != 'ACTIVE':
            raise serializers.ValidationError({"drone": "Drone must be active."})

        if operator:
            if get_user_role_code(operator) != OPERATOR_CODE:
                raise serializers.ValidationError({"operator": "Selected user does not have the Operator role."})

        if operator and mission:
            if self._check_operator_overlap(operator, mission):
                raise serializers.ValidationError({"operator": "Operator is busy during this time."})

        return attrs

    def create(self, validated_data):
        request = self.context.get('request')
        action_user = request.user if request else None
        
        mission = validated_data.get('mission')
        operator = validated_data.get('operator')

        with transaction.atomic():
            Drone = apps.get_model('drones', 'Drone')
            
            # Lock the drone to prevent concurrent assignments
            locked_drone = Drone.objects.select_for_update().get(id=validated_data['drone'].id)
            if locked_drone.status != 'ACTIVE':
                raise serializers.ValidationError({"drone": "Drone is no longer active."})
            
            # Lock the operator to prevent concurrent assignments overlapping
            locked_operator = User.objects.select_for_update().get(id=operator.id)
            if self._check_operator_overlap(locked_operator, mission):
                raise serializers.ValidationError({"operator": "Operator was just assigned to an overlapping mission."})

            validated_data['drone'] = locked_drone
            instance = super().create(validated_data)
            
            locked_drone.status = 'IN_MISSION'
            locked_drone.save(update_fields=['status'])

            AuditLog.objects.create(
                action="assignment_created",
                target_model="MissionDrone",
                user=action_user,
                changes={
                    "drone_id": instance.drone_id,
                    "operator_id": instance.operator_id,
                }
            )
            return instance
