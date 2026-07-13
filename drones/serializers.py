"""Serialize drone inventory, specifications, write-offs, and audit history.

Classes:
    DroneSpecChangeLogSerializer: Read-only serializer for spec audit entries.
    DroneSpecValidationMixin: Shared JSON validation for specification fields.
    DroneSpecSerializer: Full technical specification serializer.
    DroneSpecUpdateSerializer: Partial technical specification update serializer.
    WriteOffRecordSerializer: Read-only write-off record serializer.
    DroneStatusHistorySerializer: Status history serializer with display fields.
    DroneSerializer: Create/detail serializer for drones and nested specs.
    DroneUpdateSerializer: Partial update serializer with write-off transition data.
    DroneListSerializer: Compact drone list serializer.
    DroneModelSerializer: Drone model catalog serializer.
    WriteOffAuditSerializer: Audit/history serializer for write-off records.
    DroneImportSerializer: CSV upload validation serializer.
    WriteOffRecordCreateSerializer: Serializer for creating write-off records.
"""

from django.core.exceptions import ValidationError
from rest_framework import serializers
from rest_framework.serializers import as_serializer_error

from missions.models import Mission, MissionDrone

from .models import (
    Drone,
    DroneModel,
    DroneSpec,
    DroneSpecChangeLog,
    DroneStatusHistory,
    WriteOffRecord,
)
from .services import (
    create_drone_with_spec,
    create_writeoff_record,
    update_drone,
    validate_drone_classification,
)


class DroneSpecChangeLogSerializer(serializers.ModelSerializer):
    """Serialize specification audit entries for read-only API responses."""

    class Meta:
        """Configure read-only fields for specification change logs."""

        model = DroneSpecChangeLog
        fields = (
            "id",
            "changed_by",
            "changed_fields",
            "old_values",
            "new_values",
            "created_at",
        )
        read_only_fields = fields


class DroneSpecValidationMixin:
    """Provide shared JSON validation for drone specification serializers."""

    def validate_camera_specs(self, value):
        """Validate that camera specs are submitted as a JSON object."""
        if not isinstance(value, dict):
            raise serializers.ValidationError("camera_specs must be a JSON object.")
        return value

    def validate_additional_modules(self, value):
        """Validate that additional modules are submitted as a list of objects."""
        if not isinstance(value, list):
            raise serializers.ValidationError(
                "additional_modules must be a JSON array."
            )

        for index, module in enumerate(value):
            if not isinstance(module, dict):
                raise serializers.ValidationError(
                    f"additional_modules[{index}] must be a JSON object."
                )

        return value


class DroneSpecSerializer(DroneSpecValidationMixin, serializers.ModelSerializer):
    """Serialize full technical specifications and change history for a drone."""

    change_history = DroneSpecChangeLogSerializer(many=True, read_only=True)

    class Meta:
        """Configure full DroneSpec fields exposed by the API."""

        model = DroneSpec
        fields = (
            "id",
            "frame_type",
            "motor_model",
            "battery_type",
            "battery_capacity_mah",
            "battery_model",
            "camera_model",
            "camera_specs",
            "vtx_model",
            "flight_controller",
            "firmware_version",
            "is_firmware_outdated",
            "communication_protocol",
            "control_channel",
            "telemetry_channel",
            "max_speed_kmh",
            "typical_range_km",
            "max_range_km",
            "typical_flight_time_min",
            "max_flight_time_min",
            "frequency_mhz",
            "payload_capacity_g",
            "additional_modules",
            "technical_documentation_url",
            "firmware_file_url",
            "updated_at",
            "change_history",
        )
        read_only_fields = ("id", "updated_at", "change_history")


class DroneSpecUpdateSerializer(DroneSpecValidationMixin, serializers.ModelSerializer):
    """Serialize partial updates to a drone technical specification."""

    class Meta:
        """Configure optional DroneSpec fields accepted during partial updates."""

        model = DroneSpec
        exclude = ("drone",)
        read_only_fields = ("id", "updated_at")
        extra_kwargs = {
            "frame_type": {"required": False},
            "motor_model": {"required": False},
            "battery_type": {"required": False},
            "battery_capacity_mah": {"required": False},
            "battery_model": {"required": False},
            "camera_model": {"required": False},
            "camera_specs": {"required": False},
            "vtx_model": {"required": False},
            "flight_controller": {"required": False},
            "firmware_version": {"required": False},
            "is_firmware_outdated": {"required": False},
            "communication_protocol": {"required": False},
            "control_channel": {"required": False},
            "telemetry_channel": {"required": False},
            "typical_range_km": {"required": False},
            "max_speed_kmh": {"required": False},
            "max_range_km": {"required": False},
            "typical_flight_time_min": {"required": False},
            "max_flight_time_min": {"required": False},
            "frequency_mhz": {"required": False},
            "payload_capacity_g": {"required": False},
            "additional_modules": {"required": False},
            "technical_documentation_url": {"required": False},
            "firmware_file_url": {"required": False},
        }


