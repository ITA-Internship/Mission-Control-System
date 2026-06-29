from datetime import timedelta

from django.utils import timezone
from rest_framework import serializers

from .models import (
    REPAIR_ORDER_TRANSITIONS,
    ComponentReplacement,
    ComponentType,
    DefectReport,
    RepairEvent,
    RepairOrder,
    RepairOrderStatus,
    RepairStatus,
)
from .services import (
    add_component_replacement,
    create_component_replacement,
    create_defect_report,
    create_repair_order,
    update_repair_order_status,
)

DESCRIPTION_MIN_LENGTH = 10
DETECTED_AT_GRACE_PERIOD = timedelta(seconds=60)


class DateRangeSerializer(serializers.Serializer):
    date_from = serializers.DateTimeField(required=False, allow_null=True)
    date_to = serializers.DateTimeField(required=False, allow_null=True)

    def validate(self, attrs):
        date_from = attrs.get("date_from")
        date_to = attrs.get("date_to")
        if date_from and date_to and date_from > date_to:
            raise serializers.ValidationError(
                "date_from must be before or equal to date_to."
            )
        return attrs


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
        stripped = (value or "").strip()
        return stripped or None

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
        component_name = attrs.get("component_name")

        if component_type == ComponentType.OTHER and not component_name:
            raise serializers.ValidationError(
                {"component_name": ["Component name is required for OTHER."]}
            )

        if component_type != ComponentType.OTHER and (
            self.instance is None or "component_name" in attrs
        ):
            attrs["component_name"] = None

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


class RepairOrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = RepairOrder
        fields = (
            "id",
            "drone",
            "defect_report",
            "status",
            "description",
            "assigned_to",
            "started_at",
            "completed_at",
            "notes",
            "created_by",
            "created_at",
            "updated_at",
        )
        read_only_fields = fields


class RepairOrderListSerializer(serializers.ModelSerializer):
    class Meta:
        model = RepairOrder
        fields = (
            "id",
            "drone",
            "defect_report",
            "status",
            "assigned_to",
            "created_by",
            "created_at",
        )
        read_only_fields = fields


class RepairOrderCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = RepairOrder
        fields = (
            "id",
            "drone",
            "defect_report",
            "description",
            "assigned_to",
        )
        read_only_fields = ("id",)

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

    def create(self, validated_data):
        request = self.context.get("request")
        created_by = getattr(request, "user", None)

        return create_repair_order(
            created_by=created_by,
            **validated_data,
        )


class RepairOrderStatusUpdateSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=RepairOrderStatus.choices)
    notes = serializers.CharField(required=False, allow_blank=True, default="")

    def validate_status(self, value):
        repair_order = self.context["repair_order"]
        allowed = REPAIR_ORDER_TRANSITIONS.get(repair_order.status, [])
        if value not in allowed:
            raise serializers.ValidationError(
                f"Cannot transition from {repair_order.status} to {value}. "
                f"Allowed: {[s.value for s in allowed]}"
            )
        return value

    def save(self):
        repair_order = self.context["repair_order"]
        request = self.context.get("request")
        user = getattr(request, "user", None)

        return update_repair_order_status(
            repair_order=repair_order,
            new_status=self.validated_data["status"],
            user=user,
            notes=self.validated_data.get("notes", ""),
        )


class RepairHistoryTimelineSerializer(serializers.Serializer):
    event_type = serializers.ChoiceField(
        choices=["defect", "status_change", "repair", "replacement"],
    )
    timestamp = serializers.DateTimeField()
    summary = serializers.CharField()
    details = serializers.DictField()


class RepairOrderReplacementSerializer(ComponentReplacementSerializer):
    class Meta(ComponentReplacementSerializer.Meta):
        fields = (
            "id",
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

    def create(self, validated_data):
        repair_order = validated_data.pop("repair_order")
        request = self.context.get("request")
        replaced_by = getattr(request, "user", None)
        return add_component_replacement(
            repair_order=repair_order,
            replaced_by=replaced_by,
            **validated_data,
        )
