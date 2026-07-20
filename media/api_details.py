from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiExample, OpenApiParameter, OpenApiResponse
from rest_framework import status

from common.api_description_schema import description_schema
from config.settings import ARTIFACT_ALLOWED_EXTENSIONS, ARTIFACT_MAX_FILE_SIZE_MB
from media.serializers import (
    MediaAuditLogSerializer,
    MissionArtifactSerializer,
    MissionArtifactUploadSerializer,
    VideoMetadataSerializer,
    VideoUploadSerializer,
)

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
    summary="Download a mission artifact file",
    description=(
        "Returns the binary file for a mission artifact as an attachment. In "
        "production the file is delivered through a protected `X-Accel-Redirect` "
        "internal redirect; in debug mode the file is streamed directly. Access is "
        "restricted to administrators, the uploader, or users belonging to the "
        "artifact mission's unit.\n\n"
        "Returns 404 if the artifact does not exist or the stored file is missing "
        "from the server."
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
            description="ID of the artifact to download.",
        ),
    ],
    request=None,
    responses={
        status.HTTP_200_OK: OpenApiResponse(
            response=OpenApiTypes.BINARY,
            description=(
                "The artifact file is returned as an attachment "
                "with the appropriate content type."
            ),
        ),
    },
    error_statuses=[status.HTTP_403_FORBIDDEN, status.HTTP_404_NOT_FOUND],
)

media_audit_log_example_value = {
    "id": 5,
    "action": "view",
    "artifact": 1,
    "mission": 11,
    "user": {
        "id": 24,
        "username": "oleksandr.koval",
        "email": "oleksandr.koval@example.com",
    },
    "changes": {},
    "ip_address": "127.0.0.1",
    "created_at": "2026-07-02T02:28:43.353809Z",
}

media_audit_log_list_schema = description_schema(
    tags=["media"],
    summary="List media audit logs",
    description=(
        "Retrieves a paginated, read-only list of media audit log entries, "
        "recording view, upload, update, and delete actions on media records. "
        "Supports filtering by action, user, mission, artifact, and creation "
        "date range."
    ),
    permission_code="PERMISSION_MEDIA_VIEW_LOGS",
    parameters=[
        OpenApiParameter(
            name="action",
            type=str,
            location=OpenApiParameter.QUERY,
            description="Filter by action type (`view`, `upload`, `update`, `delete`).",
            required=False,
        ),
        OpenApiParameter(
            name="user",
            type=int,
            location=OpenApiParameter.QUERY,
            description="Filter by the ID of the acting user.",
            required=False,
        ),
        OpenApiParameter(
            name="mission",
            type=int,
            location=OpenApiParameter.QUERY,
            description="Filter by the related mission ID.",
            required=False,
        ),
        OpenApiParameter(
            name="artifact",
            type=int,
            location=OpenApiParameter.QUERY,
            description="Filter by the related artifact ID.",
            required=False,
        ),
        OpenApiParameter(
            name="start_date",
            type=str,
            location=OpenApiParameter.QUERY,
            description="Optional ISO 8601 lower bound for the creation timestamp.",
            required=False,
        ),
        OpenApiParameter(
            name="end_date",
            type=str,
            location=OpenApiParameter.QUERY,
            description="Optional ISO 8601 upper bound for the creation timestamp.",
            required=False,
        ),
    ],
    request=None,
    responses={
        status.HTTP_200_OK: OpenApiResponse(
            response=MediaAuditLogSerializer(many=True),
            description="Successfully retrieved the list of media audit logs.",
        ),
    },
    error_statuses=[status.HTTP_403_FORBIDDEN],
    examples=[
        OpenApiExample(
            name="Valid request",
            response_only=True,
            value=media_audit_log_example_value,
        ),
    ],
)

media_audit_log_retrieve_schema = description_schema(
    tags=["media"],
    summary="Retrieve a media audit log",
    description=(
        "Retrieves detailed information about a specific media audit log entry "
        "by its ID."
    ),
    permission_code="PERMISSION_MEDIA_VIEW_LOGS",
    parameters=[
        OpenApiParameter(
            name="id",
            type=int,
            location=OpenApiParameter.PATH,
            description="ID of the media audit log entry.",
        ),
    ],
    request=None,
    responses={
        status.HTTP_200_OK: OpenApiResponse(
            response=MediaAuditLogSerializer,
            description="Media audit log details successfully retrieved.",
        ),
    },
    error_statuses=[status.HTTP_403_FORBIDDEN, status.HTTP_404_NOT_FOUND],
    examples=[
        OpenApiExample(
            name="Valid request",
            response_only=True,
            value=media_audit_log_example_value,
        ),
    ],
)

