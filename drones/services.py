from django.core.exceptions import ValidationError
from django.db import transaction

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


def _get_prepared_field_value(field, value):
    if field.is_relation and field.many_to_one:
        value = getattr(value, "pk", value)

    return field.get_prep_value(value)


def _field_value_changed(instance, field_name, new_value):
    field = instance._meta.get_field(field_name)

    if field.is_relation and field.many_to_one:
        old_value = getattr(instance, field.attname)
    else:
        old_value = getattr(instance, field_name)

    old_prepared_value = _get_prepared_field_value(field, old_value)
    new_prepared_value = _get_prepared_field_value(field, new_value)

    return old_prepared_value != new_prepared_value


def _update_instance_fields(instance, data):
    changed_fields = []

    for field_name, new_value in data.items():
        if _field_value_changed(instance, field_name, new_value):
            changed_fields.append(field_name)
            setattr(instance, field_name, new_value)

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
    related_mission=None,
):
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
        writeoff_record, _ = WriteOffRecord.objects.get_or_create(
            drone=drone,
            defaults={
                "reason": writeoff_reason,
                "reason_description": writeoff_reason_description,
                "authorized_by": user,
                "related_mission": related_mission,
                "document_number": document_number,
                "written_off_at": written_off_at,
            },
        )

    if old_status != drone.status:
        DroneStatusHistory.objects.create(
            drone=drone,
            from_status=old_status,
            to_status=drone.status,
            changed_by=user,
            reason=writeoff_reason
            or f"Status changed from {old_status} to {drone.status}",
            related_mission=related_mission,
            related_writeoff=writeoff_record,
        )

    return drone


def validate_drone_classification(drone_model, classification):
    allowed_classifications = drone_model.get_allowed_classifications()

    if classification not in allowed_classifications:
        raise ValidationError(
            {
                "classification": f'Classification "{classification}" '
                f'is not supported by drone model "{drone_model.name}". '
                f'Allowed: {", ".join([c.title() for c in allowed_classifications])}'
            }
        )