class WriteOffRecordSerializer(serializers.ModelSerializer):
    """Serialize immutable write-off data attached to a drone."""

    related_mission_id = serializers.IntegerField(read_only=True)
    reason_label = serializers.CharField(read_only=True)

    class Meta:
        """Configure read-only write-off record fields."""

        model = WriteOffRecord
        fields = (
            "id",
            "reason",
            "reason_label",
            "reason_description",
            "authorized_by",
            "related_mission_id",
            "document_number",
            "written_off_at",
            "created_at",
        )
        read_only_fields = fields


class DroneStatusHistorySerializer(serializers.ModelSerializer):
    """Serialize drone lifecycle status history with display metadata.

    Adds a readable user label and event type so clients can distinguish status
    changes caused by missions, repairs, write-offs, or manual updates.
    """

    related_mission_id = serializers.IntegerField(read_only=True)
    changed_by_display = serializers.SerializerMethodField()
    event_type = serializers.SerializerMethodField()

    class Meta:
        """Configure status history fields exposed by the API."""

        model = DroneStatusHistory
        fields = (
            "id",
            "from_status",
            "to_status",
            "changed_by",
            "changed_by_display",
            "reason",
            "event_type",
            "related_mission_id",
            "related_repair_order",
            "related_writeoff",
            "created_at",
        )
        read_only_fields = fields

    def get_changed_by_display(self, obj):
        """Return a readable name for the user who changed the status."""
        user = obj.changed_by

        if not user:
            return ""

        return (
            getattr(user, "username", None) or getattr(user, "email", None) or str(user)
        )

    def get_event_type(self, obj):
        """Return the domain event type that caused this status history entry."""
        if obj.related_writeoff_id:
            return "writeoff"

        if obj.related_repair_order_id:
            return "repair"

        if obj.related_mission_id:
            return "mission"

        return "status_change"


class DroneSerializer(serializers.ModelSerializer):
    """Serialize drone create/detail data with nested technical specification.

    Creation is delegated to the service layer so the drone, DroneSpec, and
    initial DroneSpecChangeLog are created consistently in one workflow.
    """

    spec = DroneSpecSerializer()
    writeoff_record = WriteOffRecordSerializer(read_only=True)
    status_history = DroneStatusHistorySerializer(many=True, read_only=True)
    status_label = serializers.CharField(read_only=True)
    status_indicator = serializers.CharField(read_only=True)
    status_category = serializers.CharField(read_only=True)

    class Meta:
        """Expose all Drone fields for create and detail responses."""

        model = Drone
        fields = "__all__"

    def create(self, validated_data):
        """Create a drone through the service layer so initial audit logging is kept."""
        spec_data = validated_data.pop("spec")
        request = self.context.get("request")
        user = getattr(request, "user", None)

        return create_drone_with_spec(
            drone_data=validated_data,
            spec_data=spec_data,
            user=user,
        )

    def validate(self, attrs):
        """Validate that the selected classification is supported by the drone model."""
        drone_model = attrs.get("drone_model")
        classification = attrs.get("classification")

        if drone_model and classification:
            validate_drone_classification(drone_model, classification)

        return attrs


