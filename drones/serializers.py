from rest_framework import serializers

from .models import Drone, DroneSpec, DroneStatusHistory, WriteOffRecord
from .services import create_drone_with_spec, update_drone


class DroneSpecSerializer(serializers.ModelSerializer):

    class Meta:
        model = DroneSpec
        exclude = ("drone",)
        
        
class DroneSpecUpdateSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = DroneSpec
        exclude = ("drone",)
        extra_kwargs = {
            "frame_type": {"required": False},
            "motor_model": {"required": False},
            "battery_type": {"required": False},
            "battery_capacity_mah": {"required": False},
            "camera_model": {"required": False},
            "vtx_model": {"required": False},
            "flight_controller": {"required": False},
            "firmware_version": {"required": False},
            "max_speed_kmh": {"required": False},
            "max_range_km": {"required": False},
            "max_flight_time_min": {"required": False},
            "frequency_mhz": {"required": False},
            "payload_capacity_g": {"required": False},
        }
        

class WriteOffRecordSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = WriteOffRecord
        fields = (
            "id",
            "reason",
            "reason_description",
            "authorized_by",
            "related_mission_id", #must be changed when 'missions' are created
            "document_number",
            "written_off_at",
            "created_at",
        )
        read_only_fields = fields


class DroneStatusHistorySerializer(serializers.ModelSerializer):
    
    class Meta:
        model = DroneStatusHistory
        fields = (
            "id",
            "from_status",
            "to_status",
            "changed_by",
            "reason",
            "related_mission_id", #must be changed when 'missions' are created
            "related_repair_order_id", #must be changed 
            "related_writeoff",
            "created_at",
        )
        read_only_fields = fields


class DroneSerializer(serializers.ModelSerializer):
    spec = DroneSpecSerializer()
    writeoff_record = WriteOffRecordSerializer(read_only=True)
    status_history = DroneStatusHistorySerializer(many=True, read_only=True)

    class Meta:
        model = Drone
        fields = "__all__"

    def create(self, validated_data):
        spec_data = validated_data.pop("spec")

        return create_drone_with_spec(drone_data=validated_data, spec_data=spec_data)
    

class DroneUpdateSerializer(serializers.ModelSerializer):
    spec = DroneSpecUpdateSerializer(required=False)

    writeoff_reason = serializers.CharField(
        write_only=True,
        required=False,
        allow_blank=True,
    )
    writeoff_reason_description = serializers.CharField(
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
    related_mission_id = serializers.IntegerField(
        write_only=True,
        required=False,
        min_value=1,
    )

    class Meta:
        model = Drone
        fields = (
            "serial_number",
            "inventory_number",
            "name",
            "drone_model",
            "status",
            "military_unit",
            "acquired_at",
            "notes",
            "spec",
            "writeoff_reason",
            "writeoff_reason_description",
            "document_number",
            "written_off_at",
            "related_mission_id", #must be changed when 'missions' are created
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
        writeoff_reason = attrs.get("writeoff_reason", "")

        if requested_status in Drone.INACTIVE_STATUSES and not writeoff_reason.strip():
            raise serializers.ValidationError(
                {
                    "writeoff_reason": (
                        "This field is required when drone is decommissioned, "
                        "sold, transferred, or written off."
                    )
                }
            )

        return attrs

    def update(self, instance, validated_data):
        spec_data = validated_data.pop("spec", None)

        writeoff_reason = validated_data.pop("writeoff_reason", "")
        writeoff_reason_description = validated_data.pop(
            "writeoff_reason_description",
            "",
        )
        document_number = validated_data.pop("document_number", "")
        written_off_at = validated_data.pop("written_off_at", None)
        related_mission_id = validated_data.pop("related_mission_id", None)

        request = self.context.get("request")
        user = getattr(request, "user", None)

        return update_drone(
            drone=instance,
            drone_data=validated_data,
            spec_data=spec_data,
            user=user,
            writeoff_reason=writeoff_reason,
            writeoff_reason_description=writeoff_reason_description,
            document_number=document_number,
            written_off_at=written_off_at,
            related_mission_id=related_mission_id, #must be changed when 'missions' are created
        )

    def to_representation(self, instance):
        return DroneSerializer(instance, context=self.context).data
