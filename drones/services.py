import datetime
from decimal import Decimal

from django.db import transaction

from .models import (
    Drone,
    DroneSpec,
    DroneSpecChangeLog,
    DroneStatusHistory,
    WriteOffRecord,
)


def _serialize_audit_value(value):
    if isinstance(value, Decimal):
        return str(value)

    if isinstance(value, (datetime.date, datetime.datetime)):
        return value.isoformat()

    if hasattr(value, "pk"):
        return value.pk

    return value


@transaction.atomic
def create_drone_with_spec(drone_data, spec_data, user=None):
    user = _get_authenticated_user(user)

    drone = Drone.objects.create(**drone_data)
    spec = DroneSpec.objects.create(drone=drone, **spec_data)

    DroneSpecChangeLog.objects.create(
        drone_spec=spec,
        changed_by=user,
        changed_fields=list(spec_data.keys()),
        old_values={},
        new_values={
            field_name: _serialize_audit_value(getattr(spec, field_name))
            for field_name in spec_data.keys()
        },
    )

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


def _create_spec_change_log(*, spec, changed_fields, old_values, user):
    if not changed_fields:
        return

    new_values = {
        field_name: _serialize_audit_value(getattr(spec, field_name))
        for field_name in changed_fields
    }

    DroneSpecChangeLog.objects.create(
        drone_spec=spec,
        changed_by=user,
        changed_fields=changed_fields,
        old_values=old_values,
        new_values=new_values,
    )


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
            spec_was_created = False
        except DroneSpec.DoesNotExist:
            spec = DroneSpec(drone=drone)
            spec_was_created = True

        old_spec_values = {}
        if not spec_was_created:
            old_spec_values = {
                field_name: _serialize_audit_value(getattr(spec, field_name, None))
                for field_name in spec_data.keys()
            }

        spec_changed_fields = _update_instance_fields(spec, spec_data)

        if spec_changed_fields:
            spec.save()
            _create_spec_change_log(
                spec=spec,
                changed_fields=spec_changed_fields,
                old_values={
                    field_name: old_spec_values.get(field_name)
                    for field_name in spec_changed_fields
                },
                user=user,
            )

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
