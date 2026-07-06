"""Provide service-layer operations for drone inventory workflows.

Functions:
    create_drone_with_spec: Create a drone, specification, and initial audit log.
    update_drone: Update inventory/spec data and create lifecycle audit records.
    validate_drone_classification: Enforce model-to-classification compatibility.
    generate_drones_csv: Stream drone inventory rows as CSV.
    import_drones_csv: Import drones from CSV with row-level validation errors.
    create_writeoff_record: Write off a drone and record status history.
"""

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
    """Convert model, decimal, and date values into JSON-safe audit values."""
    if isinstance(value, Decimal):
        return str(value)

    if isinstance(value, (datetime.date, datetime.datetime)):
        return value.isoformat()

    if hasattr(value, "pk"):
        return value.pk

    return value


@transaction.atomic
def create_drone_with_spec(drone_data, spec_data, user=None):
    """Create a drone, its specification, and the initial audit entry atomically.

    Args:
        drone_data: Validated Drone field values.
        spec_data: Validated DroneSpec field values.
        user: User responsible for the creation event.

    Returns:
        The created Drone instance.

    Side effects:
        Creates DroneSpec and DroneSpecChangeLog records in the same transaction.
    """
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
    """Return the user only when it is authenticated."""
    if user and getattr(user, "is_authenticated", False):
        return user
    return None


def _get_prepared_field_value(field, value):
    """Normalize a field value before comparing it for model changes."""
    if field.is_relation and field.many_to_one:
        value = getattr(value, "pk", value)

    return field.get_prep_value(value)


def _field_value_changed(instance, field_name, new_value):
    """Return whether a submitted value differs from the stored field value."""
    field = instance._meta.get_field(field_name)

    if field.is_relation and field.many_to_one:
        old_value = getattr(instance, field.attname)
    else:
        old_value = getattr(instance, field_name)

    old_prepared_value = _get_prepared_field_value(field, old_value)
    new_prepared_value = _get_prepared_field_value(field, new_value)

    return old_prepared_value != new_prepared_value


def _get_changed_fields(instance, data):
    """Return field names whose submitted values would change the instance."""
    return [
        field_name
        for field_name, new_value in data.items()
        if _field_value_changed(instance, field_name, new_value)
    ]


def _set_instance_fields(instance, data, field_names):
    """Assign submitted values to the selected instance fields."""
    for field_name in field_names:
        setattr(instance, field_name, data[field_name])


def _update_instance_fields(instance, data):
    """Assign changed values to an instance and return changed field names."""
    changed_fields = _get_changed_fields(instance, data)
    _set_instance_fields(instance, data, changed_fields)

    return changed_fields


def _create_spec_change_log(*, spec, changed_fields, old_values, user):
    """Create a specification audit entry when at least one field changed."""
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
    """Update a drone and record specification/status audit events atomically.

    Applies changed Drone fields, optionally updates or creates DroneSpec, and
    writes DroneSpecChangeLog entries for existing specification changes. When
    the requested status is inactive, the service creates or reuses the drone's
    immutable WriteOffRecord and links it to DroneStatusHistory.

    Args:
        drone: Drone instance being updated.
        drone_data: Validated Drone field values.
        spec_data: Optional validated DroneSpec field values.
        user: User responsible for the update.
        writeoff_reason: Canonical write-off reason for inactive transitions.
        writeoff_reason_description: Optional human-readable write-off details.
        document_number: Optional write-off document reference.
        written_off_at: Date when the drone was written off.
        related_mission: Optional mission that caused the transition.
        status_change_reason: Optional explicit status history reason.

    Returns:
        The updated Drone instance.

    Side effects:
        May create DroneSpecChangeLog, WriteOffRecord, and DroneStatusHistory.
    """
    user = _get_authenticated_user(user)

    old_status = drone.status
    requested_status = drone_data.get("status")
    # Any transition into an inactive status is treated as a decommission/write-off
    # flow and requires the metadata validated by DroneUpdateSerializer.
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
            # Only existing specs receive update audit entries; a newly attached
            # spec has no previous values to compare against.
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
        # Write-off records are append-only. Reusing the existing record prevents
        # repeated inactive-status updates from changing the original audit data.
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

        # Status history records the business event, not only the field update.
        # Prefer the explicit user reason, then the canonical write-off label.
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
    """Raise a validation error when a model does not support a classification."""
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
    """Yield CSV rows for the supplied drone queryset."""
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
    """Import drone inventory records from a UTF-8 CSV file.

    Valid rows are created while invalid rows are collected as row-level errors.
    The current import creates placeholder technical specifications because
    DroneSpec fields are required by the database schema.

    Args:
        drones_csv_file: Uploaded CSV file object.
        user: User responsible for the import.

    Returns:
        A dictionary with success status, created row count, and row errors.
    """
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

        # TODO: CSV import cannot know the full technical specification yet, but
        # DroneSpec fields are currently NOT NULL. Make spec fields nullable or
        # move spec creation to a follow-up enrichment step, then remove these
        # placeholder values.
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
    """Write off a drone and create the matching status history entry atomically.

    Args:
        drone: Active Drone instance being written off.
        user: User authorizing the write-off.
        reason: Canonical write-off reason code.
        reason_description: Optional human-readable reason details.
        document_number: Optional source document reference.
        related_mission: Optional mission associated with the write-off.

    Returns:
        The created WriteOffRecord.

    Side effects:
        Changes the drone status to WRITTEN_OFF and creates DroneStatusHistory.
    """
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