class DroneUpdateSerializer(serializers.ModelSerializer):
    """Serialize partial drone updates and inactive lifecycle transitions.

    Inactive transitions require write-off metadata so the service layer can
    create an immutable WriteOffRecord and link it to DroneStatusHistory.
    """

    spec = DroneSpecUpdateSerializer(required=False)

    writeoff_reason = serializers.ChoiceField(
        choices=WriteOffRecord.Reason.choices,
        write_only=True,
        required=False,
        allow_blank=True,
    )
    writeoff_reason_description = serializers.CharField(
        write_only=True,
        required=False,
        allow_blank=True,
    )

    status_change_reason = serializers.CharField(
        write_only=True,
        required=False,
        allow_blank=True,
    )

    document_number = serializers.CharField(
        write_only=True,
        required=False,
        allow_blank=True,
    )
    written_off_at = serializers.DateField(write_only=True, required=False)
    related_mission_id = serializers.PrimaryKeyRelatedField(
        source="related_mission",
        queryset=Mission.objects.all(),
        write_only=True,
        required=False,
        allow_null=True,
    )

    class Meta:
        """Configure optional Drone fields and write-off inputs for partial updates."""

        model = Drone
        fields = (
            "serial_number",
            "inventory_number",
            "name",
            "drone_model",
            "classification",
            "status",
            "military_unit",
            "acquired_at",
            "notes",
            "spec",
            "writeoff_reason",
            "writeoff_reason_description",
            "status_change_reason",
            "document_number",
            "written_off_at",
            "related_mission_id",
        )
        extra_kwargs = {
            "serial_number": {"required": False},
            "inventory_number": {"required": False},
            "name": {"required": False},
            "drone_model": {"required": False},
            "status": {"required": False},
            "military_unit": {"required": False},
            "acquired_at": {"required": False},
            "notes": {"required": False},
        }

    def validate(self, attrs):
        """Require write-off fields when a patch moves a drone to an inactive status."""
        requested_status = attrs.get("status")

        # Terminal inventory states require write-off metadata before the service
        # creates immutable audit records
        if requested_status not in Drone.INACTIVE_STATUSES:
            return attrs

        required_fields = {
            "writeoff_reason": attrs.get("writeoff_reason"),
            "written_off_at": attrs.get("written_off_at"),
        }

        errors = {}

        for field_name, value in required_fields.items():
            if value is None:
                errors[field_name] = (
                    "This field is required when drone is decommissioned, "
                    "sold, transferred, or written off."
                )
                continue

            if isinstance(value, str) and not value.strip():
                errors[field_name] = (
                    "This field is required when drone is decommissioned, "
                    "sold, transferred, or written off."
                )

        if errors:
            raise serializers.ValidationError(errors)

        drone_model = attrs.get("drone_model")
        classification = attrs.get("classification")

        # Keep serializer validation aligned with the model/service classification rule.
        if drone_model and classification:
            validate_drone_classification(drone_model, classification)

        return attrs

    def update(self, instance, validated_data):
        """Apply drone updates through the service layer and map domain errors."""
        spec_data = validated_data.pop("spec", None)

        writeoff_reason = validated_data.pop("writeoff_reason", "")
        writeoff_reason_description = validated_data.pop(
            "writeoff_reason_description",
            "",
        )
        status_change_reason = validated_data.pop("status_change_reason", "")
        document_number = validated_data.pop("document_number", "")
        written_off_at = validated_data.pop("written_off_at", None)
        related_mission = validated_data.pop("related_mission", None)

        request = self.context.get("request")
        user = getattr(request, "user", None)

        # Let the service perform the audit-sensitive update, then expose any model
        # validation errors under the API field names used by clients.
        try:
            return update_drone(
                drone=instance,
                drone_data=validated_data,
                spec_data=spec_data,
                user=user,
                writeoff_reason=writeoff_reason,
                writeoff_reason_description=writeoff_reason_description,
                document_number=document_number,
                written_off_at=written_off_at,
                related_mission=related_mission,
                status_change_reason=status_change_reason,
            )
        except ValidationError as exc:
            raise serializers.ValidationError(self._map_writeoff_errors(exc))

    # Map model-level write-off fields to serializer input field names.
    WRITEOFF_FIELD_MAP = {
        "reason": "writeoff_reason",
        "reason_description": "writeoff_reason_description",
    }

    @classmethod
    def _map_writeoff_errors(cls, exc):
        """Map WriteOffRecord validation errors to API-facing field names."""
        error_detail = as_serializer_error(exc)

        return {
            cls.WRITEOFF_FIELD_MAP.get(field, field): messages
            for field, messages in error_detail.items()
        }

    def to_representation(self, instance):
        """Return the full drone representation after a partial update."""
        return DroneSerializer(instance, context=self.context).data


class DroneListSerializer(serializers.ModelSerializer):
    """Serialize compact drone fields for list responses."""

    status_label = serializers.CharField(read_only=True)
    status_indicator = serializers.CharField(read_only=True)
    status_category = serializers.CharField(read_only=True)

    class Meta:
        """Configure compact Drone fields exposed by list endpoints."""

        model = Drone
        fields = (
            "id",
            "serial_number",
            "inventory_number",
            "name",
            "drone_model",
            "classification",
            "status",
            "status_label",
            "status_indicator",
            "status_category",
            "military_unit",
            "created_at",
        )


