from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework import serializers

from roles.models import COMMANDER_CODE
from .models import Mission


User = get_user_model()


class MissionSerializer(serializers.ModelSerializer):
    commander_id = serializers.PrimaryKeyRelatedField(
        source='commander',
        queryset=User.objects.all(),
        required=False,
        allow_null=True,
    )
    created_by = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = Mission
        fields = [
            'id',
            'title',
            'commander_id',
            'status',
            'result',
            'location_description',
            'latitude',
            'longitude',
            'started_at',
            'ended_at',
            'notes',
            'created_by',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'status', 'result', 'created_by', 'created_at', 'updated_at']

    def validate_title(self, value):
        value = (value or '').strip()
        if not value:
            raise serializers.ValidationError('Title is required.')
        return value

    def validate_started_at(self, value):
        if value is None:
            raise serializers.ValidationError('started_at is required.')
        if value < timezone.now():
            raise serializers.ValidationError('started_at cannot be in the past.')
        return value

    def validate_commander_id(self, user):
        if user is None:
            return user
        role_code = getattr(getattr(user, 'role', None), 'code', None)
        if role_code != COMMANDER_CODE:
            raise serializers.ValidationError(
                'Selected user does not have the Commander role.'
            )
        return user

    def validate(self, attrs):
        location = (attrs.get('location_description') or '').strip()
        latitude = attrs.get('latitude')
        longitude = attrs.get('longitude')
        has_coordinates = latitude is not None and longitude is not None

        if not location and not has_coordinates:
            raise serializers.ValidationError(
                'Either location or latitude and longitude must be provided.'
            )

        if (latitude is None) ^ (longitude is None):
            raise serializers.ValidationError(
                'latitude and longitude must be provided together.'
            )

        return attrs
