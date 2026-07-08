import codecs
import csv
import datetime
from decimal import Decimal

from django.conf import settings
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
        writeoff_reason_label = WriteOffRecord.label_for(
            writeoff_record.reason if writeoff_record else writeoff_reason
        )

        DroneStatusHistory.objects.create(
            drone=drone,
            from_status=old_status,
            to_status=drone.status,
            changed_by=user,
            reason=(
                status_change_reason
                or writeoff_reason_label
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

    for drone in queryset.iterator(chunk_size=2000):
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


def import_drones_csv(drones_csv_file, user=None):

    required_columns = {
        "Serial Number",
        "Inventory Number",
        "Name",
        "Model",
        "Military Unit",
        "Acquired At",
    }

    max_rows = getattr(settings, "DRONES_IMPORT_MAX_ROWS", 10000)
    batch_size = getattr(settings, "DRONES_IMPORT_BATCH_SIZE", 1000)

    try:
        decoded_file = codecs.iterdecode(drones_csv_file, "utf-8")
        reader_iterator = csv.DictReader(decoded_file)

        if not reader_iterator.fieldnames or not required_columns.issubset(
            set(reader_iterator.fieldnames)
        ):
            return {
                "success": False,
                "error": f"Invalid file format. Required columns: "
                f"{', '.join(required_columns)}",
            }

        rows = []

        for count, row in enumerate(reader_iterator):
            if count >= max_rows:
                return {
                    "success": False,
                    "error": f"File is too large. "
                    f"Maximum allowed is {max_rows} rows per import.",
                }
            rows.append(row)

    except UnicodeDecodeError:
        return {
            "success": False,
            "error": "Read file failed. "
            "Verify that it is a valid UTF-8 encoded text file.",
        }

    csv_serials = set()
    csv_invs = set()
    csv_models = set()
    csv_units = set()

    for row in rows:
        csv_serials.add(row.get("Serial Number", "").strip())
        csv_invs.add(row.get("Inventory Number", "").strip())
        csv_models.add(row.get("Model", "").strip())
        csv_units.add(row.get("Military Unit", "").strip())

    csv_serials.discard("")
    csv_invs.discard("")
    csv_models.discard("")
    csv_units.discard("")

    existing_serials = set(
        Drone.objects.filter(serial_number__in=csv_serials).values_list(
            "serial_number", flat=True
        )
    )
    existing_invs = set(
        Drone.objects.filter(inventory_number__in=csv_invs).values_list(
            "inventory_number", flat=True
        )
    )

    models_cache = {m.name: m for m in DroneModel.objects.filter(name__in=csv_models)}
    units_cache = {u.name: u for u in MilitaryUnit.objects.filter(name__in=csv_units)}

    errors = []
    valid_drones_data = []

    for row_num, row in enumerate(rows, start=2):
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

        if serial_number in existing_serials:
            errors.append(
                {
                    "row": row_num,
                    "error": f"Drone with serial number "
                    f"'{serial_number}' already exists.",
                }
            )
            continue

        if inventory_number in existing_invs:
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
                    "error": f"Invalid date format for "
                    f"Acquired At: '{acquired_at}'. Expected: YYYY-MM-DD.",
                }
            )
            continue

        military_unit = units_cache.get(military_unit_name)
        if not military_unit:
            errors.append(
                {
                    "row": row_num,
                    "error": f"Military unit '{military_unit_name}' not found.",
                }
            )
            continue

        drone_model_obj = models_cache.get(drone_model_name)
        if not drone_model_obj:
            errors.append(
                {
                    "row": row_num,
                    "error": f"Drone model '{drone_model_name}' not found.",
                }
            )
            continue

        valid_drones_data.append(
            {
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
                "row_num": row_num,
            }
        )

        existing_serials.add(serial_number)
        existing_invs.add(inventory_number)

    success_cnt = 0
    auth_user = _get_authenticated_user(user) if user else None

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

    static_audit_values = {
        k: _serialize_audit_value(v) for k, v in dummy_spec_data.items()
    }

    for i in range(0, len(valid_drones_data), batch_size):
        batch = valid_drones_data[i : i + batch_size]

        try:
            with transaction.atomic():
                drones_to_create = [
                    Drone(**{k: v for k, v in data.items() if k != "row_num"})
                    for data in batch
                ]

                created_drones = Drone.objects.bulk_create(
                    drones_to_create, batch_size=batch_size
                )

                specs_to_create = [
                    DroneSpec(drone=d, **dummy_spec_data) for d in created_drones
                ]
                created_specs = DroneSpec.objects.bulk_create(
                    specs_to_create, batch_size=batch_size
                )

                logs_to_create = [
                    DroneSpecChangeLog(
                        drone_spec=spec,
                        changed_by=auth_user,
                        changed_fields=list(dummy_spec_data.keys()),
                        old_values={},
                        new_values=static_audit_values,
                    )
                    for spec in created_specs
                ]
                DroneSpecChangeLog.objects.bulk_create(
                    logs_to_create, batch_size=batch_size
                )

                success_cnt += len(batch)

        except IntegrityError as e:
            start_row = batch[0]["row_num"]
            end_row = batch[-1]["row_num"]
            errors.append(
                {
                    "row": f"{start_row}-{end_row}",
                    "error": f"Batch insert failed due to database constraint "
                    f"(likely concurrent duplicate): {str(e)}",
                }
            )
        except Exception as e:
            start_row = batch[0]["row_num"]
            end_row = batch[-1]["row_num"]
            errors.append(
                {
                    "row": f"{start_row}-{end_row}",
                    "error": f"Unexpected batch failure: {str(e)}",
                }
            )

    return {
        "success": True,
        "added_count": success_cnt,
        "errors": errors,
    }


@transaction.atomic
def create_writeoff_record(
    *,
    drone,
    user,
    reason,
    reason_description="",
    document_number="",
    related_mission=None,
):
    user = _get_authenticated_user(user)

    old_status = drone.status
    drone.status = Drone.STATUS_WRITTEN_OFF
    drone.save(update_fields=["status"])

    writeoff_record = WriteOffRecord.objects.create(
        drone=drone,
        reason=reason,
        reason_description=reason_description,
        authorized_by=user,
        related_mission=related_mission,
        document_number=document_number,
    )

    DroneStatusHistory.objects.create(
        drone=drone,
        from_status=old_status,
        to_status=drone.status,
        changed_by=user,
        reason=writeoff_record.reason_label,
        related_mission=related_mission,
        related_writeoff=writeoff_record,
    )

    return writeoff_record
