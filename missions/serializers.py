from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework import serializers

#? Pulls the canonical role codes from the roles app.
from roles.models import COMMANDER_CODE

from .models import Mission


User = get_user_model()


#we will need smth like this function from accoints team
def _user_has_role(user, *codes):
    """Check whether `user` has any of the given role codes."""

    if not user or not getattr(user, 'is_authenticated', False):
        return False
    
    role = getattr(user, 'role', None)
    if role is not None and getattr(role, 'code', None) in codes:
        return True
    
    return False


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
        if not _user_has_role(user, COMMANDER_CODE):
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
                'Either location_description or both latitude and longitude must be provided.'
            )

        if (latitude is None) ^ (longitude is None):
            raise serializers.ValidationError(
                'latitude and longitude must be provided together.'
            )

        return attrs
