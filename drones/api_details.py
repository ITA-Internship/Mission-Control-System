from drf_spectacular.utils import OpenApiExample, OpenApiParameter, OpenApiResponse
from rest_framework import status

from common.api_description_schema import description_schema
from config.settings import MAX_EXPORT_LIMIT
from drones.serializers import (
    DroneImportSerializer,
    DroneListSerializer,
    DroneModelSerializer,
    DroneSerializer,
    DroneSpecChangeLogSerializer,
    DroneStatusHistorySerializer,
    DroneUpdateSerializer,
    WriteOffAuditSerializer,
    WriteOffRecordCreateSerializer,
    WriteOffRecordSerializer,
)

drone_example_value = {
    "id": 21,
    "spec": {
        "id": 21,
        "frame_type": "7-inch carbon frame",
        "motor_model": "XING2 2806.5 1300KV",
        "battery_type": "Li-Ion 6S",
        "battery_capacity_mah": 4000,
        "battery_model": "",
        "camera_model": "RunCam Phoenix 2",
        "camera_specs": {},
        "vtx_model": "Rush Tank Solo",
        "flight_controller": "Matek H743",
        "firmware_version": "INAV 7.1",
        "is_firmware_outdated": False,
        "communication_protocol": "",
        "control_channel": "",
        "telemetry_channel": "",
        "max_speed_kmh": "118.50",
        "typical_range_km": "14.60",
        "max_range_km": "18.20",
        "typical_flight_time_min": "21.00",
        "max_flight_time_min": "24.00",
        "frequency_mhz": 5800,
        "payload_capacity_g": 250,
        "additional_modules": [],
        "technical_documentation_url": "",
        "firmware_file_url": "",
        "updated_at": "2026-07-02T02:21:31.177903Z",
        "change_history": [],
    },
    "writeoff_record": None,
    "status_history": [],
    "status_label": "Active",
    "status_indicator": "success",
    "status_category": "available",
    "serial_number": "FPV-AER-24001",
    "inventory_number": "INV-AER-001",
    "name": "Falcon Eye 1",
    "classification": "RECONNAISSANCE",
    "status": "ACTIVE",
    "acquired_at": "2025-01-12",
    "notes": "Recon platform configured for stable daytime observation sorties.",
    "created_at": "2026-07-02T02:21:31.174390Z",
    "updated_at": "2026-07-02T02:21:31.174396Z",
    "drone_model": 15,
    "military_unit": 7,
}

drone_model_example_value = {
    "id": 18,
    "name": "Atlas Relay 8",
    "manufacturer": "Quantum Systems",
    "description": "Long-endurance signal relay and perimeter monitoring platform.",
    "supported_classifications": ["TRANSPORT", "SURVEILLANCE"],
    "is_active": True,
    "created_at": "2026-07-02T02:21:31.163658Z",
    "updated_at": "2026-07-02T02:21:31.163664Z",
}

drone_get_schema = description_schema(
    summary="List drones",
    description=(
        "Retrieves a paginated and filtered list of all drones in the system.\n\n"
        "By default list displays only drones with active statuses. "
        "Choose one of the inactive statuses during filtration "
        "to get drones with inactive status."
    ),
    permission_code="PERMISSION_DRONES_VIEW",
    request=DroneListSerializer,
    responses={
        status.HTTP_200_OK: OpenApiResponse(
            response=DroneListSerializer(many=True),
            description="Successfully retrieved the list of drones.",
        ),
    },
    error_statuses=[status.HTTP_403_FORBIDDEN],
    examples=[
        OpenApiExample(
            name="Get list of all active drones",
            value={
                "id": 21,
                "serial_number": "FPV-AER-24001",
                "inventory_number": "INV-AER-001",
                "name": "Falcon Eye 1",
                "drone_model": 15,
                "classification": "RECONNAISSANCE",
                "status": "ACTIVE",
                "status_label": "Active",
                "status_indicator": "success",
                "status_category": "available",
                "military_unit": 7,
                "created_at": "2026-07-02T02:21:31.174390Z",
            },
        ),
        OpenApiExample(
            name="Get list of all written-off drones",
            value={
                "id": 29,
                "serial_number": "FPV-ATK-24009",
                "inventory_number": "INV-ATK-009",
                "name": "Lancer 1",
                "drone_model": 21,
                "classification": "COMBAT",
                "status": "WRITTEN_OFF",
                "status_label": "Written off",
                "status_indicator": "danger",
                "status_category": "written_off",
                "military_unit": 8,
                "created_at": "2026-07-02T02:21:31.218672Z",
            },
        ),
    ],
)

