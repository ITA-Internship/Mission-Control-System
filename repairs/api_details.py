from drf_spectacular.utils import OpenApiExample, OpenApiParameter, OpenApiResponse
from rest_framework import status

from common.api_description_schema import description_schema
from config.settings import MAX_EXPORT_LIMIT
from repairs.serializers import (
    DESCRIPTION_MIN_LENGTH,
    ComponentReplacementListSerializer,
    ComponentReplacementSerializer,
    DefectReportListSerializer,
    DefectReportSerializer,
    DefectStatusUpdateSerializer,
    RepairEventSerializer,
    RepairHistoryTimelineSerializer,
    RepairOrderCreateSerializer,
    RepairOrderListSerializer,
    RepairOrderReplacementSerializer,
    RepairOrderSerializer,
    RepairOrderStatusUpdateSerializer,
)

defect_get_schema = description_schema(
    summary="List defect reports",
    description=(
        "Retrieves a paginated and filtered list of all recorded drone defect reports. "
    ),
    permission_code="PERMISSION_REPAIRS_VIEW",
    request=None,
    responses={
        status.HTTP_200_OK: OpenApiResponse(
            response=DefectReportListSerializer(many=True),
            description="Successfully retrieved the list of defect reports.",
        ),
    },
    error_statuses=[status.HTTP_403_FORBIDDEN],
    examples=[
        OpenApiExample(
            name="Valid Request.",
            value={
                "id": 4,
                "drone": 21,
                "defect_type": "CAMERA",
                "severity": "MEDIUM",
                "detected_at": "2026-05-19T16:05:00Z",
                "reporter": 28,
                "created_at": "2026-07-02T02:21:31.254932Z",
            },
        )
    ],
)

defect_post_schema = description_schema(
    summary="Create a new defect report",
    description=(
        "Creates a new defect report. \n\n"
        "Validation: \n"
        f"- Description must be at least {DESCRIPTION_MIN_LENGTH} character long. \n"
    ),
    permission_code="PERMISSION_REPAIRS_CREATE",
    request=DefectReportSerializer,
    responses={
        status.HTTP_201_CREATED: OpenApiResponse(
            response=DefectReportSerializer,
            description="Defect report successfully created.",
        ),
    },
    error_statuses=[status.HTTP_400_BAD_REQUEST, status.HTTP_403_FORBIDDEN],
    examples=[
        OpenApiExample(
            name="Valid Request",
            request_only=True,
            value={
                "drone": 21,
                "defect_type": "CAMERA",
                "severity": "MEDIUM",
                "description": (
                    "Camera feed intermittently flickers during high-speed turns."
                ),
                "detected_at": "2026-07-02",
            },
        ),
        OpenApiExample(
            name="Valid Request",
            response_only=True,
            value={
                "id": 5,
                "drone": 21,
                "defect_type": "CAMERA",
                "severity": "MEDIUM",
                "description": (
                    "Camera feed intermittently flickers during high-speed turns."
                ),
                "detected_at": "2026-07-02T00:00:00Z",
                "reporter": 24,
                "created_at": "2026-07-03T05:03:12.266745Z",
                "updated_at": "2026-07-03T05:03:12.266754Z",
            },
        ),
    ],
)

defect_detail_schema = description_schema(
    summary="Retrieve specific defect report details",
    description=(
        "Retrieves detailed information about specific defect report by its ID."
    ),
    permission_code="PERMISSION_REPAIRS_VIEW",
    parameters=[
        OpenApiParameter(
            name="id",
            type=int,
            location=OpenApiParameter.PATH,
            description="ID of specific defect report.",
        )
    ],
    request=None,
    responses={
        status.HTTP_200_OK: OpenApiResponse(
            response=DefectReportSerializer,
            description="Detailed information about the drone defect report.",
        ),
    },
    error_statuses=[status.HTTP_403_FORBIDDEN, status.HTTP_404_NOT_FOUND],
    examples=[
        OpenApiExample(
            name="Valid Request",
            value={
                "id": 4,
                "drone": 21,
                "defect_type": "CAMERA",
                "severity": "MEDIUM",
                "description": (
                    "Camera feed intermittently flickers during high-speed turns."
                ),
                "detected_at": "2026-05-19T16:05:00Z",
                "reporter": 28,
                "created_at": "2026-07-02T02:21:31.254932Z",
                "updated_at": "2026-07-03T01:17:37.754142Z",
            },
        )
    ],
)

