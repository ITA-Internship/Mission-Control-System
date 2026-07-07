from drf_spectacular.utils import OpenApiExample, OpenApiParameter, OpenApiResponse
from rest_framework import status

from common.api_description_schema import description_schema

from .serializers import (
    AuditLogSerializer,
    ChangePasswordSerializer,
    PasswordResetConfirmSerializer,
    PasswordResetRequestSerializer,
    UserMeSerializer,
    UserRegistrationSerializer,
    UserRoleUpdateResponseSerializer,
    UserRoleUpdateSerializer,
    UserStatusUpdateSerializer,
)

user_registration_schema = description_schema(
    summary="Register a new user",
    description=(
        "Creates a new user. "
        "Sends an activation email to the user and creates an audit log entry. \n\n"
        "Validation: \n"
        "- Image file size cannot exceed 5 MB. \n"
        "- Supported image file formats: .jpg, .jpeg, .png, .webp. "
    ),
    permission_code="PERMISSION_USERS_CREATE",
    request=UserRegistrationSerializer,
    responses={
        status.HTTP_201_CREATED: OpenApiResponse(
            response=UserRegistrationSerializer,
            description="User account successfully created.",
        ),
        status.HTTP_400_BAD_REQUEST: OpenApiResponse(
            response=UserRegistrationSerializer,
            description="Bad Request",
            examples=[
                OpenApiExample(
                    name="Invalid profile picture file extension",
                    value={
                        "profile_picture": (
                            "Unsupported file format. "
                            "Allowed are: .jpg, .jpeg, .png, .webp."
                        )
                    },
                ),
                OpenApiExample(
                    name="Invalid profile picture file size",
                    value={"profile_picture": "Image size cannot exceed 5MB."},
                ),
            ],
        ),
    },
    error_statuses=[status.HTTP_403_FORBIDDEN],
    examples=[
        OpenApiExample(
            name="Valid request",
            value={
                "username": "oleksandr.koval",
                "email": "oleksandr.koval@example.com",
                "first_name": "Oleksandr",
                "last_name": "Koval",
                "rank": "Colonel",
                "contact": "+380000000000",
                "role": 1,
                "unit": 7,
            },
        ),
    ],
)

user_role_update_schema = description_schema(
    summary="Update user role",
    description=(
        "Updates the role of a specific user and creates an audit log entry. \n\n"
        "Validation: \n"
        "- Role ID is required and must be valid. \n"
        "- The role of an inactive user cannot be changed. \n"
        "- Admin user cannot remove their own admin role. \n"
        "- The admin role cannot be removed from the root account. \n"
        "- The admin role cannot be removed from the last admin user. "
    ),
    permission_code="PERMISSION_USERS_MANAGE_ROLES",
    parameters=[
        OpenApiParameter(
            name="user_id",
            type=int,
            location=OpenApiParameter.PATH,
            description="ID of the user whose role is being updated.",
        )
    ],
    request=UserRoleUpdateSerializer,
    responses={
        status.HTTP_200_OK: OpenApiResponse(
            response=UserRoleUpdateResponseSerializer,
            description="User role successfully updated.",
        ),
        status.HTTP_400_BAD_REQUEST: OpenApiResponse(
            response=UserRoleUpdateResponseSerializer,
            description="Bad Request",
            examples=[
                OpenApiExample(
                    name="Missing required field",
                    value={"role_id": "This field is required."},
                ),
                OpenApiExample(
                    name="Invalid field value", value={"role_id": "Invalid role_id"}
                ),
                OpenApiExample(
                    name="Changing role of an inactive user",
                    value={"role_id": "Cannot change the role of an inactive user."},
                ),
            ],
        ),
    },
    error_statuses=[status.HTTP_403_FORBIDDEN, status.HTTP_404_NOT_FOUND],
    examples=[
        OpenApiExample(
            name="Valid request",
            value={
                "role_id": 3,
            },
        )
    ],
)

activate_account_schema = description_schema(
    summary="Activate user account",
    description=(
        "Validates the activation token provided via the URL parameters. "
        "If the token is valid, it sets the user's new password "
        "and creates an audit log entry. "
    ),
    permission_code="AllowAny",
    parameters=[
        OpenApiParameter(
            name="user_id",
            type=int,
            location=OpenApiParameter.PATH,
            description="The ID of the user activating the account.",
            required=True,
        ),
        OpenApiParameter(
            name="token",
            type=str,
            location=OpenApiParameter.PATH,
            description="The one-time secure activation token generated for the user.",
            required=True,
        ),
    ],
    request=None,
    responses={
        status.HTTP_200_OK: OpenApiResponse(
            description="Your account has been activated. You can now log in."
        ),
        status.HTTP_400_BAD_REQUEST: OpenApiResponse(
            description="Bad Request",
            response=dict,
            examples=[
                OpenApiExample(
                    name="Activation link error",
                    value={"detail": "Invalid or expired activation link."},
                ),
                OpenApiExample(
                    name="Missing required field",
                    value={"password": "This field is required."},
                ),
            ],
        ),
    },
    error_statuses=[status.HTTP_404_NOT_FOUND],
)