drone_post_schema = description_schema(
    summary="Create a new drone",
    description="Creates a new drone with its technical specification. "
    "Creates an audit log entry with all spec values written down as `new_values`. \n\n"
    "Validation: \n"
    "- Classification of a drone must be supported by its model.",
    permission_code="PERMISSION_DRONES_CREATE",
    request=DroneSerializer,
    responses={
        status.HTTP_201_CREATED: OpenApiResponse(
            response=DroneSerializer, description="Drone created successfully."
        ),
        status.HTTP_400_BAD_REQUEST: OpenApiResponse(
            description="Bad Request",
            response=dict,
            examples=[
                OpenApiExample(
                    name="Invalid supported classification",
                    value={
                        "classification": (
                            'Classification "RECONNAISSANCE" is not supported by '
                            'drone model "Atlas Relay 8". '
                            "Allowed: Transport, Surveillance"
                        )
                    },
                )
            ],
        ),
    },
    error_statuses=[status.HTTP_403_FORBIDDEN],
    examples=[
        OpenApiExample(
            name="Valid Request",
            value={
                "id": 32,
                "spec": {
                    "id": 32,
                    "frame_type": "7-inch carbon frame",
                    "motor_model": "XING2 2806.5 1300KV",
                    "battery_type": "Li-Ion 6S",
                    "battery_capacity_mah": 4000,
                    "battery_model": "",
                    "camera_model": "RunCam Phoenix 2",
                    "camera_specs": {},
                    "vtx_model": "Rush Tank Solo",
                    "flight_controller": "Matek H743",
                    "firmware_version": "INAV 7.1",
                    "is_firmware_outdated": False,
                    "communication_protocol": "",
                    "control_channel": "",
                    "telemetry_channel": "",
                    "max_speed_kmh": "118.50",
                    "typical_range_km": "14.60",
                    "max_range_km": "18.20",
                    "typical_flight_time_min": "21.00",
                    "max_flight_time_min": "24.00",
                    "frequency_mhz": 5800,
                    "payload_capacity_g": 250,
                    "additional_modules": [],
                    "technical_documentation_url": "",
                    "firmware_file_url": "",
                    "updated_at": "2026-07-03T00:40:00.799313Z",
                    "change_history": [
                        {
                            "id": 2,
                            "changed_by": 24,
                            "changed_fields": [
                                "frame_type",
                                "motor_model",
                                "battery_type",
                                "battery_capacity_mah",
                                "camera_model",
                                "vtx_model",
                                "flight_controller",
                                "firmware_version",
                                "is_firmware_outdated",
                                "max_speed_kmh",
                                "typical_range_km",
                                "max_range_km",
                                "typical_flight_time_min",
                                "max_flight_time_min",
                                "frequency_mhz",
                                "payload_capacity_g",
                            ],
                            "old_values": {},
                            "new_values": {
                                "vtx_model": "Rush Tank Solo",
                                "frame_type": "7-inch carbon frame",
                                "motor_model": "XING2 2806.5 1300KV",
                                "battery_type": "Li-Ion 6S",
                                "camera_model": "RunCam Phoenix 2",
                                "max_range_km": "18.20",
                                "frequency_mhz": 5800,
                                "max_speed_kmh": "118.50",
                                "firmware_version": "INAV 7.1",
                                "typical_range_km": "14.60",
                                "flight_controller": "Matek H743",
                                "payload_capacity_g": 250,
                                "max_flight_time_min": "24.00",
                                "battery_capacity_mah": 4000,
                                "is_firmware_outdated": False,
                                "typical_flight_time_min": "21.00",
                            },
                            "created_at": "2026-07-03T00:40:00.800251Z",
                        }
                    ],
                },
                "writeoff_record": None,
                "status_history": [],
                "status_label": "Active",
                "status_indicator": "success",
                "status_category": "available",
                "serial_number": "FPV-AER-24001",
                "inventory_number": "INV-AER-001",
                "name": "Falcon Eye 1",
                "classification": "RECONNAISSANCE",
                "status": "ACTIVE",
                "acquired_at": "2025-01-12",
                "notes": (
                    "Recon platform configured for stable daytime observation sorties."
                ),
                "created_at": "2026-07-03T00:40:00.798536Z",
                "updated_at": "2026-07-03T00:40:00.798549Z",
                "drone_model": 15,
                "military_unit": 7,
            },
            response_only=True,
        ),
        OpenApiExample(
            name="Valid Request",
            request_only=True,
            value={
                "spec": {
                    "frame_type": "7-inch carbon frame",
                    "motor_model": "XING2 2806.5 1300KV",
                    "battery_type": "Li-Ion 6S",
                    "battery_capacity_mah": 4000,
                    "camera_model": "RunCam Phoenix 2",
                    "vtx_model": "Rush Tank Solo",
                    "flight_controller": "Matek H743",
                    "firmware_version": "INAV 7.1",
                    "is_firmware_outdated": False,
                    "max_speed_kmh": "118.50",
                    "typical_range_km": "14.60",
                    "max_range_km": "18.20",
                    "typical_flight_time_min": "21.00",
                    "max_flight_time_min": "24.00",
                    "frequency_mhz": 5800,
                    "payload_capacity_g": 250,
                },
                "status_label": "Active",
                "status_indicator": "success",
                "status_category": "available",
                "serial_number": "FPV-AER-24001",
                "inventory_number": "INV-AER-001",
                "name": "Falcon Eye 1",
                "classification": "RECONNAISSANCE",
                "status": "ACTIVE",
                "acquired_at": "2025-01-12",
                "notes": (
                    "Recon platform configured for stable daytime observation sorties."
                ),
                "drone_model": 15,
                "military_unit": 7,
            },
        ),
    ],
)

