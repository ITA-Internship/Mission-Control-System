from datetime import timedelta

from django.utils import timezone
from rest_framework import serializers

from .models import DefectReport, RepairEvent, RepairStatus
from .services import create_defect_report

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


class RepairEventSerializer(serializers.ModelSerializer):
    class Meta:
        model = RepairEvent
        fields = (
            "id",
            "from_status",
            "to_status",
            "action_taken",
            "technician",
            "created_at",
        )
        read_only_fields = fields


class DefectStatusUpdateSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=RepairStatus.choices)
    action_taken = serializers.CharField(trim_whitespace=True)

    def validate_action_taken(self, value):
        if not value:
            raise serializers.ValidationError("Action taken comment is required.")
        return value
