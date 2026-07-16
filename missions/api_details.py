from drf_spectacular.utils import OpenApiExample, OpenApiParameter, OpenApiResponse
from rest_framework import status

from common.api_description_schema import description_schema
from missions.models import Status
from missions.serializers import (
    TITLE_MIN_LENGTH,
    MissionDroneConditionSerializer,
    MissionDroneSerializer,
    MissionOutcomeSerializer,
    MissionSerializer,
    MissionStatusUpdateSerializer,
)

mission_example_value = {
    "id": 31,
    "title": "Fallback Route Mapping",
    "commander": {
        "id": 27,
        "username": "commander.south",
        "email": "commander.south@example.com",
    },
    "status": "planned",
    "result": None,
    "location_description": (
        "Secondary fallback route south-west of artillery support line."
    ),
    "latitude": "48.619700",
    "longitude": "22.287900",
    "started_at": "2026-07-09T01:17:37.650595Z",
    "ended_at": "2026-07-09T01:49:37.650595Z",
    "notes": "Objective: capture updated terrain references and route obstacles.",
    "incident_notes": "",
    "created_by": {
        "id": 24,
        "username": "oleksander.koval",
        "email": "oleksander.koval@example.com",
    },
    "created_at": "2026-07-02T02:21:31.151234Z",
    "updated_at": "2026-07-03T01:17:37.651465Z",
    "drones": [],
}

assignment_example_value = {
    "id": 1,
    "mission": 34,
    "drone": 21,
    "drone_details": {
        "id": 21,
        "name": "Falcon Eye 1",
        "serial_number": "FPV-AER-24001",
        "drone_model": 15,
        "status": "ACTIVE",
    },
    "operator": 28,
    "operator_details": {
        "id": 28,
        "username": "operator.alpha",
        "email": "operator.alpha@example.com",
    },
    "condition_after": None,
    "condition_description": None,
    "flight_started_at": None,
    "flight_ended_at": None,
    "created_at": "2026-07-06T02:19:18.140785Z",
}

mission_get_schema = description_schema(
    summary="List missions",
    description=(
        "Retrieves a paginated and filtered by status list of missions, "
        "assigned to the currently authenticated user. "
    ),
    permission_code="IsDispatcherOrAdmin, PERMISSION_MISSIONS_VIEW",
    parameters=[
        OpenApiParameter(
            name="status",
            type=str,
            location=OpenApiParameter.QUERY,
            required=False,
            enum=[choice.value for choice in Status],
            description="Filter missions by their current state.",
        ),
        OpenApiParameter(
            name="assigned_to",
            type=str,
            location=OpenApiParameter.QUERY,
            required=False,
            enum=["me"],
            description=(
                "Filter to only show missions where "
                "the currently authenticated user is assigned to."
            ),
        ),
    ],
    request=None,
    responses={
        status.HTTP_200_OK: OpenApiResponse(
            response=MissionSerializer(many=True),
            description="Successfully retrieved the filtered list of missions.",
        ),
    },
    error_statuses=[status.HTTP_403_FORBIDDEN],
    examples=[
        OpenApiExample(
            name="Valid Request",
            value=mission_example_value,
        )
    ],
)