component_replacement_get_schema = description_schema(
    summary="List component replacements",
    description=(
        "Retrieves a paginated and filtered list of all"
        " recorded component replacements performed on drones.\n\n"
    ),
    permission_code="PERMISSION_REPAIRS_VIEW",
    request=None,
    responses={
        status.HTTP_200_OK: OpenApiResponse(
            response=ComponentReplacementListSerializer(many=True),
            description="Successfully retrieved the list of component replacements.",
        ),
    },
    error_statuses=[status.HTTP_403_FORBIDDEN],
    examples=[
        OpenApiExample(
            name="Valid Request",
            value={
                "id": 1,
                "drone": 24,
                "component_type": "MOTOR",
                "component_name": None,
                "new_serial_number": "TM-F60PV-24004-B",
                "replaced_at": "2026-05-09T09:30:00Z",
                "replaced_by": 31,
                "created_at": "2026-07-02T02:21:31.258041Z",
            },
        )
    ],
)

component_replacement_post_schema = description_schema(
    summary="Record a component replacement",
    description=(
        "Creates a new component replacement report. \n\n"
        "Validation: \n"
        "- If component type is `OTHER`, component name must be provided."
    ),
    permission_code="PERMISSION_REPAIRS_CREATE",
    request=ComponentReplacementSerializer,
    responses={
        status.HTTP_201_CREATED: OpenApiResponse(
            response=ComponentReplacementSerializer,
            description="Component replacement report successfully created.",
        ),
        status.HTTP_400_BAD_REQUEST: OpenApiResponse(
            description="Bad Request. Provided payload contains validation errors.",
            examples=[
                OpenApiExample(
                    name="Name must be provided.",
                    value={"component_name": "Component name is required for OTHER."},
                )
            ],
        ),
    },
    error_statuses=[status.HTTP_403_FORBIDDEN],
    examples=[
        OpenApiExample(
            name="Valid Request",
            request_only=True,
            value={
                "drone": 25,
                "component_type": "FRAME",
                "component_name": None,
                "old_serial_number": "FRAME-SPEAR1-OLD",
                "new_serial_number": "FRAME-SPEAR1-NEW",
                "reason": (
                    "Frame section replaced after "
                    "structural damage from forced landing."
                ),
                "replaced_at": "2026-07-03",
            },
        ),
        OpenApiExample(
            name="Valid Request",
            response_only=True,
            value={
                "id": 5,
                "drone": 25,
                "component_type": "FRAME",
                "component_name": None,
                "old_serial_number": "FRAME-SPEAR1-OLD",
                "new_serial_number": "FRAME-SPEAR1-NEW",
                "reason": (
                    "Frame section replaced after "
                    "structural damage from forced landing."
                ),
                "replaced_at": "2026-07-03T00:00:00Z",
                "replaced_by": 24,
                "created_at": "2026-07-03T05:09:09.903830Z",
                "updated_at": "2026-07-03T05:09:09.903879Z",
            },
        ),
    ],
)

component_replacement_detail_schema = description_schema(
    summary="Retrieve specific component replacement details",
    description=(
        "Retrieves detailed information about "
        "specific component replacement report by its ID."
    ),
    permission_code="PERMISSION_REPAIRS_VIEW",
    parameters=[
        OpenApiParameter(
            name="id",
            type=int,
            location=OpenApiParameter.PATH,
            description="ID of specific component replacement report.",
        )
    ],
    request=None,
    responses={
        status.HTTP_200_OK: OpenApiResponse(
            response=ComponentReplacementSerializer,
            description="Detailed information about the component replacement record.",
        ),
    },
    error_statuses=[status.HTTP_403_FORBIDDEN, status.HTTP_404_NOT_FOUND],
    examples=[
        OpenApiExample(
            name="Valid Request",
            value={
                "id": 1,
                "drone": 24,
                "component_type": "MOTOR",
                "component_name": None,
                "old_serial_number": "TM-F60PV-24004-A",
                "new_serial_number": "TM-F60PV-24004-B",
                "reason": (
                    "Motor replaced after abnormal vibration "
                    "was confirmed in inspection."
                ),
                "replaced_at": "2026-05-09T09:30:00Z",
                "replaced_by": 31,
                "created_at": "2026-07-02T02:21:31.258041Z",
                "updated_at": "2026-07-03T01:17:37.756512Z",
            },
        )
    ],
)

