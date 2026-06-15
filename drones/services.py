import csv
import datetime
import io
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction

from accounts.models import MilitaryUnit
from common.utils import EchoBuffer

from .models import (
    Drone,
    DroneModel,
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


def _get_changed_fields(instance, data):
    return [
        field_name
        for field_name, new_value in data.items()
        if _field_value_changed(instance, field_name, new_value)
    ]


def _set_instance_fields(instance, data, field_names):
    for field_name in field_names:
        setattr(instance, field_name, data[field_name])


def _update_instance_fields(instance, data):
    changed_fields = _get_changed_fields(instance, data)
    _set_instance_fields(instance, data, changed_fields)

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
    status_change_reason="",
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

        spec_changed_fields = _get_changed_fields(spec, spec_data)
        old_spec_values = {}

        if spec_changed_fields:
            if not spec_was_created:
                old_spec_values = {
                    field_name: _serialize_audit_value(getattr(spec, field_name))
                    for field_name in spec_changed_fields
                }

            _set_instance_fields(spec, spec_data, spec_changed_fields)
            spec.save()

            if not spec_was_created:
                _create_spec_change_log(
                    spec=spec,
                    changed_fields=spec_changed_fields,
                    old_values=old_spec_values,
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
            reason=(
                status_change_reason
                or writeoff_reason
                or f"Status changed from {old_status} to {drone.status}"
            ),
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


def generate_drones_csv(queryset):

    buffer = EchoBuffer()
    writer = csv.writer(buffer)

    yield writer.writerow(
        [
            "ID",
            "Serial Number",
            "Inventory Number",
            "Name",
            "Model",
            "Classification",
            "Status",
            "Military Unit",
            "Created At",
        ]
    )

    for drone in queryset:
        yield writer.writerow(
            [
                drone.id,
                drone.serial_number,
                drone.inventory_number,
                drone.name,
                drone.drone_model,
                drone.get_classification_display(),
                drone.get_status_display(),
                drone.military_unit.name if drone.military_unit else "",
                (
                    drone.created_at.strftime("%Y-%m-%d %H:%M:%S")
                    if drone.created_at
                    else ""
                ),
            ]
        )


@transaction.atomic
def import_drones_csv(drones_csv_file, user=None):
    try:
        decoded_file = drones_csv_file.read().decode("utf-8")
    except UnicodeDecodeError:
        return {
            "success": False,
            "error": "Read file soon. "
            "Verify that it is a valid UTF-8 encoded text file. ",
        }

    io_string = io.StringIO(decoded_file)

    reader = csv.DictReader(io_string)

    required_columns = {
        "Serial Number",
        "Inventory Number",
        "Name",
        "Model",
        "Military Unit",
        "Acquired At",
    }

    if not reader.fieldnames or not required_columns.issubset(set(reader.fieldnames)):
        return {
            "success": False,
            "error": f"Invalid file format. Required columns: "
            f"{', '.join(required_columns)}",
        }

    success_cnt = 0
    errors = []

    for row_num, row in enumerate(reader, start=2):
        serial_number = row.get("Serial Number", "").strip()
        inventory_number = row.get("Inventory Number", "").strip()
        name = row.get("Name", "").strip()
        drone_model_name = row.get("Model", "").strip()
        military_unit_name = row.get("Military Unit", "").strip()
        acquired_at = row.get("Acquired At", "").strip()

        if not all(
            [
                serial_number,
                inventory_number,
                name,
                drone_model_name,
                military_unit_name,
                acquired_at,
            ]
        ):
            errors.append(
                {"row": row_num, "error": "Missing one or more required fields."}
            )
            continue

        if Drone.objects.filter(serial_number=serial_number).exists():
            errors.append(
                {
                    "row": row_num,
                    "error": f"Drone with serial number "
                    f"'{serial_number}' already exists.",
                }
            )
            continue

        if Drone.objects.filter(inventory_number=inventory_number).exists():
            errors.append(
                {
                    "row": row_num,
                    "error": f"Drone with inventory number "
                    f"'{inventory_number}' already exists.",
                }
            )
            continue

        try:
            datetime.datetime.strptime(acquired_at, "%Y-%m-%d")
        except ValueError:
            errors.append(
                {
                    "row": row_num,
                    "error": f"Invalid date format for Acquired At: "
                    f"'{acquired_at}'. Expected format: YYYY-MM-DD.",
                }
            )
            continue

        try:
            military_unit = MilitaryUnit.objects.get(name=military_unit_name)
        except MilitaryUnit.DoesNotExist:
            errors.append(
                {
                    "row": row_num,
                    "error": f"Military unit "
                    f"'{military_unit_name}' not found in database.",
                }
            )
            continue

        try:
            drone_model_obj = DroneModel.objects.get(name=drone_model_name)
        except DroneModel.DoesNotExist:
            errors.append(
                {
                    "row": row_num,
                    "error": f"Drone model '{drone_model_name}' not found in database.",
                }
            )
            continue

        drone_data = {
            "serial_number": serial_number,
            "inventory_number": inventory_number,
            "name": name,
            "drone_model": drone_model_obj,
            "classification": (
                drone_model_obj.supported_classifications[0]
                if drone_model_obj.supported_classifications
                else "RECONNAISSANCE"
            ),
            "military_unit": military_unit,
            "acquired_at": acquired_at,
        }

        # TODO: This is a stub to work around the NOT NULL restrictions in DroneSpec.
        # In the future specification field, it is worth making null=True/blank=True,
        # then when importing according to the technical details unknown.
        dummy_spec_data = {
            "frame_type": "Unknown",
            "motor_model": "Unknown",
            "battery_type": "Unknown",
            "battery_capacity_mah": 0,
            "camera_model": "Unknown",
            "flight_controller": "Unknown",
            "max_speed_kmh": "0.00",
            "max_range_km": "0.00",
            "max_flight_time_min": "0.00",
            "frequency_mhz": 0,
        }

        try:
            create_drone_with_spec(drone_data, spec_data=dummy_spec_data, user=user)
            success_cnt += 1
        except IntegrityError:
            errors.append(
                {
                    "row": row_num,
                    "error": f"Database constraint error: "
                    f"Drone with serial number '{serial_number}' "
                    f"or inventory number "
                    f"'{inventory_number}' was just created by another process.",
                }
            )
        except Exception as e:
            errors.append({"row": row_num, "error": f"Failed to create: {str(e)}"})

    return {
        "success": True,
        "added_count": success_cnt,
        "errors": errors,
    }
