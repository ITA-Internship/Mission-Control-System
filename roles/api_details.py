from drf_spectacular.utils import OpenApiExample, OpenApiResponse
from rest_framework import status

from common.api_description_schema import description_schema

from .serializers import RoleSerializer

role_list_schema = description_schema(
    summary="List roles",
    description=(
        "Retrieves the full list of roles available in the system. "
        "Intended to populate role filters and the create-user / change-role "
        "selection controls. This endpoint is not paginated."
    ),
    permission_code="PERMISSION_ROLES_VIEW",
    request=None,
    responses={
        status.HTTP_200_OK: OpenApiResponse(
            response=RoleSerializer(many=True),
            description="Successfully retrieved the list of roles.",
        ),
    },
    error_statuses=[status.HTTP_403_FORBIDDEN],
    examples=[
        OpenApiExample(
            name="Valid Request",
            response_only=True,
            status_codes=[status.HTTP_200_OK],
            value={"id": 1, "code": "ADMIN", "name": "Admin"},
        )
    ],
)