drone_detail_get_schema = description_schema(
    summary="Retrieve drone details",
    description="Retrieves detailed information about a specific drone by its ID, "
    "including technical specification and history.",
    permission_code="PERMISSION_DRONES_VIEW",
    request=DroneSerializer,
    parameters=[
        OpenApiParameter(
            name="id",
            type=int,
            location=OpenApiParameter.PATH,
            description="ID of specific drone.",
        )
    ],
    responses={
        status.HTTP_200_OK: OpenApiResponse(
            response=DroneSerializer,
            description="Detailed information about the drone.",
        ),
    },
    error_statuses=[status.HTTP_403_FORBIDDEN, status.HTTP_404_NOT_FOUND],
    examples=[OpenApiExample(name="Valid request", value=drone_example_value)],
)

drone_detail_patch_schema = description_schema(
    summary="Partially update a drone",
    description="Updates specific fields of an existing drone record.\n\n"
    "Validation: \n"
    "- New classification of a drone must be supported by its model. \n"
    "- If a drone is being decommissioned, sold, transferred, or written off "
    "the reason must be provided.",
    permission_code="PERMISSION_DRONES_UPDATE",
    request=DroneUpdateSerializer,
    responses={
        status.HTTP_200_OK: OpenApiResponse(
            response=DroneSerializer, description="Drone updated successfully."
        ),
        status.HTTP_400_BAD_REQUEST: OpenApiResponse(
            description="Bad Request",
            response=dict,
            examples=[
                OpenApiExample(
                    name="Missing write-off reason",
                    value={
                        "writeoff_reason": (
                            "This field is required when drone is "
                            "decommissioned, sold, transferred, or written off."
                        )
                    },
                ),
                OpenApiExample(
                    name="Invalid supported classification",
                    value={
                        "classification": (
                            'Classification "RECONNAISSANCE" is not supported '
                            'by drone model "Atlas Relay 8". '
                            "Allowed: Transport, Surveillance"
                        )
                    },
                ),
            ],
        ),
    },
    error_statuses=[status.HTTP_403_FORBIDDEN, status.HTTP_404_NOT_FOUND],
    examples=[
        OpenApiExample(
            name="Valid Request", value=drone_example_value, response_only=True
        ),
        OpenApiExample(
            name="Valid Request", value={"name": "Falcon Eye 1"}, request_only=True
        ),
    ],
)

