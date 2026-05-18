from django.db import transaction
from django.utils import timezone

from .models import Drone, DroneSpec, DroneStatusHistory, WriteOffRecord


@transaction.atomic
def create_drone_with_spec(drone_data, spec_data):
    drone = Drone.objects.create(**drone_data)
    DroneSpec.objects.create(drone=drone, **spec_data)

    return drone


def _get_authenticated_user(user):
    if user and getattr(user, "is_authenticated", False):
        return user
    return None


def _update_instance_fields(instance, data):
    changed_fields = []

    for field, new_value in data.items():
        old_value = getattr(instance, field)

        if old_value != new_value:
            changed_fields.append(field)
            setattr(instance, field, new_value)

    return changed_fields


@transaction.atomic
def update_drone(
    *,
    drone,
    drone_data,
    spec_data=None,
    user=None,
    writeoff_reason="",
    writeoff_reason_description="",
    document_number="",
    written_off_at=None,
    related_mission_id=None): #must be changed when 'missions' are created
    user = _get_authenticated_user(user)

    old_status = drone.status
    requested_status = drone_data.get("status")
    is_decommission_flow = requested_status in Drone.INACTIVE_STATUSES

    drone_changed_fields = _update_instance_fields(drone, drone_data)

    if drone_changed_fields:
        drone.save()

    spec_changed_fields = []

    if spec_data is not None:
        try:
            spec = drone.spec
        except DroneSpec.DoesNotExist:
            spec = DroneSpec(drone=drone)

        spec_changed_fields = _update_instance_fields(spec, spec_data)

        if spec_changed_fields:
            spec.save()

    writeoff_record = None

    if is_decommission_flow:
        writeoff_record, _ = WriteOffRecord.objects.update_or_create(
            drone=drone,
            defaults={
                "reason": writeoff_reason,
                "reason_description": writeoff_reason_description,
                "authorized_by": user,
                "related_mission_id": related_mission_id, #must be changed when 'missions' are created
                "document_number": document_number,
                "written_off_at": written_off_at or timezone.localdate(),
            },
        )

    if old_status != drone.status:
        DroneStatusHistory.objects.create(
            drone=drone,
            from_status=old_status,
            to_status=drone.status,
            changed_by=user,
            reason=writeoff_reason or f"Status changed from {old_status} to {drone.status}",
            related_mission_id=related_mission_id, #must be changed when 'missions' are created
            related_writeoff=writeoff_record,
        )

    return drone