class DroneModelSerializer(serializers.ModelSerializer):
    """Serialize drone model catalog entries and supported classifications."""

    class Meta:
        """Configure DroneModel fields exposed by the API."""

        model = DroneModel
        fields = (
            "id",
            "name",
            "manufacturer",
            "description",
            "supported_classifications",
            "is_active",
            "created_at",
            "updated_at",
        )

    def validate(self, attrs):
        """Validate that the model defines at least one known classification."""
        classifications = attrs.get("supported_classifications")

        if not classifications:
            raise ValidationError(
                {
                    "supported_classifications": (
                        "A drone model must support at least one classification."
                    )
                }
            )

        valid_keys = {choice[0] for choice in Drone.CLASSIFICATION_CHOICES}
        invalid_items = [item for item in classifications if item not in valid_keys]

        if invalid_items:
            raise ValidationError(
                {
                    "supported_classifications": (
                        f"Value {invalid_items} are not valid classifications. "
                        f'Valid classifications: {", ".join(valid_keys)}'
                    )
                }
            )

        return attrs


class WriteOffAuditSerializer(serializers.ModelSerializer):
    """Serialize write-off records for audit and history endpoints."""

    drone_id = serializers.IntegerField(source="drone.id", read_only=True)
    drone_name = serializers.CharField(source="drone.name", read_only=True)
    drone_serial_number = serializers.CharField(
        source="drone.serial_number", read_only=True
    )
    drone_inventory_number = serializers.CharField(
        source="drone.inventory_number", read_only=True
    )
    authorized_by_username = serializers.CharField(
        source="authorized_by.username",
        read_only=True,
        allow_null=True,
    )
    related_mission_id = serializers.IntegerField(read_only=True)

    class Meta:
        """Configure read-only write-off audit fields."""

        model = WriteOffRecord
        fields = (
            "id",
            "drone_id",
            "drone_name",
            "drone_serial_number",
            "drone_inventory_number",
            "reason",
            "reason_description",
            "authorized_by",
            "authorized_by_username",
            "related_mission",
            "related_mission_id",
            "document_number",
            "written_off_at",
            "created_at",
        )
        read_only_fields = fields


class DroneImportSerializer(serializers.Serializer):
    """Validate uploaded files for drone CSV import."""

    file = serializers.FileField(
        help_text="CSV file with drone inventory data.",
    )

    def validate_file(self, file):
        """Accept only files with the .csv extension for drone import."""
        if not file.name.endswith(".csv"):
            raise serializers.ValidationError(
                "Only files with the extension .csv are allowed"
            )
        return file


class WriteOffRecordCreateSerializer(serializers.ModelSerializer):
    """Validate and create immutable drone write-off records.

    A drone can be written off only once, cannot already be inactive, and when a
    mission is supplied it must be the latest mission assigned to that drone.
    """

    class Meta:
        """Configure fields accepted when creating a write-off record."""

        model = WriteOffRecord
        fields = (
            "id",
            "drone",
            "reason",
            "reason_description",
            "related_mission",
            "document_number",
            "written_off_at",
            "created_at",
        )

    def validate(self, attrs):
        """Validate business rules for creating a drone write-off record."""
        drone = attrs.get("drone")
        related_mission = attrs.get("related_mission")

        if related_mission is not None:
            # A mission-linked write-off must point to the drone's latest assignment,
            # so loss/destruction is not attached to an older mission by mistake.
            mission_ids = list(
                MissionDrone.objects.filter(drone=drone)
                .order_by("-created_at")
                .values_list("mission_id", flat=True)
            )

            if mission_ids:
                latest_mission_id = mission_ids[0]

                if related_mission.id != latest_mission_id:
                    if related_mission.id in mission_ids:
                        raise serializers.ValidationError(
                            {
                                "related_mission": (
                                    f"Mission {related_mission.id} is not the latest. "
                                    f"A drone can only be written off based on "
                                    f"its latest mission."
                                )
                            }
                        )
                    else:
                        raise serializers.ValidationError(
                            {
                                "related_mission": (
                                    f"Drone {drone.id} is not assigned to "
                                    f"mission {related_mission.id}."
                                )
                            }
                        )

            else:
                raise serializers.ValidationError(
                    {"related_mission": f"Drone {drone} has no related missions."}
                )

        if WriteOffRecord.objects.filter(drone=drone).exists():
            raise serializers.ValidationError(
                {"drone": "A write-off record for this drone already exists."}
            )

        if drone.status in Drone.INACTIVE_STATUSES:
            raise serializers.ValidationError(
                {
                    "drone": (
                        f"Cannot write off a drone "
                        f"with inactive status '{drone.status}'."
                    )
                }
            )

        return attrs

    def create(self, validated_data):
        """
        Create the write-off through the service layer so status history is
        recorded."""
        user = self.context["request"].user

        return create_writeoff_record(user=user, **validated_data)
