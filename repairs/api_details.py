from drf_spectacular.utils import OpenApiExample, OpenApiParameter, OpenApiResponse
from rest_framework import status

from common.api_description_schema import description_schema
from repairs.serializers import (
    ComponentReplacementListSerializer,
    ComponentReplacementSerializer,
    DefectReportListSerializer,
    DefectReportSerializer,
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
        "- Description must be at least 10 character long. \n"
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
        "The export is limited to a maximum of 10,000 records. "
    ),
    permission_code="PERMISSION_REPAIRS_VIEW",
    request=None,
    responses={
        200: OpenApiResponse(description="A CSV file generated successfully."),
    },
    error_statuses=[status.HTTP_403_FORBIDDEN],
)