video_metadata_example_value = {
    "id": 3,
    "mission": 11,
    "drone": 21,
    "uploader": 24,
    "uploader_username": "oleksandr.koval",
    "file": "http://localhost:8000/media/videos/mission_11/recon.mp4",
    "file_name": "recon.mp4",
    "file_size": 20984320,
    "content_type": "video/mp4",
    "status": "ready",
    "checksum": "9f2c1a4b8e5d6f70a1b2c3d4e5f60718",
    "duration_seconds": 132,
    "recorded_at": "2026-06-02T02:28:43Z",
    "created_at": "2026-07-02T02:28:43.353809Z",
    "updated_at": "2026-07-02T02:28:43.353809Z",
    "url": "http://localhost:8000/media/videos/mission_11/recon.mp4",
}

video_metadata_list_schema = description_schema(
    tags=["media"],
    summary="List video metadata records",
    description=(
        "Retrieves a paginated list of video metadata records. Supports filtering "
        "by mission, drone, uploader, status, and creation/recording date ranges."
    ),
    permission_code="PERMISSION_MEDIA_VIEW",
    parameters=[
        OpenApiParameter(
            name="mission_id",
            type=int,
            location=OpenApiParameter.QUERY,
            description="Filter by mission ID (alias: `mission`).",
            required=False,
        ),
        OpenApiParameter(
            name="drone_id",
            type=int,
            location=OpenApiParameter.QUERY,
            description="Filter by drone ID (alias: `drone`).",
            required=False,
        ),
        OpenApiParameter(
            name="uploader_id",
            type=int,
            location=OpenApiParameter.QUERY,
            description="Filter by uploader user ID (alias: `uploader`).",
            required=False,
        ),
        OpenApiParameter(
            name="status",
            type=str,
            location=OpenApiParameter.QUERY,
            description="Filter by status (`uploading`, `ready`, `failed`).",
            required=False,
        ),
        OpenApiParameter(
            name="created_after",
            type=str,
            location=OpenApiParameter.QUERY,
            description="Filter by creation date lower bound (format YYYY-MM-DD).",
            required=False,
        ),
        OpenApiParameter(
            name="created_before",
            type=str,
            location=OpenApiParameter.QUERY,
            description="Filter by creation date upper bound (format YYYY-MM-DD).",
            required=False,
        ),
        OpenApiParameter(
            name="recorded_after",
            type=str,
            location=OpenApiParameter.QUERY,
            description="Filter by recording date lower bound (format YYYY-MM-DD).",
            required=False,
        ),
        OpenApiParameter(
            name="recorded_before",
            type=str,
            location=OpenApiParameter.QUERY,
            description="Filter by recording date upper bound (format YYYY-MM-DD).",
            required=False,
        ),
    ],
    request=None,
    responses={
        status.HTTP_200_OK: OpenApiResponse(
            response=VideoMetadataSerializer(many=True),
            description="Successfully retrieved the list of video metadata records.",
        ),
        status.HTTP_400_BAD_REQUEST: OpenApiResponse(
            description="Bad Request",
            response=dict,
            examples=[
                OpenApiExample(
                    name="Invalid filter value",
                    value={"mission_id": "Must be an integer."},
                ),
                OpenApiExample(
                    name="Invalid date format",
                    value={"created_after": "Expected format YYYY-MM-DD."},
                ),
            ],
        ),
    },
    error_statuses=[status.HTTP_403_FORBIDDEN],
    examples=[
        OpenApiExample(
            name="Valid request",
            response_only=True,
            value=video_metadata_example_value,
        ),
    ],
)