mission_post_schema = description_schema(
    summary="Create a new mission",
    description=(
        "Creates a new mission. "
        "The logged-in user is automatically assigned "
        "as the creator (`created_by`).\n\n"
        "Validation: \n"
        f"- Title of the mission must be at least {TITLE_MIN_LENGTH} character long. \n"
        "- User assigned as a commander must have a Commander role. \n"
        "- Either location or latitude and longitude must be provided. \n"
        "- Assigned drones and operators "
        "cannot already be assigned to another mission. "
    ),
    permission_code="IsDispatcherOrAdmin, PERMISSION_MISSIONS_CREATE",
    request=MissionSerializer,
    responses={
        status.HTTP_200_OK: OpenApiResponse(
            response=MissionSerializer, description="Mission successfully created."
        ),
    },
    error_statuses=[status.HTTP_400_BAD_REQUEST, status.HTTP_403_FORBIDDEN],
    examples=[
        OpenApiExample(
            name="Valid Request",
            request_only=True,
            value={
                "title": "Fallback Route Mapping",
                "status": "planned",
                "location_description": (
                    "Secondary fallback route south-west of artillery support line."
                ),
                "latitude": "48.619700",
                "longitude": "22.287900",
                "started_at": "2026-07-09T01:17:37.650595Z",
                "ended_at": "2026-07-09T01:49:37.650595Z",
                "notes": "Objective: capture updated terrain references.",
            },
        ),
        OpenApiExample(
            name="Valid Request",
            response_only=True,
            value={
                "id": 33,
                "title": "Fallback Route Mapping",
                "commander": None,
                "status": "planned",
                "result": None,
                "location_description": (
                    "Secondary fallback route south-west of artillery support line."
                ),
                "latitude": "48.619700",
                "longitude": "22.287900",
                "started_at": "2026-07-09T01:17:37.650595Z",
                "ended_at": "2026-07-09T01:49:37.650595Z",
                "notes": "Objective: capture updated terrain references.",
                "incident_notes": "",
                "created_by": {
                    "id": 24,
                    "username": "oleksander.koval",
                    "email": "oleksander.koval@example.com",
                },
                "created_at": "2026-07-03T01:24:28.367298Z",
                "updated_at": "2026-07-03T01:24:28.367301Z",
                "drones": [],
            },
        ),
    ],
)

mission_detail_schema = description_schema(
    summary="Retrieve mission details",
    description="Retrieves detailed information about a single mission by its ID.",
    permission_code="PERMISSION_MISSIONS_VIEW",
    parameters=[
        OpenApiParameter(
            name="id",
            type=int,
            location=OpenApiParameter.PATH,
            description="ID of the mission.",
        )
    ],
    request=None,
    responses={
        status.HTTP_200_OK: OpenApiResponse(
            response=MissionSerializer, description="Detailed mission profile."
        ),
    },
    error_statuses=[status.HTTP_403_FORBIDDEN, status.HTTP_404_NOT_FOUND],
    examples=[
        OpenApiExample(
            name="Valid Request",
            value=mission_example_value,
        )
    ],
)

mission_outcome_schema = description_schema(
    summary="Record mission outcome",
    description=(
        "Partially updates the mission record to record status, "
        "result and incident notes for the mission. "
        "Creates an audit log entry. \n\n"
        "Validation: \n"
        "- Status can only be recorded for completed or aborted mission. \n"
        "- Already recorded outcome cannot be overwritten. \n"
        "- If result of a mission is a failure, incident notes must be provided."
    ),
    permission_code="IsAssignedOperatorOrAdmin, PERMISSION_MISSIONS_RECORD_OUTCOME",
    parameters=[
        OpenApiParameter(
            name="id",
            type=int,
            location=OpenApiParameter.PATH,
            description="ID of the mission.",
        )
    ],
    request=MissionOutcomeSerializer,
    responses={
        status.HTTP_200_OK: OpenApiResponse(
            response=MissionOutcomeSerializer,
            description="Mission outcome recorded successfully.",
        ),
        status.HTTP_400_BAD_REQUEST: OpenApiResponse(
            description="Bad Request.",
            response=dict,
            examples=[
                OpenApiExample(
                    name="Invalid mission status",
                    value={
                        "status": (
                            "Outcome can only be recorded for missions "
                            "with status 'completed' or 'aborted'."
                        )
                    },
                ),
                OpenApiExample(
                    name="Outcome already recorded",
                    value={
                        "result": (
                            "Outcome has already been recorded for this mission "
                            "and cannot be overwritten."
                        )
                    },
                ),
                OpenApiExample(
                    name="Incident notes not provided for failed mission",
                    value={
                        "incident_notes": (
                            "Incident notes are required when result is 'failure'."
                        )
                    },
                ),
            ],
        ),
    },
    error_statuses=[
        status.HTTP_403_FORBIDDEN,
        status.HTTP_404_NOT_FOUND,
    ],
    examples=[
        OpenApiExample(
            name="Valid Request", value={"result": "success"}, request_only=True
        ),
        OpenApiExample(
            name="Valid Request",
            value={
                "id": 35,
                "status": "completed",
                "result": "success",
                "notes": "The mission was completed successfully.",
                "incident_notes": "",
            },
            response_only=True,
        ),
    ],
)

