"""Serialize role catalog entries.

Classes:
    RoleSerializer: Read-only serializer exposing role id, code, and name.
"""

from rest_framework import serializers

from .models import Role


class RoleSerializer(serializers.ModelSerializer):
    """Serialize roles for role filters and selection controls."""

    class Meta:
        model = Role
        fields = ("id", "code", "name")
        read_only_fields = fields