video_metadata_create_schema = description_schema(
    tags=["media"],
    summary="Upload a video metadata record",
    description=(
        "Uploads a new video file and creates its metadata record. The uploader is "
        "set to the authenticated user and the record starts in the `uploading` "
        "status while the duration is extracted asynchronously.\n\n"
        "Validation: \n"
        "- The selected drone must be assigned to the selected mission."
    ),
    permission_code="PERMISSION_MEDIA_UPLOAD",
    request=VideoUploadSerializer,
    responses={
        status.HTTP_201_CREATED: OpenApiResponse(
            response=VideoUploadSerializer,
            description="Video metadata record created successfully.",
        ),
        status.HTTP_400_BAD_REQUEST: OpenApiResponse(
            description="Bad Request",
            response=dict,
            examples=[
                OpenApiExample(
                    name="Drone not assigned to mission",
                    value={"drone": "Drone must be assigned to the selected mission."},
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
                "mission": 11,
                "drone": 21,
                "file": "recon.mp4",
                "recorded_at": "2026-06-02T02:28:43Z",
                "checksum": "9f2c1a4b8e5d6f70a1b2c3d4e5f60718",
            },
        ),
        OpenApiExample(
            name="Valid Request",
            response_only=True,
            value={
                "id": 3,
                "mission": 11,
                "drone": 21,
                "file": "http://localhost:8000/media/videos/mission_11/recon.mp4",
                "recorded_at": "2026-06-02T02:28:43Z",
                "checksum": "9f2c1a4b8e5d6f70a1b2c3d4e5f60718",
            },
        ),
    ],
)

video_metadata_retrieve_schema = description_schema(
    tags=["media"],
    summary="Retrieve a video metadata record",
    description=(
        "Retrieves detailed information about a specific video metadata record "
        "by its ID."
    ),
    permission_code="PERMISSION_MEDIA_VIEW",
    parameters=[
        OpenApiParameter(
            name="id",
            type=int,
            location=OpenApiParameter.PATH,
            description="ID of the video metadata record.",
        ),
    ],
    request=None,
    responses={
        status.HTTP_200_OK: OpenApiResponse(
            response=VideoMetadataSerializer,
            description="Video metadata details successfully retrieved.",
        ),
    },
    error_statuses=[status.HTTP_403_FORBIDDEN, status.HTTP_404_NOT_FOUND],
    examples=[
        OpenApiExample(
            name="Valid request",
            response_only=True,
            value=video_metadata_example_value,
        ),
    ],
)

video_metadata_update_schema = description_schema(
    tags=["media"],
    summary="Update a video metadata record",
    description=(
        "Fully updates the writable fields (mission, drone, recorded date, and "
        "checksum) of a video metadata record. File contents and system-managed "
        "fields such as status and duration cannot be changed through this endpoint."
    ),
    permission_code="PERMISSION_MEDIA_DELETE",
    parameters=[
        OpenApiParameter(
            name="id",
            type=int,
            location=OpenApiParameter.PATH,
            description="ID of the video metadata record to update.",
        ),
    ],
    request=VideoMetadataSerializer,
    responses={
        status.HTTP_200_OK: OpenApiResponse(
            response=VideoMetadataSerializer,
            description="Video metadata record updated successfully.",
        ),
    },
    error_statuses=[
        status.HTTP_400_BAD_REQUEST,
        status.HTTP_403_FORBIDDEN,
        status.HTTP_404_NOT_FOUND,
    ],
    examples=[
        OpenApiExample(
            name="Valid Request",
            request_only=True,
            value={
                "mission": 11,
                "drone": 21,
                "recorded_at": "2026-06-02T02:28:43Z",
                "checksum": "9f2c1a4b8e5d6f70a1b2c3d4e5f60718",
            },
        ),
        OpenApiExample(
            name="Valid Request",
            response_only=True,
            value=video_metadata_example_value,
        ),
    ],
)

video_metadata_partial_update_schema = description_schema(
    tags=["media"],
    summary="Partially update a video metadata record",
    description=(
        "Updates one or more writable fields (mission, drone, recorded date, or "
        "checksum) of a video metadata record. File contents and system-managed "
        "fields such as status and duration cannot be changed through this endpoint."
    ),
    permission_code="PERMISSION_MEDIA_DELETE",
    parameters=[
        OpenApiParameter(
            name="id",
            type=int,
            location=OpenApiParameter.PATH,
            description="ID of the video metadata record to update.",
        ),
    ],
    request=VideoMetadataSerializer,
    responses={
        status.HTTP_200_OK: OpenApiResponse(
            response=VideoMetadataSerializer,
            description="Video metadata record updated successfully.",
        ),
    },
    error_statuses=[
        status.HTTP_400_BAD_REQUEST,
        status.HTTP_403_FORBIDDEN,
        status.HTTP_404_NOT_FOUND,
    ],
    examples=[
        OpenApiExample(
            name="Valid Request",
            request_only=True,
            value={"recorded_at": "2026-06-02T02:28:43Z"},
        ),
        OpenApiExample(
            name="Valid Request",
            response_only=True,
            value=video_metadata_example_value,
        ),
    ],
)

video_metadata_destroy_schema = description_schema(
    tags=["media"],
    summary="Delete a video metadata record",
    description="Deletes a specific video metadata record by its ID.",
    permission_code="PERMISSION_MEDIA_DELETE",
    parameters=[
        OpenApiParameter(
            name="id",
            type=int,
            location=OpenApiParameter.PATH,
            description="ID of the video metadata record to delete.",
        ),
    ],
    request=None,
    responses={
        status.HTTP_204_NO_CONTENT: OpenApiResponse(
            description="Video metadata record successfully deleted. No content.",
        ),
        status.HTTP_400_BAD_REQUEST: OpenApiResponse(
            description="Bad Request",
            response=dict,
            examples=[
                OpenApiExample(
                    name="Protected by dependencies",
                    value={
                        "detail": (
                            "Cannot delete this record because it is protected "
                            "by dependencies."
                        )
                    },
                ),
            ],
        ),
    },
    error_statuses=[status.HTTP_403_FORBIDDEN, status.HTTP_404_NOT_FOUND],
)