mission_drone_condition_schema = description_schema(
    tags=["mission assignments"],
    summary="Update drone post-mission condition",
    permission_code="PERMISSION_MISSIONS_RECORD_CONDITION, IsAssignedOperatorOrAdmin",
    description=(
        "Updates the condition of a specific drone assigned to "
        "a mission and creates an audit log entry. \n\n"
        "Validation: \n"
        "- Drone condition can only be recorded for missions "
        "with status `completed` or `aborted`. \n"
        "- Condition `lost` cannot be overwritten."
    ),
    parameters=[
        OpenApiParameter(
            name="pk",
            type=int,
            location=OpenApiParameter.PATH,
            description="ID of the parent mission.",
        ),
        OpenApiParameter(
            name="assignment_id",
            type=int,
            location=OpenApiParameter.PATH,
            description="ID of the specific drone-to-mission assignment.",
        ),
    ],
    request=MissionDroneConditionSerializer,
    responses={
        status.HTTP_200_OK: OpenApiResponse(
            response=MissionDroneConditionSerializer,
            description="Drone condition successfully updated.",
        ),
        status.HTTP_400_BAD_REQUEST: OpenApiResponse(
            description="Bad Request",
            response=dict,
            examples=[
                OpenApiExample(
                    name="Invalid mission status",
                    value={
                        "mission": (
                            "Drone condition can only be recorded for missions "
                            "with status 'completed' or 'aborted'."
                        )
                    },
                ),
                OpenApiExample(
                    name="Overwriting lost condition",
                    value={
                        "condition_after": (
                            "Cannot reverse a 'lost' condition: a writeoff record "
                            "has been created and requires a manual reversal process."
                        )
                    },
                ),
                OpenApiExample(
                    name="Written-off drone",
                    value={
                        "condition_after": (
                            "Drone is already written off; "
                            "cannot record 'lost' condition again."
                        )
                    },
                ),
            ],
        ),
    },
    error_statuses=[status.HTTP_403_FORBIDDEN, status.HTTP_404_NOT_FOUND],
    examples=[
        OpenApiExample(
            name="Valid Request", value={"condition_after": "ok"}, request_only=True
        ),
        OpenApiExample(
            name="Valid Request",
            value={"id": 1, "condition_after": "ok", "condition_description": None},
            response_only=True,
        ),
    ],
)

mission_status_get_schema = description_schema(
    summary="Retrieve mission status",
    description=("Retrieves the current status of a mission."),
    permission_code="CanUpdateMissionStatus",
    parameters=[
        OpenApiParameter(
            name="id",
            type=int,
            location=OpenApiParameter.PATH,
            description="ID of the mission.",
        )
    ],
    request=None,
    responses={
        status.HTTP_200_OK: OpenApiResponse(
            response=MissionStatusUpdateSerializer,
            description="Current mission status successfully retrieved.",
        ),
    },
    error_statuses=[status.HTTP_403_FORBIDDEN, status.HTTP_404_NOT_FOUND],
    examples=[
        OpenApiExample(
            name="Valid Request", value={"status": "planned"}, response_only=True
        )
    ],
)

mission_status_update_schema = description_schema(
    summary="Update mission status",
    description=(
        "Updates the mission status and creates an audit log entry. \n\n"
        "Validation: \n"
        "- Status validation restrictions: \n"
        "\t- status `PLANNED` can be updated to `ACTIVE` or `ABORTED`; \n"
        "\t- status `ACTIVE` can be updated to `COMPLETED` or `ABORTED`; \n"
        "\t- statuses `COMPLETED` or `ABORTED` cannot be updated. \n"
        "- Mission cannot be updated to status `ACTIVE` "
        "if it has assigned inactive drones."
    ),
    permission_code="CanUpdateMissionStatus",
    parameters=[
        OpenApiParameter(
            name="id",
            type=int,
            location=OpenApiParameter.PATH,
            description="ID of the mission.",
        )
    ],
    request=MissionStatusUpdateSerializer,
    responses={
        status.HTTP_200_OK: OpenApiResponse(
            response=MissionStatusUpdateSerializer,
            description="Mission status updated successfully.",
        ),
        status.HTTP_400_BAD_REQUEST: OpenApiResponse(
            description="Bad Request",
            response=dict,
            examples=[
                OpenApiExample(
                    name="Invalid status",
                    value={
                        "status": "Cannot change status from 'completed' to 'planned'."
                    },
                )
            ],
        ),
    },
    error_statuses=[status.HTTP_403_FORBIDDEN, status.HTTP_404_NOT_FOUND],
    examples=[
        OpenApiExample(
            name="Valid Request",
            value={"status": "completed"},
        )
    ],
)

