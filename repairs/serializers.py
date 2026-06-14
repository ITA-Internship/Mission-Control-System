from datetime import timedelta

from django.utils import timezone
from rest_framework import serializers

from .models import ComponentReplacement, ComponentType, DefectReport
from .services import create_component_replacement, create_defect_report

DESCRIPTION_MIN_LENGTH = 10
DETECTED_AT_GRACE_PERIOD = timedelta(seconds=60)


class DefectReportSerializer(serializers.ModelSerializer):
    class Meta:
        model = DefectReport
        fields = (
            "id",
            "drone",
            "defect_type",
            "severity",
            "description",
            "detected_at",
            "reporter",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "reporter", "created_at", "updated_at")

    def validate_description(self, value):
        stripped = (value or "").strip()
        if not stripped:
            raise serializers.ValidationError("Description is required.")
        if len(stripped) < DESCRIPTION_MIN_LENGTH:
            raise serializers.ValidationError(
                f"Description must be at least {DESCRIPTION_MIN_LENGTH} "
                "characters long."
            )
        return stripped

    def validate_detected_at(self, value):
        if value > timezone.now() + DETECTED_AT_GRACE_PERIOD:
            raise serializers.ValidationError("detected_at cannot be in the future.")
        return value

    def create(self, validated_data):
        request = self.context.get("request")
        reporter = getattr(request, "user", None)

        return create_defect_report(reporter=reporter, **validated_data)


class DefectReportListSerializer(serializers.ModelSerializer):
    class Meta:
        model = DefectReport
        fields = (
            "id",
            "drone",
            "defect_type",
            "severity",
            "detected_at",
            "reporter",
            "created_at",
        )
        read_only_fields = fields


class ComponentReplacementSerializer(serializers.ModelSerializer):
    class Meta:
        model = ComponentReplacement
        fields = (
            "id",
            "drone",
            "component_type",
            "component_name",
            "old_serial_number",
            "new_serial_number",
            "reason",
            "replaced_at",
            "replaced_by",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "replaced_by", "created_at", "updated_at")

    def validate_component_name(self, value):
        return (value or "").strip()

    def validate_old_serial_number(self, value):
        return (value or "").strip()

    def validate_new_serial_number(self, value):
        stripped = (value or "").strip()
        if not stripped:
            raise serializers.ValidationError("New serial number is required.")
        return stripped

    def validate_reason(self, value):
        stripped = (value or "").strip()
        if not stripped:
            raise serializers.ValidationError("Reason is required.")
        return stripped

    def validate_replaced_at(self, value):
        if value > timezone.now():
            raise serializers.ValidationError("replaced_at cannot be in the future.")
        return value

    def validate(self, attrs):
        attrs = super().validate(attrs)
        component_type = attrs.get("component_type")
        component_name = attrs.get("component_name", "")

        if component_type == ComponentType.OTHER and not component_name:
            raise serializers.ValidationError(
                {"component_name": ["Component name is required for OTHER."]}
            )

        if component_type != ComponentType.OTHER:
            attrs["component_name"] = ""

        return attrs

    def create(self, validated_data):
        request = self.context.get("request")
        replaced_by = getattr(request, "user", None)

        return create_component_replacement(
            replaced_by=replaced_by,
            **validated_data,
        )


class ComponentReplacementListSerializer(serializers.ModelSerializer):
    class Meta:
        model = ComponentReplacement
        fields = (
            "id",
            "drone",
            "component_type",
            "component_name",
            "new_serial_number",
            "replaced_at",
            "replaced_by",
            "created_at",
        )
        read_only_fields = fields