component_replacement_export_schema = description_schema(
    summary="Export component replacement data to CSV",
    description=(
        "Generates and downloads a CSV file with"
        " the filtered component replacement history."
        "Supports full filtering identical to the standard list endpoint. \n\n"
        f"The export is limited to a maximum of {MAX_EXPORT_LIMIT} records. "
    ),
    permission_code="PERMISSION_REPAIRS_VIEW",
    request=None,
    responses={
        200: OpenApiResponse(description="A CSV file generated successfully."),
    },
    error_statuses=[status.HTTP_403_FORBIDDEN],
)

repair_event_example_value = {
    "id": 7,
    "from_status": "REPORTED",
    "to_status": "IN_PROGRESS",
    "action_taken": "Started diagnostics on the camera gimbal wiring.",
    "technician": 24,
    "created_at": "2026-07-03T05:20:11.884120Z",
}

defect_history_get_schema = description_schema(
    summary="List defect status history",
    description=(
        "Retrieves a paginated, read-only audit trail of status transition events "
        "for a specific defect report, showing how the defect moved through the "
        "repair workflow over time."
    ),
    permission_code="PERMISSION_REPAIRS_VIEW",
    parameters=[
        OpenApiParameter(
            name="id",
            type=int,
            location=OpenApiParameter.PATH,
            description="ID of the defect report whose history is being retrieved.",
            required=True,
        ),
    ],
    request=None,
    responses={
        status.HTTP_200_OK: OpenApiResponse(
            response=RepairEventSerializer(many=True),
            description="Successfully retrieved the defect status history.",
        ),
    },
    error_statuses=[status.HTTP_403_FORBIDDEN],
    examples=[
        OpenApiExample(
            name="Valid request",
            response_only=True,
            value=repair_event_example_value,
        ),
    ],
)

