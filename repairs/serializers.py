"""DRF serializers for the repairs API.

Validate and shape defect reports, repair orders, and replacements,
delegating state-changing operations to the service layer.
"""

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
    """Validate a date range for filtering history and timelines."""

    date_from = serializers.DateTimeField(required=False, allow_null=True)
    date_to = serializers.DateTimeField(required=False, allow_null=True)

    def validate(self, attrs):
        """Ensure date_from does not occur after date_to."""
        date_from = attrs.get("date_from")
        date_to = attrs.get("date_to")
        if date_from and date_to and date_from > date_to:
            raise serializers.ValidationError(
                "date_from must be before or equal to date_to."
            )
        return attrs


class DefectReportSerializer(serializers.ModelSerializer):
    """Serialize a defect report for creation and detailed view.

    The reporter field is derived securely from the request context during
    creation rather than accepting it from the payload.
    """

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
        # 'reporter' is strictly read-only because it must be securely bound to the
        # authenticated user making the request via the service layer.
        read_only_fields = ("id", "reporter", "created_at", "updated_at")

    def validate_description(self, value):
        """Require a non-empty description meeting the minimum length."""
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
        """Reject a detection time in the future, allowing a short grace period."""
        # Allow a small grace period for future dates to account for clock skew
        # between offline clients (e.g., a technician's tablet) and the server.
        if value > timezone.now() + DETECTED_AT_GRACE_PERIOD:
            raise serializers.ValidationError("detected_at cannot be in the future.")
        return value

    def create(self, validated_data):
        """Create a defect report via the service layer to ensure auditing."""
        request = self.context.get("request")
        reporter = getattr(request, "user", None)

        return create_defect_report(reporter=reporter, **validated_data)


class DefectReportListSerializer(serializers.ModelSerializer):
    """Read-only summary of a defect report for list views."""

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
    """Read-only view of a repair state transition event."""

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
    """Validate payloads for transitioning a DefectReport's status."""

    status = serializers.ChoiceField(choices=RepairStatus.choices)
    action_taken = serializers.CharField(trim_whitespace=True)

    def validate_action_taken(self, value):
        """Ensure an audit comment is provided for the status change."""
        # Status changes mandate a comment (action_taken) so the audit log
        # always explains *why* the status was moved (e.g., "Soldered the VTX wire").
        if not value:
            raise serializers.ValidationError("Action taken comment is required.")
        return value


class ComponentReplacementSerializer(serializers.ModelSerializer):
    """Serialize standalone hardware replacements.

    Validates physical consistency (e.g., specific names for the OTHER category)
    and delegates creation to the service layer.
    """

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
        """Strip whitespace and convert empty strings to None."""
        stripped = (value or "").strip()
        return stripped or None

    def validate_old_serial_number(self, value):
        """Clean the old serial number, allowing empty values."""
        return (value or "").strip()

    def validate_new_serial_number(self, value):
        """Require a valid, non-empty new serial number."""
        stripped = (value or "").strip()
        if not stripped:
            raise serializers.ValidationError("New serial number is required.")
        return stripped

    def validate_reason(self, value):
        """Require a non-empty reason for the replacement."""
        stripped = (value or "").strip()
        if not stripped:
            raise serializers.ValidationError("Reason is required.")
        return stripped

    def validate_replaced_at(self, value):
        """Ensure the replacement timestamp is not in the future."""
        if value > timezone.now():
            raise serializers.ValidationError("replaced_at cannot be in the future.")
        return value

    def validate(self, attrs):
        """Cross-validate component type and custom naming rules."""
        attrs = super().validate(attrs)
        component_type = attrs.get("component_type")
        component_name = attrs.get("component_name")

        if component_type == ComponentType.OTHER and not component_name:
            raise serializers.ValidationError(
                {"component_name": ["Component name is required for OTHER."]}
            )

        # Enforce data consistency: if the component is a known type (e.g., MOTOR),
        # wipe any user-provided custom name. This prevents database pollution where
        # standard components get arbitrary names, which breaks inventory grouping.
        if component_type != ComponentType.OTHER and (
            self.instance is None or "component_name" in attrs
        ):
            attrs["component_name"] = None

        return attrs

    def create(self, validated_data):
        """Persist the replacement via the service layer."""
        request = self.context.get("request")
        replaced_by = getattr(request, "user", None)

        return create_component_replacement(
            replaced_by=replaced_by,
            **validated_data,
        )


class ComponentReplacementListSerializer(serializers.ModelSerializer):
    """Read-only summary of a component replacement for list views."""

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
    """Serialize a repair order for detailed views."""

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
    """Read-only summary of a repair order for list views."""

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
    """Validate payloads for creating a new repair order."""

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
        """Require a non-empty description meeting the minimum length."""
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
        """Create the repair order via the service layer."""
        request = self.context.get("request")
        created_by = getattr(request, "user", None)

        return create_repair_order(
            created_by=created_by,
            **validated_data,
        )


class RepairOrderStatusUpdateSerializer(serializers.Serializer):
    """Drive a repair order through its state machine."""

    status = serializers.ChoiceField(choices=RepairOrderStatus.choices)
    notes = serializers.CharField(required=False, allow_blank=True, default="")

    def validate_status(self, value):
        """Ensure the transition is permitted by the state machine."""
        # Validate against the state machine definition so clients cannot skip
        # required operational steps (e.g., jumping from PENDING straight to COMPLETED).
        repair_order = self.context["repair_order"]
        allowed = REPAIR_ORDER_TRANSITIONS.get(repair_order.status, [])
        if value not in allowed:
            raise serializers.ValidationError(
                f"Cannot transition from {repair_order.status} to {value}. "
                f"Allowed: {[s.value for s in allowed]}"
            )
        return value

    def save(self):
        """Apply the status change via the service layer.

        Bypasses DRF's standard model update to ensure state transitions
        are handled inside an atomic transaction with row locks.
        """
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
    """Shape heterogeneous repair events into a uniform timeline response."""

    event_type = serializers.ChoiceField(
        choices=["defect", "status_change", "repair", "replacement"],
    )
    timestamp = serializers.DateTimeField()
    summary = serializers.CharField()
    details = serializers.DictField()


class RepairOrderReplacementSerializer(ComponentReplacementSerializer):
    """Serialize hardware replacements explicitly linked to a repair order."""

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
        """Persist the replacement linked to the order via the service layer."""
        repair_order = validated_data.pop("repair_order")
        request = self.context.get("request")
        replaced_by = getattr(request, "user", None)
        return add_component_replacement(
            repair_order=repair_order,
            replaced_by=replaced_by,
            **validated_data,
        )
