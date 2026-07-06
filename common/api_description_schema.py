from drf_spectacular.utils import extend_schema, OpenApiResponse
from rest_framework import status


STATUS_403_FORBIDDEN = OpenApiResponse(description="Forbidden. User does not have permission to perform this action.")
STATUS_400_BAD_REQUEST = OpenApiResponse(description="Bad Request. Provided payload contains validation errors.")
STATUS_404_NOT_FOUND = OpenApiResponse(description="Not Found")
STATUS_429_TOO_MANY_REQUESTS = OpenApiResponse(description="Export rate limit exceeded")

DEFAULT_ERRORS = {
    status.HTTP_400_BAD_REQUEST: STATUS_400_BAD_REQUEST,
    status.HTTP_403_FORBIDDEN: STATUS_403_FORBIDDEN,
    status.HTTP_404_NOT_FOUND: STATUS_404_NOT_FOUND,
    status.HTTP_429_TOO_MANY_REQUESTS: STATUS_429_TOO_MANY_REQUESTS,
}


def description_schema(
        summary: str,
        description: str,
        request=None,
        responses=None,
        examples=None,
        permission_code: str = None,
        error_statuses: list = None,
        **kwargs
):
    final_responses = responses.copy() if responses else {}

    if error_statuses:
        for code in error_statuses:
            if code not in final_responses:
                final_responses[code] = DEFAULT_ERRORS.get(code, OpenApiResponse(description="Error"))

    final_description = description
    if permission_code:
        permission_str = f"\n\nRequired permission: `{permission_code}`."
        final_description = f"{description.strip()}{permission_str}"

    return extend_schema(
        summary=summary,
        description=final_description,
        request=request,
        responses=final_responses,
        examples=examples,
        **kwargs
    )