mission_assignment_get_schema = description_schema(
    tags=["mission assignments"],
    summary="List drone assignments for a mission",
    description=(
        "Retrieves a list of all drones and "
        "their designated operators assigned to a specific mission."
    ),
    permission_code="PERMISSION_MISSIONS_VIEW",
    parameters=[
        OpenApiParameter(
            name="mission_pk",
            type=int,
            location=OpenApiParameter.PATH,
            description="ID of the mission.",
        )
    ],
    request=None,
    responses={
        status.HTTP_200_OK: OpenApiResponse(
            response=MissionDroneSerializer(many=True),
            description=(
                "Successfully retrieved the list "
                "of mission drone and operator assignments."
            ),
        ),
    },
    error_statuses=[status.HTTP_403_FORBIDDEN, status.HTTP_404_NOT_FOUND],
    examples=[
        OpenApiExample(
            name="Valid Request",
            value=assignment_example_value,
        )
    ],
)

mission_assignment_post_schema = description_schema(
    tags=["mission assignments"],
    summary="Assign a drone and operator to a mission",
    description=(
        "Deploys a specific drone and maps an operator to the given mission. "
        "Validation: \n"
        "- User selected as a operator must have an Operator role. \n"
        "- Assignments can only be added to planned missions. \n"
        "- Mission must have a start time before assigning drones or operators. \n"
        "- All assigned drones must be active. \n"
        "- Operators and drones cannot be assigned to overlapping missions."
    ),
    permission_code="IsDispatcherOrAdmin, PERMISSION_MISSIONS_ASSIGN",
    parameters=[
        OpenApiParameter(
            name="mission_pk",
            type=int,
            location=OpenApiParameter.PATH,
            description="ID of the target mission.",
        )
    ],
    request=MissionDroneSerializer,
    responses={
        status.HTTP_201_CREATED: OpenApiResponse(
            response=MissionDroneSerializer,
            description="Drone and operator successfully assigned to the mission.",
        ),
    },
    error_statuses=[
        status.HTTP_400_BAD_REQUEST,
        status.HTTP_403_FORBIDDEN,
        status.HTTP_404_NOT_FOUND,
    ],
    examples=[
        OpenApiExample(
            name="Valid Request.",
            value={"drone": 21, "operator": 28},
            request_only=True,
        ),
        OpenApiExample(name="Valid Request.", value=assignment_example_value),
    ],
)

mission_assignment_delete_schema = description_schema(
    tags=["mission assignments"],
    summary="Remove a drone assignment from a mission",
    description=(
        "Deletes a specific drone assignment and creates an audit log entry. \n\n"
        "Validation: \n"
        "- Cannot delete assignment unless mission is planned."
    ),
    permission_code="IsDispatcherOrAdmin, PERMISSION_MISSIONS_ASSIGN",
    parameters=[
        OpenApiParameter(
            name="mission_pk",
            type=int,
            location=OpenApiParameter.PATH,
            description="ID of the parent mission.",
        ),
        OpenApiParameter(
            name="pk",
            type=int,
            location=OpenApiParameter.PATH,
            description="ID of the specific drone assignment to be removed.",
        ),
    ],
    request=None,
    responses={
        status.HTTP_204_NO_CONTENT: OpenApiResponse(
            description="Assignment successfully deleted. No content is returned."
        ),
        status.HTTP_400_BAD_REQUEST: OpenApiResponse(
            description="Cannot delete assignment unless mission is planned."
        ),
    },
    error_statuses=[status.HTTP_403_FORBIDDEN, status.HTTP_404_NOT_FOUND],
)