defect_status_update_post_schema = description_schema(
    summary="Update defect report status",
    description=(
        "Transitions a defect report to a new status and records a repair event "
        "documenting the change. On success, the reporter is notified by email for "
        "`IN_PROGRESS` and `FIXED` transitions.\n\n"
        "Validation: \n"
        "- An `action_taken` comment is required to explain the change. \n"
        "- The new status must differ from the current status. \n"
        "- A defect can be moved to `VERIFIED` only if its current status is "
        "`FIXED`. \n\n"
        "Additional permissions: \n"
        "- Transitions to `IN_PROGRESS` or `FIXED` require "
        "`PERMISSION_REPAIRS_MANAGE` or `PERMISSION_REPAIRS_VERIFY`. \n"
        "- Transitions to `VERIFIED` require `PERMISSION_REPAIRS_VERIFY`."
    ),
    permission_code="PERMISSION_REPAIRS_CREATE",
    parameters=[
        OpenApiParameter(
            name="id",
            type=int,
            location=OpenApiParameter.PATH,
            description="ID of the defect report whose status is being updated.",
            required=True,
        ),
    ],
    request=DefectStatusUpdateSerializer,
    responses={
        status.HTTP_200_OK: OpenApiResponse(
            response=RepairEventSerializer,
            description="Status updated successfully; the repair event is returned.",
        ),
        status.HTTP_400_BAD_REQUEST: OpenApiResponse(
            description="Bad Request",
            response=dict,
            examples=[
                OpenApiExample(
                    name="Missing action comment",
                    value={"action_taken": "This field may not be blank."},
                ),
                OpenApiExample(
                    name="Defect already in status",
                    value={"status": "The defect is already in this status."},
                ),
                OpenApiExample(
                    name="Invalid verify transition",
                    value={
                        "status": (
                            "A defect can only be verified if its current "
                            "status is FIXED."
                        )
                    },
                ),
                OpenApiExample(
                    name="Defect not found",
                    value={"detail": "Defect report not found."},
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
                "status": "IN_PROGRESS",
                "action_taken": "Started diagnostics on the camera gimbal wiring.",
            },
        ),
        OpenApiExample(
            name="Valid Request",
            response_only=True,
            value=repair_event_example_value,
        ),
    ],
)

repair_order_get_schema = description_schema(
    summary="List repair orders",
    description=(
        "Retrieves a paginated and filtered list of all repair orders, ordered by "
        "creation date."
    ),
    permission_code="PERMISSION_REPAIRS_VIEW",
    request=None,
    responses={
        status.HTTP_200_OK: OpenApiResponse(
            response=RepairOrderListSerializer(many=True),
            description="Successfully retrieved the list of repair orders.",
        ),
    },
    error_statuses=[status.HTTP_403_FORBIDDEN],
    examples=[
        OpenApiExample(
            name="Valid request",
            response_only=True,
            value={
                "id": 2,
                "drone": 21,
                "defect_report": 4,
                "status": "PENDING",
                "assigned_to": 31,
                "created_by": 24,
                "created_at": "2026-07-03T05:15:02.114120Z",
            },
        ),
    ],
)

repair_order_post_schema = description_schema(
    summary="Create a repair order",
    description=(
        "Creates a new repair order for a drone. The order can be standalone "
        "(routine maintenance) or linked to an existing defect report.\n\n"
        "Validation: \n"
        f"- Description must be at least {DESCRIPTION_MIN_LENGTH} characters long."
    ),
    permission_code="PERMISSION_REPAIRS_MANAGE",
    request=RepairOrderCreateSerializer,
    responses={
        status.HTTP_201_CREATED: OpenApiResponse(
            response=RepairOrderCreateSerializer,
            description="Repair order created successfully.",
        ),
        status.HTTP_400_BAD_REQUEST: OpenApiResponse(
            description="Bad Request",
            response=dict,
            examples=[
                OpenApiExample(
                    name="Description too short",
                    value={
                        "description": (
                            f"Description must be at least "
                            f"{DESCRIPTION_MIN_LENGTH} characters long."
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
                "drone": 21,
                "defect_report": 4,
                "description": "Replace damaged camera gimbal and recalibrate.",
                "assigned_to": 31,
            },
        ),
        OpenApiExample(
            name="Valid Request",
            response_only=True,
            value={
                "id": 2,
                "drone": 21,
                "defect_report": 4,
                "description": "Replace damaged camera gimbal and recalibrate.",
                "assigned_to": 31,
            },
        ),
    ],
)

repair_order_example_value = {
    "id": 2,
    "drone": 21,
    "defect_report": 4,
    "status": "IN_PROGRESS",
    "description": "Replace damaged camera gimbal and recalibrate.",
    "assigned_to": 31,
    "started_at": "2026-07-03T05:30:00Z",
    "completed_at": None,
    "notes": "Awaiting replacement gimbal from stores.",
    "created_by": 24,
    "created_at": "2026-07-03T05:15:02.114120Z",
    "updated_at": "2026-07-03T05:30:00.552310Z",
}

repair_order_detail_get_schema = description_schema(
    summary="Retrieve repair order details",
    description=(
        "Retrieves detailed information about a specific repair order by its ID."
    ),
    permission_code="PERMISSION_REPAIRS_VIEW",
    parameters=[
        OpenApiParameter(
            name="id",
            type=int,
            location=OpenApiParameter.PATH,
            description="ID of the repair order to retrieve.",
            required=True,
        ),
    ],
    request=None,
    responses={
        status.HTTP_200_OK: OpenApiResponse(
            response=RepairOrderSerializer,
            description="Detailed information about the repair order.",
        ),
    },
    error_statuses=[status.HTTP_403_FORBIDDEN, status.HTTP_404_NOT_FOUND],
    examples=[
        OpenApiExample(
            name="Valid request",
            response_only=True,
            value=repair_order_example_value,
        ),
    ],
)

repair_order_detail_patch_schema = description_schema(
    summary="Update repair order status",
    description=(
        "Transitions a repair order to a new status through its lifecycle state "
        "machine. Operational timestamps (`started_at`, `completed_at`) are stamped "
        "automatically as the order progresses.\n\n"
        "Validation: \n"
        "- The requested transition must be allowed from the order's current "
        "status (e.g., `PENDING` cannot jump straight to `COMPLETED`)."
    ),
    permission_code="PERMISSION_REPAIRS_MANAGE",
    parameters=[
        OpenApiParameter(
            name="id",
            type=int,
            location=OpenApiParameter.PATH,
            description="ID of the repair order whose status is being updated.",
            required=True,
        ),
    ],
    request=RepairOrderStatusUpdateSerializer,
    responses={
        status.HTTP_200_OK: OpenApiResponse(
            response=RepairOrderSerializer,
            description="Repair order status updated successfully.",
        ),
        status.HTTP_400_BAD_REQUEST: OpenApiResponse(
            description="Bad Request",
            response=dict,
            examples=[
                OpenApiExample(
                    name="Disallowed transition",
                    value={
                        "status": [
                            "Cannot transition from PENDING to COMPLETED. "
                            "Allowed: ['IN_PROGRESS', 'CANCELLED']"
                        ]
                    },
                ),
            ],
        ),
    },
    error_statuses=[status.HTTP_403_FORBIDDEN, status.HTTP_404_NOT_FOUND],
    examples=[
        OpenApiExample(
            name="Valid Request",
            request_only=True,
            value={"status": "IN_PROGRESS", "notes": "Technician started the repair."},
        ),
        OpenApiExample(
            name="Valid Request",
            response_only=True,
            value=repair_order_example_value,
        ),
    ],
)

repair_order_replacement_post_schema = description_schema(
    summary="Add a component replacement to a repair order",
    description=(
        "Records a new component replacement and links it to an existing repair "
        "order.\n\n"
        "Validation: \n"
        "- A new serial number is required. \n"
        "- A reason is required. \n"
        "- `replaced_at` cannot be in the future. \n"
        "- If the component type is `OTHER`, a component name must be provided; "
        "for known component types any supplied name is cleared."
    ),
    permission_code="PERMISSION_REPAIRS_MANAGE",
    parameters=[
        OpenApiParameter(
            name="id",
            type=int,
            location=OpenApiParameter.PATH,
            description="ID of the repair order the replacement is attached to.",
            required=True,
        ),
    ],
    request=RepairOrderReplacementSerializer,
    responses={
        status.HTTP_201_CREATED: OpenApiResponse(
            response=RepairOrderReplacementSerializer,
            description="Component replacement recorded and linked successfully.",
        ),
        status.HTTP_400_BAD_REQUEST: OpenApiResponse(
            description="Bad Request",
            response=dict,
            examples=[
                OpenApiExample(
                    name="Name required for OTHER",
                    value={"component_name": ["Component name is required for OTHER."]},
                ),
                OpenApiExample(
                    name="Missing new serial number",
                    value={"new_serial_number": ["New serial number is required."]},
                ),
            ],
        ),
    },
    error_statuses=[status.HTTP_403_FORBIDDEN, status.HTTP_404_NOT_FOUND],
    examples=[
        OpenApiExample(
            name="Valid Request",
            request_only=True,
            value={
                "component_type": "CAMERA",
                "component_name": None,
                "old_serial_number": "CAM-GIMBAL-OLD",
                "new_serial_number": "CAM-GIMBAL-NEW",
                "reason": "Gimbal replaced after confirmed camera feed instability.",
                "replaced_at": "2026-07-03",
            },
        ),
        OpenApiExample(
            name="Valid Request",
            response_only=True,
            value={
                "id": 6,
                "component_type": "CAMERA",
                "component_name": None,
                "old_serial_number": "CAM-GIMBAL-OLD",
                "new_serial_number": "CAM-GIMBAL-NEW",
                "reason": "Gimbal replaced after confirmed camera feed instability.",
                "replaced_at": "2026-07-03T00:00:00Z",
                "replaced_by": 24,
                "created_at": "2026-07-03T05:40:12.114120Z",
                "updated_at": "2026-07-03T05:40:12.114160Z",
            },
        ),
    ],
)

repair_history_query_parameters = [
    OpenApiParameter(
        name="drone_id",
        type=int,
        location=OpenApiParameter.PATH,
        description="ID of the drone whose repair history is being retrieved.",
        required=True,
    ),
    OpenApiParameter(
        name="date_from",
        type=str,
        location=OpenApiParameter.QUERY,
        description="Optional ISO 8601 lower bound for the event timestamp.",
        required=False,
    ),
    OpenApiParameter(
        name="date_to",
        type=str,
        location=OpenApiParameter.QUERY,
        description="Optional ISO 8601 upper bound for the event timestamp.",
        required=False,
    ),
    OpenApiParameter(
        name="event_type",
        type=str,
        location=OpenApiParameter.QUERY,
        description=(
            "Optional comma-separated list of event types to include "
            "(`defect`, `status_change`, `repair`, `replacement`)."
        ),
        required=False,
    ),
]

drone_repair_history_get_schema = description_schema(
    summary="Retrieve drone repair history timeline",
    description=(
        "Retrieves a paginated, chronological timeline that aggregates every "
        "repair-related event for a drone (defect reports, status changes, repair "
        "orders, and component replacements). Results can be filtered by date range "
        "and event type.\n\n"
        "Validation: \n"
        "- `date_from` must be before or equal to `date_to`."
    ),
    permission_code="PERMISSION_REPAIRS_VIEW",
    parameters=repair_history_query_parameters,
    request=None,
    responses={
        status.HTTP_200_OK: OpenApiResponse(
            response=RepairHistoryTimelineSerializer(many=True),
            description="Successfully retrieved the drone repair history timeline.",
        ),
        status.HTTP_400_BAD_REQUEST: OpenApiResponse(
            description="Bad Request",
            response=dict,
            examples=[
                OpenApiExample(
                    name="Invalid date range",
                    value={
                        "non_field_errors": [
                            "date_from must be before or equal to date_to."
                        ]
                    },
                ),
            ],
        ),
    },
    error_statuses=[status.HTTP_403_FORBIDDEN, status.HTTP_404_NOT_FOUND],
    examples=[
        OpenApiExample(
            name="Valid request",
            response_only=True,
            value={
                "event_type": "replacement",
                "timestamp": "2026-07-03T05:40:12.114120Z",
                "summary": "Camera replaced on Falcon Eye 1.",
                "details": {
                    "component_type": "CAMERA",
                    "new_serial_number": "CAM-GIMBAL-NEW",
                    "replaced_by": "oleksandr.koval",
                },
            },
        ),
    ],
)

drone_repair_history_export_schema = description_schema(
    summary="Export drone repair history to CSV",
    description=(
        "Generates and downloads a CSV file with the drone's complete repair "
        "history timeline. Supports the same date range and event type filtering "
        "as the timeline endpoint.\n\n"
        "Validation: \n"
        "- `date_from` must be before or equal to `date_to`."
    ),
    permission_code="PERMISSION_REPAIRS_EXPORT",
    parameters=repair_history_query_parameters,
    request=None,
    responses={
        status.HTTP_200_OK: OpenApiResponse(
            description=(
                "A CSV file containing the drone repair history "
                "generated successfully."
            ),
        ),
        status.HTTP_400_BAD_REQUEST: OpenApiResponse(
            description="Bad Request",
            response=dict,
            examples=[
                OpenApiExample(
                    name="Invalid date range",
                    value={
                        "non_field_errors": [
                            "date_from must be before or equal to date_to."
                        ]
                    },
                ),
            ],
        ),
    },
    error_statuses=[status.HTTP_403_FORBIDDEN, status.HTTP_404_NOT_FOUND],
)