drone_model_get_schema = description_schema(
    summary="List drone models",
    description="Retrieves a list of all drone models.",
    permission_code="PERMISSION_DRONES_VIEW",
    request=DroneModelSerializer,
    responses={
        status.HTTP_200_OK: OpenApiResponse(
            response=DroneModelSerializer,
            description="Successfully retrieved the list of drone models.",
        ),
    },
    error_statuses=[status.HTTP_403_FORBIDDEN],
    examples=[
        OpenApiExample(
            name="Valid Request",
            value=drone_model_example_value,
        ),
    ],
)

drone_model_post_schema = description_schema(
    summary="Create a new drone model",
    description="Creates a new drone model in the system. \n\n"
    "Validation: \n"
    "- Drone model must have at least one valid supported classification.",
    permission_code="PERMISSION_DRONES_CREATE",
    request=DroneModelSerializer,
    responses={
        status.HTTP_200_OK: OpenApiResponse(
            response=DroneModelSerializer,
            description="Drone model created successfully.",
        ),
        status.HTTP_400_BAD_REQUEST: OpenApiResponse(
            description="Bad Request",
            response=dict,
            examples=[
                OpenApiExample(
                    name="Supported classification not provided",
                    value={
                        "supported_classifications": (
                            "A drone model must support at least one classification."
                        )
                    },
                ),
                OpenApiExample(
                    name="Invalid supported classification",
                    value={
                        "supported_classifications": (
                            "Value ['Example classification'] are not "
                            "valid classifications. "
                            "Valid classifications: "
                            "RECONNAISSANCE, COMBAT, TRANSPORT, SURVEILLANCE"
                        )
                    },
                ),
            ],
        ),
    },
    error_statuses=[status.HTTP_403_FORBIDDEN],
    examples=[
        OpenApiExample(
            name="Valid Request",
            value={
                "name": "Atlas Relay 8",
                "manufacturer": "Quantum Systems",
                "description": (
                    "Long-endurance signal relay and perimeter monitoring platform."
                ),
                "supported_classifications": ["TRANSPORT", "SURVEILLANCE"],
            },
            request_only=True,
        ),
        OpenApiExample(
            name="Valid Request", value=drone_model_example_value, response_only=True
        ),
    ],
)

drone_data_export_schema = description_schema(
    summary="Export drones data to CSV",
    description=(
        "Generates and downloads a CSV file with the filtered list of drones. "
        "Supports full filtering and sorting "
        "identical to the standard list endpoint. \n\n"
        f"The export is limited to a maximum of {MAX_EXPORT_LIMIT} records. "
    ),
    permission_code="PERMISSION_DRONES_VIEW",
    responses={
        200: OpenApiResponse(
            description="A CSV file containing drone data generated successfully.",
        ),
    },
    error_statuses=[status.HTTP_403_FORBIDDEN],
)

drone_data_import_schema = description_schema(
    summary="Import drones data via CSV",
    description=(
        "Uploads a CSV file to batch-import drone data. "
        "Processes the file record row by row, "
        "validates data and return error logs if any. "
        "Rows with existing `Serial Number`s will be skipped "
        "and reported in the API error summary.\n\n"
        "Validation: \n"
        "- In uploaded .csv file following headers must be present: "
        "Serial Number, Inventory Number, Name, Model, Military Unit, Acquired At. \n"
        "- `Military Unit` must exactly match the name "
        "of an existing unit in the database."
    ),
    permission_code="PERMISSION_DRONES_CREATE",
    request=DroneImportSerializer,
    responses={
        status.HTTP_200_OK: OpenApiResponse(description="Import processing completed."),
    },
    error_statuses=[status.HTTP_400_BAD_REQUEST, status.HTTP_403_FORBIDDEN],
)

