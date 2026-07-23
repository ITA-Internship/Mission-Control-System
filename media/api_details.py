from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiExample, OpenApiParameter, OpenApiResponse
from rest_framework import status

from common.api_description_schema import description_schema
from config.settings import ARTIFACT_ALLOWED_EXTENSIONS, ARTIFACT_MAX_FILE_SIZE_MB
from media.serializers import MissionArtifactSerializer, MissionArtifactUploadSerializer

artifact_example_value = {
    "id": 1,
    "mission": 11,
    "uploaded_by": {
        "id": 24,
        "username": "oleksandr.koval",
        "email": "oleksandr.koval@example.com",
    },
    "title": "Example Title",
    "description": None,
    "file": "http://localhost:8000/media/artifacts/mission_11/d4ab2e.png",
    "file_type": "image",
    "original_filename": "test_drone_photo.png",
    "file_size": 982936,
    "storage_backend": "local",
    "captured_at": "2026-06-02T02:28:43.353809Z",
    "uploaded_at": "2026-07-02T02:28:43.353809Z",
}

artifact_get_schema = description_schema(
    tags=["media"],
    summary="List all artifacts for a specific mission",
    description=(
        "Retrieves a paginated list of artifacts associated with a given mission."
    ),
    permission_code="PERMISSION_MEDIA_VIEW",
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
            response=MissionArtifactSerializer(many=True),
            description="Successfully retrieved the list of mission artifacts.",
        ),
    },
    error_statuses=[status.HTTP_403_FORBIDDEN, status.HTTP_404_NOT_FOUND],
    examples=[OpenApiExample(name="Valid Request", value=artifact_example_value)],
)

formatted_extensions = "\n".join(
    f"\t- {file_type}: {', '.join(exts)}"
    for file_type, exts in ARTIFACT_ALLOWED_EXTENSIONS.items()
)

artifact_post_schema = description_schema(
    tags=["media"],
    summary="Upload a new artifact to a mission",
    description=(
        "Uploads a media file or document as an artifact for a specific mission. \n\n"
        "Validation: \n"
        f"- File must have one of the following formats:\n{formatted_extensions}\n"
        f"- File size cannot be empty or exceed {ARTIFACT_MAX_FILE_SIZE_MB}MB."
    ),
    permission_code="PERMISSION_MEDIA_UPLOAD",
    parameters=[
        OpenApiParameter(
            name="mission_pk",
            type=int,
            location=OpenApiParameter.PATH,
            description="ID of the mission.",
        )
    ],
    request=MissionArtifactUploadSerializer,
    responses={
        status.HTTP_201_CREATED: OpenApiResponse(
            response=MissionArtifactSerializer,
            description="Artifact successfully uploaded.",
            examples=[
                OpenApiExample(
                    name="Valid Request.",
                    value=artifact_example_value,
                )
            ],
        ),
        status.HTTP_400_BAD_REQUEST: OpenApiResponse(
            description="Bad Request",
            response=dict,
            examples=[
                OpenApiExample(
                    name="Missing required fild", value={"title": "Title is required."}
                ),
                OpenApiExample(
                    name="Invalid uploaded file",
                    value={"file": "File is empty or its size cannot be determined."},
                ),
                OpenApiExample(
                    name="Unsupported file format",
                    value={
                        "file": "Unsupported file type '.md'. "
                        "Allowed: .csv, .jpeg, .jpg, .json, .png."
                    },
                ),
            ],
        ),
    },
    error_statuses=[status.HTTP_403_FORBIDDEN, status.HTTP_404_NOT_FOUND],
    examples=[
        OpenApiExample(
            request_only=True,
            response_only=False,
            name="Valid Artifact Upload Example",
            value={"file": "test_drone_photo.png", "title": "Test Drone Photo"},
        )
    ],
)

artifact_detail_get_schema = description_schema(
    tags=["media"],
    summary="Retrieve specific artifact details",
    description=(
        "Retrieves detailed information for a single mission artifact by its ID."
    ),
    permission_code="PERMISSION_MEDIA_VIEW",
    parameters=[
        OpenApiParameter(
            name="mission_pk",
            type=int,
            location=OpenApiParameter.PATH,
            description="ID of the mission.",
        ),
        OpenApiParameter(
            name="artifact_pk",
            type=int,
            location=OpenApiParameter.PATH,
            description="ID of the artifact.",
        ),
    ],
    request=None,
    responses={
        status.HTTP_200_OK: OpenApiResponse(
            response=MissionArtifactSerializer, description="Artifact detailed profile."
        ),
    },
    error_statuses=[status.HTTP_403_FORBIDDEN, status.HTTP_404_NOT_FOUND],
    examples=[
        OpenApiExample(
            name="Valid Request",
            value=artifact_example_value,
        )
    ],
)

artifact_detail_delete_schema = description_schema(
    tags=["media"],
    summary="Delete a mission artifact",
    description=(
        "Deletes the specified artifact from the mission "
        "and creates an audit log entry."
    ),
    permission_code="PERMISSION_MEDIA_DELETE",
    parameters=[
        OpenApiParameter(
            name="mission_pk",
            type=int,
            location=OpenApiParameter.PATH,
            description="ID of the mission.",
        ),
        OpenApiParameter(
            name="artifact_pk",
            type=int,
            location=OpenApiParameter.PATH,
            description="ID of the artifact.",
        ),
    ],
    request=None,
    responses={
        status.HTTP_204_NO_CONTENT: OpenApiResponse(
            description="Artifact successfully deleted. No content returned."
        ),
    },
    error_statuses=[status.HTTP_403_FORBIDDEN, status.HTTP_404_NOT_FOUND],
)

protected_media_get_schema = description_schema(
    tags=["media"],
    summary="Download a protected artifact file",
    description=(
        "Streams or internally redirects to the stored artifact file after "
        "object-level media access checks pass."
    ),
    permission_code="PERMISSION_MEDIA_VIEW",
    parameters=[
        OpenApiParameter(
            name="artifact_pk",
            type=int,
            location=OpenApiParameter.PATH,
            description="ID of the artifact to download.",
        )
    ],
    request=None,
    responses={
        status.HTTP_200_OK: OpenApiResponse(
            response=OpenApiTypes.BINARY,
            description="Artifact file returned successfully.",
        ),
    },
    error_statuses=[status.HTTP_403_FORBIDDEN, status.HTTP_404_NOT_FOUND],
)