audit_log_view_schema = description_schema(
    summary="List audit logs",
    description=(
        "Retrieves a paginated and filtered list of audit logs. "
        "Superusers and staff members can view all logs. "
        "Other authenticated users can only view logs where "
        "they are either the actor or the target user."
    ),
    permission_code="PERMISSION_AUDIT_LOGS_VIEW_OWN, PERMISSION_AUDIT_LOGS_VIEW_ALL",
    request=None,
    responses={
        status.HTTP_200_OK: OpenApiResponse(
            response=AuditLogSerializer(many=True),
            description="Successfully retrieved the list of audit logs.",
        ),
    },
    error_statuses=[status.HTTP_403_FORBIDDEN],
    examples=[
        OpenApiExample(
            name="Valid Request",
            response_only=True,
            status_codes=[status.HTTP_200_OK],
            value={
                "id": 3,
                "actor": 1,
                "actor_username": "user",
                "target_user": 1,
                "target_user_username": "user",
                "action_type": "LOGOUT",
                "result": "SUCCESS",
                "description": "User logged out successfully",
                "ip_address": "127.0.0.1",
                "user_agent": "Test Agent Value",
                "created_at": "2026-06-25T14:44:49.068836Z",
            },
        )
    ],
)

audit_log_retrieve_schema = description_schema(
    summary="Retrieve an audit log",
    description=(
        "Retrieves detailed information about specific audit log entry by its ID. "
        "Superusers and staff members can view all logs. "
        "Other authenticated users can only view logs where "
        "they are either the actor or the target user."
    ),
    permission_code="IsAuthenticated",
    parameters=[
        OpenApiParameter(
            name="id",
            type=int,
            location=OpenApiParameter.PATH,
            description="ID of specific audit log.",
        )
    ],
    request=None,
    responses={
        status.HTTP_200_OK: OpenApiResponse(
            response=AuditLogSerializer,
            description="Audit log details successfully retrieved.",
        ),
    },
    error_statuses=[status.HTTP_403_FORBIDDEN, status.HTTP_404_NOT_FOUND],
    examples=[
        OpenApiExample(
            name="Audit Log Details",
            response_only=True,
            value={
                "id": 3,
                "actor": 1,
                "actor_username": "user",
                "target_user": 1,
                "target_user_username": "user",
                "action_type": "LOGOUT",
                "result": "SUCCESS",
                "description": "User logged out successfully",
                "ip_address": "127.0.0.1",
                "user_agent": "Test Agent Value",
                "created_at": "2026-06-25T14:44:49.068836Z",
            },
        ),
    ],
)

audit_log_export_schema = description_schema(
    summary="Export audit logs to CSV",
    description=(
        "Generates and downloads a CSV file "
        "with the filtered audit logs. "
        "Supports full filtering and sorting identical "
        "to the standard list endpoint. \n\n"
        "The export is limited to a maximum of 10,000 records. "
    ),
    permission_code="IsAuthenticated",
    request=None,
    responses={
        status.HTTP_200_OK: OpenApiResponse(
            description="A CSV file containing audit logs generated successfully."
        ),
    },
    error_statuses=[status.HTTP_403_FORBIDDEN, status.HTTP_429_TOO_MANY_REQUESTS],
)

user_status_update_schema = description_schema(
    summary="Update user status",
    description=(
        "Allows system administrators to activate or deactivate a user's account, "
        "creates an audit log entry. \n\n"
        "Validation: \n"
        "- User cannot deactivate their own account. "
    ),
    permission_code="IsSystemAdmin",
    parameters=[
        OpenApiParameter(
            name="pk",
            type=int,
            location=OpenApiParameter.PATH,
            description="The ID of the target user whose status is being updated.",
            required=True,
        ),
    ],
    request=UserStatusUpdateSerializer,
    responses={
        status.HTTP_200_OK: OpenApiResponse(
            description="User status updated successfully.",
            examples=[
                OpenApiExample(
                    name="User already has required status.",
                    value={"detail": "User is already Active."},
                )
            ],
        ),
        status.HTTP_400_BAD_REQUEST: OpenApiResponse(
            description="Bad Request",
            examples=[
                OpenApiExample(
                    name="Deactivating invalid account",
                    value={"detail": "You cannot deactivate your own account."},
                )
            ],
        ),
    },
    error_statuses=[status.HTTP_403_FORBIDDEN, status.HTTP_404_NOT_FOUND],
    examples=[
        OpenApiExample(
            name="Valid request",
            value={
                "is_active": True,
            },
        )
    ],
)