drone_status_history_example_value = {
    "id": 12,
    "from_status": "ACTIVE",
    "to_status": "IN_MISSION",
    "changed_by": 24,
    "changed_by_display": "oleksandr.koval",
    "reason": "Assigned to reconnaissance sortie.",
    "event_type": "mission",
    "related_mission_id": 5,
    "related_repair_order": None,
    "related_writeoff": None,
    "created_at": "2026-07-02T02:21:31.177903Z",
}

drone_status_history_get_schema = description_schema(
    summary="List drone status history",
    description=(
        "Retrieves a paginated, read-only history of lifecycle status changes for "
        "a specific drone, ordered from newest to oldest. Each entry exposes an "
        "`event_type` (`mission`, `repair`, `writeoff`, or `status_change`) that "
        "explains what caused the transition."
    ),
    permission_code="PERMISSION_DRONES_VIEW",
    parameters=[
        OpenApiParameter(
            name="id",
            type=int,
            location=OpenApiParameter.PATH,
            description="ID of the drone whose status history is being retrieved.",
            required=True,
        ),
    ],
    request=None,
    responses={
        status.HTTP_200_OK: OpenApiResponse(
            response=DroneStatusHistorySerializer(many=True),
            description="Successfully retrieved the drone status history.",
        ),
    },
    error_statuses=[status.HTTP_403_FORBIDDEN, status.HTTP_404_NOT_FOUND],
    examples=[
        OpenApiExample(
            name="Valid request",
            response_only=True,
            value=drone_status_history_example_value,
        ),
    ],
)

drone_spec_changes_example_value = {
    "id": 2,
    "changed_by": 24,
    "changed_fields": ["firmware_version", "max_speed_kmh"],
    "old_values": {"firmware_version": "INAV 7.0", "max_speed_kmh": "110.00"},
    "new_values": {"firmware_version": "INAV 7.1", "max_speed_kmh": "118.50"},
    "created_at": "2026-07-03T00:40:00.800251Z",
}

drone_spec_changes_get_schema = description_schema(
    summary="List drone specification change history",
    description=(
        "Retrieves a paginated, read-only audit trail of technical specification "
        "changes for a specific drone, ordered from newest to oldest. Each entry "
        "records which fields changed together with their previous and new values."
    ),
    permission_code="PERMISSION_DRONES_VIEW",
    parameters=[
        OpenApiParameter(
            name="id",
            type=int,
            location=OpenApiParameter.PATH,
            description=(
                "ID of the drone whose specification change history is retrieved."
            ),
            required=True,
        ),
    ],
    request=None,
    responses={
        status.HTTP_200_OK: OpenApiResponse(
            response=DroneSpecChangeLogSerializer(many=True),
            description="Successfully retrieved the specification change history.",
        ),
    },
    error_statuses=[status.HTTP_403_FORBIDDEN, status.HTTP_404_NOT_FOUND],
    examples=[
        OpenApiExample(
            name="Valid request",
            response_only=True,
            value=drone_spec_changes_example_value,
        ),
    ],
)

writeoff_audit_example_value = {
    "id": 3,
    "drone_id": 29,
    "drone_name": "Lancer 1",
    "drone_serial_number": "FPV-ATK-24009",
    "drone_inventory_number": "INV-ATK-009",
    "reason": "LOSS",
    "reason_description": "Lost during combat sortie behind enemy lines.",
    "authorized_by": 24,
    "authorized_by_username": "oleksandr.koval",
    "related_mission": 5,
    "related_mission_id": 5,
    "document_number": "WO-2026-0009",
    "written_off_at": "2026-07-10",
    "created_at": "2026-07-10T14:44:49.068836Z",
}

