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
    class Meta:
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
    def validate_camera_specs(self, value):
        if not isinstance(value, dict):
            raise serializers.ValidationError("camera_specs must be a JSON object.")
        return value

    def validate_additional_modules(self, value):
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
    change_history = DroneSpecChangeLogSerializer(many=True, read_only=True)

    class Meta:
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
    class Meta:
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
    related_mission_id = serializers.IntegerField(read_only=True)
    reason_label = serializers.CharField(read_only=True)

    class Meta:
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
    related_mission_id = serializers.IntegerField(read_only=True)
    changed_by_display = serializers.SerializerMethodField()
    event_type = serializers.SerializerMethodField()

    class Meta:
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

    def get_changed_by_display(self, obj) -> str:
        user = obj.changed_by

        if not user:
            return ""

        return (
            getattr(user, "username", None) or getattr(user, "email", None) or str(user)
        )

    def get_event_type(self, obj) -> str:
        if obj.related_writeoff_id:
            return "writeoff"

        if obj.related_repair_order_id:
            return "repair"

        if obj.related_mission_id:
            return "mission"

        return "status_change"


class DroneSerializer(serializers.ModelSerializer):
    spec = DroneSpecSerializer()
    writeoff_record = WriteOffRecordSerializer(read_only=True)
    status_history = DroneStatusHistorySerializer(many=True, read_only=True)
    status_label = serializers.CharField(read_only=True)
    status_indicator = serializers.CharField(read_only=True)
    status_category = serializers.CharField(read_only=True)

    class Meta:
        model = Drone
        fields = "__all__"

    def create(self, validated_data):
        spec_data = validated_data.pop("spec")
        request = self.context.get("request")
        user = getattr(request, "user", None)

        return create_drone_with_spec(
            drone_data=validated_data,
            spec_data=spec_data,
            user=user,
        )

    def validate(self, attrs):
        drone_model = attrs.get("drone_model")
        classification = attrs.get("classification")

        if drone_model and classification:
            validate_drone_classification(drone_model, classification)

        return attrs


class DroneUpdateSerializer(serializers.ModelSerializer):
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
        requested_status = attrs.get("status")

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

        if drone_model and classification:
            validate_drone_classification(drone_model, classification)

        return attrs

    def update(self, instance, validated_data):
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

    WRITEOFF_FIELD_MAP = {
        "reason": "writeoff_reason",
        "reason_description": "writeoff_reason_description",
    }

    @classmethod
    def _map_writeoff_errors(cls, exc):
        error_detail = as_serializer_error(exc)

        return {
            cls.WRITEOFF_FIELD_MAP.get(field, field): messages
            for field, messages in error_detail.items()
        }

    def to_representation(self, instance):
        return DroneSerializer(instance, context=self.context).data


class DroneListSerializer(serializers.ModelSerializer):
    status_label = serializers.CharField(read_only=True)
    status_indicator = serializers.CharField(read_only=True)
    status_category = serializers.CharField(read_only=True)

    class Meta:
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
    class Meta:
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
    file = serializers.FileField(
        help_text="CSV file with drone inventory data.",
    )

    def validate_file(self, file):
        if not file.name.endswith(".csv"):
            raise serializers.ValidationError(
                "Only files with the extension .csv are allowed"
            )
        return file


class WriteOffRecordCreateSerializer(serializers.ModelSerializer):
    class Meta:
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
        drone = attrs.get("drone")
        related_mission = attrs.get("related_mission")

        if related_mission is not None:

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
        user = self.context["request"].user

        return create_writeoff_record(user=user, **validated_data)
