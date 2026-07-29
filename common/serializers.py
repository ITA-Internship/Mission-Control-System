from django.contrib.auth import get_user_model
from rest_framework import serializers

from accounts.models import MilitaryUnit

User = get_user_model()


class UserBriefSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "username", "email"]
        read_only_fields = fields


class MilitaryUnitBriefSerializer(serializers.ModelSerializer):
    class Meta:
        model = MilitaryUnit
        fields = ["id", "name", "code"]
        read_only_fields = fields