user_me_get_schema = description_schema(
    summary="Retrieve current user profile",
    description=(
        "Retrieves the profile details of the currently authenticated user "
        "based on the authentication token provided in the request headers."
    ),
    permission_code="IsAuthenticated",
    request=None,
    responses={
        status.HTTP_200_OK: OpenApiResponse(
            response=UserMeSerializer,
            description="Profile details successfully retrieved.",
        ),
    },
    error_statuses=[status.HTTP_403_FORBIDDEN],
    examples=[
        OpenApiExample(
            name="Valid Request",
            value={
                "id": 24,
                "username": "oleksander.koval",
                "email": "oleksander.koval@example.com",
                "first_name": "Oleksandr",
                "last_name": "Koval",
                "rank": "Colonel",
                "contact": "+380000000000",
                "profile_picture": None,
                "role": 1,
                "unit": 7,
                "is_active": True,
            },
        )
    ],
)

user_me_update_schema = description_schema(
    summary="Update current user profile",
    description=(
        "Updates the currently authenticated user's profile information "
        "and creates an audit log entry.\n\n"
        "Validation: \n"
        "- Image file size cannot exceed 5 MB. \n"
        "- Supported image file formats: .jpg, .jpeg, .png, .webp. "
    ),
    permission_code="IsAuthenticated",
    request=UserMeSerializer,
    responses={
        status.HTTP_200_OK: OpenApiResponse(
            response=UserMeSerializer,
            description="Profile information successfully updated.",
        ),
    },
    error_statuses=[status.HTTP_400_BAD_REQUEST, status.HTTP_403_FORBIDDEN],
    examples=[
        OpenApiExample(
            name="Valid Request",
            request_only=True,
            value={
                "first_name": "Oleksandr",
                "last_name": "Koval",
                "rank": "Colonel",
                "contact": "+380000000000",
            },
        ),
        OpenApiExample(
            name="Valid Request",
            response_only=True,
            value={
                "id": 24,
                "username": "oleksander.koval",
                "email": "oleksander.koval@example.com",
                "first_name": "Oleksandr",
                "last_name": "Koval",
                "rank": "Colonel",
                "contact": "+380000000000",
                "profile_picture": None,
                "role": 1,
                "unit": 7,
                "is_active": True,
            },
        ),
    ],
)

change_password_schema = description_schema(
    summary="Change user password",
    description=(
        "Changes the password for the currently authenticated user "
        "and creates an audit log entry. "
        "Upon a successful password change, "
        "all active sessions for this user are invalidated. "
    ),
    permission_code="IsAuthenticated",
    request=ChangePasswordSerializer,
    responses={
        status.HTTP_200_OK: OpenApiResponse(
            description=(
                "Password changed successfully. Active sessions have been invalidated."
            ),
        ),
    },
    error_statuses=[status.HTTP_400_BAD_REQUEST, status.HTTP_403_FORBIDDEN],
    examples=[
        OpenApiExample(
            name="Valid Request",
            value={
                "old_password": "my_old_password_123",
                "new_password": "my_new_password_123",
            },
        )
    ],
)

password_reset_schema = description_schema(
    summary="Initiate password reset",
    description=(
        "Accepts a user's email address "
        "and sends a password reset link "
        "containing a secure, one-time token to that email. "
        "Always returns a 200 OK response with a generic message, "
        "regardless of whether the email address exists in the system. "
        "An audit log entry and an email are "
        "only generated if a matching user is found."
    ),
    permission_code="AllowAny",
    request=PasswordResetRequestSerializer,
    responses={
        status.HTTP_200_OK: OpenApiResponse(
            response=PasswordResetRequestSerializer,
            description=(
                "Success. A generic response indicating that if the email exists, "
                "a password reset link has been dispatched."
            ),
        ),
    },
    error_statuses=[status.HTTP_400_BAD_REQUEST],
)

password_reset_confirm_schema = description_schema(
    summary="Confirm password reset",
    description=(
        "Validates the secure link parameters sent via email. "
        "If valid, updates the user's password to the newly provided one, "
        "invalidates all current sessions for this user, sends a confirmation email, "
        "and records a successful audit log. "
    ),
    permission_code="AllowAny",
    request=PasswordResetConfirmSerializer,
    parameters=[
        OpenApiParameter(
            name="uidb64",
            type=str,
            location=OpenApiParameter.PATH,
            description="The Base64-encoded unique identifier of the user.",
            required=True,
        ),
        OpenApiParameter(
            name="token",
            type=str,
            location=OpenApiParameter.PATH,
            description="The one-time secure password reset token generated for the user.",
            required=True,
        ),
    ],
    responses={
        status.HTTP_200_OK: OpenApiResponse(
            description=(
                "Password has been successfully reset. User sessions invalidated."
            ),
        ),
    },
    error_statuses=[status.HTTP_400_BAD_REQUEST],
)