writeoff_history_get_schema = description_schema(
    summary="List write-off history",
    description=(
        "Retrieves a paginated, read-only list of drone write-off audit records, "
        "ordered from newest to oldest. Supports filtering, search "
        "(by drone name, serial/inventory number, reason, and document number), "
        "and ordering.\n\n"
        "When the request is made against the drone-scoped route "
        "(`/api/drones/{drone_pk}/write-offs/history/`), the results are limited "
        "to write-off records for that single drone."
    ),
    permission_code="PERMISSION_WRITEOFF_VIEW",
    request=None,
    responses={
        status.HTTP_200_OK: OpenApiResponse(
            response=WriteOffAuditSerializer(many=True),
            description="Successfully retrieved the write-off history.",
        ),
    },
    error_statuses=[status.HTTP_403_FORBIDDEN],
    examples=[
        OpenApiExample(
            name="Valid request",
            response_only=True,
            value=writeoff_audit_example_value,
        ),
    ],
)

writeoff_record_get_schema = description_schema(
    summary="List write-off records",
    description=(
        "Retrieves a paginated, read-only list of drone write-off records, "
        "ordered by write-off date from newest to oldest."
    ),
    permission_code="PERMISSION_WRITEOFF_VIEW",
    request=None,
    responses={
        status.HTTP_200_OK: OpenApiResponse(
            response=WriteOffRecordSerializer(many=True),
            description="Successfully retrieved the list of write-off records.",
        ),
    },
    error_statuses=[status.HTTP_403_FORBIDDEN],
    examples=[
        OpenApiExample(
            name="Valid request",
            response_only=True,
            value={
                "id": 3,
                "reason": "LOSS",
                "reason_label": "Loss",
                "reason_description": "Lost during combat sortie behind enemy lines.",
                "authorized_by": 24,
                "related_mission_id": 5,
                "document_number": "WO-2026-0009",
                "written_off_at": "2026-07-10",
                "created_at": "2026-07-10T14:44:49.068836Z",
            },
        ),
    ],
)

writeoff_record_post_schema = description_schema(
    summary="Create a write-off record",
    description=(
        "Creates a new immutable write-off record for a drone and records the "
        "resulting status transition in the drone status history.\n\n"
        "Validation: \n"
        "- A drone can be written off only once; a second write-off is rejected. \n"
        "- A drone that already has an inactive status cannot be written off. \n"
        "- When a related mission is supplied, it must be the drone's latest "
        "assigned mission, and the drone must be assigned to that mission."
    ),
    permission_code="PERMISSION_WRITEOFF_CREATE",
    request=WriteOffRecordCreateSerializer,
    responses={
        status.HTTP_201_CREATED: OpenApiResponse(
            response=WriteOffRecordCreateSerializer,
            description="Write-off record created successfully.",
        ),
        status.HTTP_400_BAD_REQUEST: OpenApiResponse(
            description="Bad Request",
            response=dict,
            examples=[
                OpenApiExample(
                    name="Drone already written off",
                    value={
                        "drone": "A write-off record for this drone already exists."
                    },
                ),
                OpenApiExample(
                    name="Drone already inactive",
                    value={
                        "drone": (
                            "Cannot write off a drone with inactive status "
                            "'WRITTEN_OFF'."
                        )
                    },
                ),
                OpenApiExample(
                    name="Mission is not the latest",
                    value={
                        "related_mission": (
                            "Mission 4 is not the latest. A drone can only be "
                            "written off based on its latest mission."
                        )
                    },
                ),
            ],
        ),
    },
    error_statuses=[status.HTTP_403_FORBIDDEN],
    examples=[
        OpenApiExample(
            name="Valid Request",
            request_only=True,
            value={
                "drone": 29,
                "reason": "LOSS",
                "reason_description": "Lost during combat sortie behind enemy lines.",
                "related_mission": 5,
                "document_number": "WO-2026-0009",
                "written_off_at": "2026-07-10",
            },
        ),
        OpenApiExample(
            name="Valid Request",
            response_only=True,
            value={
                "id": 3,
                "drone": 29,
                "reason": "LOSS",
                "reason_description": "Lost during combat sortie behind enemy lines.",
                "related_mission": 5,
                "document_number": "WO-2026-0009",
                "written_off_at": "2026-07-10",
                "created_at": "2026-07-10T14:44:49.068836Z",
            },
        ),
    ],
)
