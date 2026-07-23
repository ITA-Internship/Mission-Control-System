"""Expose user management, authentication, and authorization endpoints.

Classes:
    UserRegistrationView: Handles user registration.
    UserRoleUpdateAPIView: Handles updating user roles.
    ActivateAccountAPIView: Handles user account activation via email tokens.
    AuditLogViewSet: Provides read-only access and CSV export for audit logs.
    UserStatusUpdateView: Manages user status (active/inactive) updates.
    UserMeView: Retrieves and updates the authenticated user's profile.
    ChangePasswordView: Handles password changes for the authenticated user.
    PasswordResetRequestView: Initiates the password reset process via email.
    PasswordResetConfirmView: Confirms and executes a password reset using a token.
    ProtectedProfilePictureView: Serves profile pictures securely.
"""

import csv
import mimetypes
import os
import posixpath

from django.conf import settings
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.tokens import default_token_generator
from django.core.exceptions import ValidationError as DjangoValidationError
from django.http import FileResponse, Http404, HttpResponse, StreamingHttpResponse
from django.shortcuts import get_object_or_404
from django.utils.encoding import escape_uri_path, force_bytes, force_str
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from django_filters import rest_framework as filters
from drf_spectacular.utils import extend_schema_view
from rest_framework import generics, permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView

from common.pagination import AuditLogPagination
from common.utils import EchoBuffer

from .api_details import (
    activate_account_schema,
    audit_log_export_schema,
    audit_log_retrieve_schema,
    audit_log_view_schema,
    change_password_schema,
    password_reset_confirm_schema,
    password_reset_schema,
    user_me_get_schema,
    user_me_update_schema,
    user_registration_schema,
    user_role_update_schema,
    user_status_update_schema,
)
from .models import AuditLog, User, UserStatusLog
from .permissions import HasRBACPermission, IsSystemAdmin, user_has_permission
from .rbac import (
    PERMISSION_AUDIT_LOGS_VIEW_ALL,
    PERMISSION_AUDIT_LOGS_VIEW_OWN,
    PERMISSION_USERS_CREATE,
    PERMISSION_USERS_MANAGE_ROLES,
)
from .serializers import (
    AccountActivationSerializer,
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
from .services import create_audit_log, set_user_password, update_user_role
from .tasks import send_email_task
from .throttles import (
    AccountActivationThrottle,
    PasswordResetConfirmThrottle,
    PasswordResetRequestThrottle,
)


@user_registration_schema
class UserRegistrationView(generics.CreateAPIView):
    """Register a new user account."""

    queryset = User.objects.all()
    serializer_class = UserRegistrationSerializer
    permission_classes = [HasRBACPermission]
    required_permission = PERMISSION_USERS_CREATE


@user_role_update_schema
class UserRoleUpdateAPIView(APIView):
    """Handle role updates for user accounts."""

    permission_classes = [HasRBACPermission]
    required_permission = PERMISSION_USERS_MANAGE_ROLES

    def patch(self, request, user_id):
        """Validate and update a specific user's role.

        Args:
            request (Request): The HTTP request containing the new role_id.
            user_id (int): The primary key of the target user.

        Returns:
            Response: The updated user role data or validation errors.
        """
        target_user = get_object_or_404(User.objects.select_related("role"), pk=user_id)

        serializer = UserRoleUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            updated_user = update_user_role(
                target_user=target_user,
                new_role_id=serializer.validated_data["role_id"],
                changed_by=request.user,
            )
        except DjangoValidationError as exc:
            return Response(exc.message_dict, status=status.HTTP_400_BAD_REQUEST)

        response_serializer = UserRoleUpdateResponseSerializer(updated_user)
        return Response(response_serializer.data, status=status.HTTP_200_OK)


@activate_account_schema
class ActivateAccountAPIView(APIView):
    """Handle account activation requests."""

    permission_classes = [AllowAny]
    throttle_classes = [AccountActivationThrottle]

    def post(self, request, user_id, token):
        """Activate a user account using the provided user ID and token.
        Args:
            request (Request): The HTTP request containing the user's initial password.
            user_id (int): The ID of the user to activate.
            token (str): The one-time activation token sent via email.

        Returns:
            Response: A success message or an error if the token is invalid/expired.

        """
        user = get_object_or_404(User, pk=user_id)

        if not default_token_generator.check_token(user, token):
            return Response(
                {"detail": "Invalid or expired activation link."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # A fully activated account is both active and already holds a usable
        # password. Reject those so this endpoint cannot double as a
        # token-scoped "set password" endpoint for live accounts.
        if user.is_active and user.has_usable_password():
            return Response(
                {"detail": "This account has already been activated."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = AccountActivationSerializer(
            data=request.data, context={"user": user}
        )
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        set_user_password(user, serializer.validated_data["password"])

        if not user.is_active:
            user.is_active = True
            user.save(update_fields=["is_active"])

        create_audit_log(
            actor=user,
            action_type=AuditLog.ActionType.ACCOUNT_ACTIVATED,
            result=AuditLog.ResultStatus.SUCCESS,
            target_user=user,
            description="Account activated",
            request=request,
        )

        return Response(
            {"detail": "Your account has been activated. You can now log in."},
            status=status.HTTP_200_OK,
        )


class AuditLogFilter(filters.FilterSet):
    """Filters audit logs by date and specific relational fields."""

    start_date = filters.DateFilter(field_name="created_at", lookup_expr="gte")
    end_date = filters.DateFilter(field_name="created_at", lookup_expr="lte")

    class Meta:
        model = AuditLog
        fields = ["actor", "target_user", "action_type", "result"]


@extend_schema_view(
    list=audit_log_view_schema,
    retrieve=audit_log_retrieve_schema,
    export=audit_log_export_schema,
)
class AuditLogViewSet(viewsets.ReadOnlyModelViewSet):
    """Provide read-only API endpoints for viewing and exporting logs"""

    serializer_class = AuditLogSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = AuditLogPagination
    filter_backends = [filters.DjangoFilterBackend]
    filterset_class = AuditLogFilter

    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "audit_export"

    def get_queryset(self):
        """Return a queryset of audit logs base on RBAC permissions."""
        if getattr(self, "swagger_fake_view", False):
            return AuditLog.objects.none()

        user = self.request.user

        if user_has_permission(user, PERMISSION_AUDIT_LOGS_VIEW_ALL):
            return AuditLog.objects.all().select_related("actor", "target_user")

        if user_has_permission(user, PERMISSION_AUDIT_LOGS_VIEW_OWN):
            actor_ids = AuditLog.objects.filter(actor=user).values("pk")
            target_ids = AuditLog.objects.filter(target_user=user).values("pk")

            allowed_log_ids = actor_ids.union(target_ids)

            return AuditLog.objects.filter(pk__in=allowed_log_ids).select_related(
                "actor", "target_user"
            )

        return AuditLog.objects.none()

    @action(
        detail=False,
        methods=["get"],
        throttle_classes=[ScopedRateThrottle],
    )
    def export(self, request):
        """Export the filtered audit logs as a downloadable CSV file."""
        max_export_limit = getattr(settings, "MAX_EXPORT_LIMIT", 10000)

        queryset = self.filter_queryset(self.get_queryset())[:max_export_limit]

        def generate_csv():
            writer = csv.writer(EchoBuffer())

            yield writer.writerow(
                [
                    "ID",
                    "Date/Time",
                    "Actor",
                    "Target User",
                    "Action Type",
                    "Result",
                    "IP Address",
                    "Description",
                ]
            )

            for log in queryset.iterator(chunk_size=2000):
                yield writer.writerow(
                    [
                        log.id,
                        log.created_at.strftime("%Y-%m-%d %H:%M:%S"),
                        log.actor.username if log.actor else "System",
                        log.target_user.username if log.target_user else "N/A",
                        log.action_type,
                        log.result,
                        log.ip_address or "N/A",
                        log.description,
                    ]
                )

        response = StreamingHttpResponse(generate_csv(), content_type="text/csv")
        response["Content-Disposition"] = 'attachment; filename="audit_logs.csv"'

        return response


@user_status_update_schema
class UserStatusUpdateView(APIView):
    """Handle activation and deactivation of user accounts by administrators."""

    permission_classes = [IsSystemAdmin]

    def patch(self, request, pk):
        """Update the active status of a specific user.

        Args:
            request (Request): The HTTP request containing 'is_active' and 'reason'.
            pk (int): The primary key of the target user.

        Returns:
            Response: The updated status or validation errors.
        """
        target_user = get_object_or_404(User, pk=pk)
        serializer = UserStatusUpdateSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        new_status = serializer.validated_data["is_active"]
        reason = serializer.validated_data.get("reason", "")
        previous_status = target_user.is_active

        if new_status == previous_status:
            status_str = "active" if new_status else "inactive"
            return Response(
                {"detail": f"User is already {status_str}."},
                status=status.HTTP_200_OK,
            )

        if not new_status and request.user.id == target_user.id:
            return Response(
                {"detail": "You cannot deactivate your own account."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        target_user.is_active = new_status
        target_user.save()

        UserStatusLog.objects.create(
            target_user=target_user,
            changed_by=request.user,
            old_status=previous_status,
            new_status=new_status,
            reason=reason,
        )

        action = (
            AuditLog.ActionType.ACCOUNT_ACTIVATED
            if new_status
            else AuditLog.ActionType.ACCOUNT_DEACTIVATED
        )

        create_audit_log(
            actor=request.user,
            action_type=action,
            result=AuditLog.ResultStatus.SUCCESS,
            target_user=target_user,
            description=f"Account status changed to "
            f"{'active' if new_status else 'inactive'}. Reason: {reason}",
            request=request,
        )

        return Response(
            {"detail": "User status updated successfully.", "is_active": new_status},
            status=status.HTTP_200_OK,
        )


@extend_schema_view(
    get=user_me_get_schema, put=user_me_update_schema, patch=user_me_update_schema
)
class UserMeView(generics.RetrieveUpdateAPIView):
    """Retrieve or update the currently authenticated user's profile."""

    serializer_class = UserMeSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        """Return the currently authenticated user."""
        return self.request.user

    def perform_update(self, serializer):
        """Save the updated user data and create an audit logs entry."""
        updated_user = serializer.save()

        create_audit_log(
            actor=self.request.user,
            action_type=AuditLog.ActionType.PROFILE_UPDATED,
            result=AuditLog.ResultStatus.SUCCESS,
            target_user=updated_user,
            description="User updated their basic profile information.",
            request=self.request,
        )


def invalidate_user_sessions(user):
    """Invalidate and delete all active sessions for a given user.
    Args:
        user (User): The user whose sessions should be terminated.
    """
    from django.contrib.sessions.models import Session
    from django.utils import timezone

    from .models import UserSession

    tracked = UserSession.objects.filter(user=user)
    session_keys = list(tracked.values_list("session_key", flat=True))

    if session_keys:
        Session.objects.filter(session_key__in=session_keys).delete()
        tracked.delete()
    else:
        # Fallback: scan sessions if UserSession tracking wasn't populated yet
        active_sessions = Session.objects.filter(expire_date__gte=timezone.now())
        user_pk_str = str(user.pk)

        keys_to_delete = []
        for session in active_sessions.iterator(chunk_size=500):
            data = session.get_decoded()
            if user_pk_str == str(data.get("_auth_user_id")):
                keys_to_delete.append(session.session_key)

        if keys_to_delete:
            Session.objects.filter(session_key__in=keys_to_delete).delete()


@change_password_schema
class ChangePasswordView(APIView):
    """Handle password change requests for the authenticated user."""

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        """Verify the old password and set a new password for the user."""
        serializer = ChangePasswordSerializer(
            data=request.data, context={"request": request}
        )

        if serializer.is_valid():
            user = request.user
            set_user_password(user, serializer.validated_data["new_password"])

            update_session_auth_hash(request, user)

            create_audit_log(
                actor=user,
                action_type=AuditLog.ActionType.PASSWORD_CHANGED,
                result=AuditLog.ResultStatus.SUCCESS,
                target_user=user,
                description="User successfully changed their password.",
                request=request,
            )

            return Response(
                {"detail": "Password has been successfully changed."},
                status=status.HTTP_200_OK,
            )

        create_audit_log(
            actor=request.user,
            action_type=AuditLog.ActionType.PASSWORD_CHANGED,
            result=AuditLog.ResultStatus.FAILED,
            target_user=request.user,
            description="Failed attempt to change password.",
            request=request,
        )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@password_reset_schema
class PasswordResetRequestView(APIView):
    """Handle requests to send password reset link via email."""

    permission_classes = [permissions.AllowAny]
    throttle_classes = [PasswordResetRequestThrottle]

    def post(self, request):
        """Generate and email a password reset token if the user exists."""
        serializer = PasswordResetRequestSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data["email"]
            try:
                user = User.objects.get(email__iexact=email)
            except User.DoesNotExist:
                user = None

            if user:
                uid = urlsafe_base64_encode(force_bytes(user.pk))
                token = default_token_generator.make_token(user)

                reset_link = f"{settings.FRONTEND_URL}/reset-password/{uid}/{token}/"

                send_email_task.delay(
                    subject="Password Reset Request",
                    message=f"You requested a password reset. "
                    f"Click the link below to reset your password:\n\n{reset_link}",
                    recipient_list=[user.email],
                )

                create_audit_log(
                    actor=None,
                    action_type=AuditLog.ActionType.PASSWORD_RESET_REQUESTED,
                    result=AuditLog.ResultStatus.SUCCESS,
                    target_user=user,
                    description="Password reset email sent.",
                    request=request,
                )

            return Response(
                {
                    "detail": "If an account with this email exists, "
                    "a password reset link has been sent."
                },
                status=status.HTTP_200_OK,
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@password_reset_confirm_schema
class PasswordResetConfirmView(APIView):
    """Handle password reset confirmations using a secure token."""

    permission_classes = [permissions.AllowAny]
    throttle_classes = [PasswordResetConfirmThrottle]

    def post(self, request, uidb64, token):
        """Verify the reset token and set a new password for the user.
        Args:
            request (Request): The HTTP request containing the new password.
            uidb64 (str): Base64 encoded user ID.
            token (str): The one-time password reset token.

        Returns:
            Response: A success message or an error for invalid/expired tokens.
        """

        try:
            uid = force_str(urlsafe_base64_decode(uidb64))
            user = User.objects.get(pk=uid)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            user = None

        if user is not None and default_token_generator.check_token(user, token):
            serializer = PasswordResetConfirmSerializer(data=request.data)
            if not serializer.is_valid():
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

            new_password = serializer.validated_data["new_password"]
            set_user_password(user, new_password)

            create_audit_log(
                actor=user,
                action_type=AuditLog.ActionType.PASSWORD_CHANGED,
                result=AuditLog.ResultStatus.SUCCESS,
                target_user=user,
                description="Password successfully reset via email link.",
                request=request,
            )

            send_email_task.delay(
                subject="Password Changed Successfully",
                message="Your password has been successfully updated. "
                "If you did not make this change, contact support immediately.",
                recipient_list=[user.email],
            )

            return Response(
                {"detail": "Password has been reset successfully."},
                status=status.HTTP_200_OK,
            )

        if user:
            create_audit_log(
                actor=None,
                action_type=AuditLog.ActionType.PASSWORD_CHANGED,
                result=AuditLog.ResultStatus.FAILED,
                target_user=user,
                description="Failed attempt to reset password (invalid/expired token).",
                request=request,
            )

        return Response(
            {"detail": "The reset link is invalid or has expired."},
            status=status.HTTP_400_BAD_REQUEST,
        )


class ProtectedProfilePictureView(APIView):
    """Serve profile picture securely."""

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, user_id):
        """Return the user's profile picture if the requester has permission.

        Args:
            request (Request): The incoming HTTP request.
            user_id (str): The ID of the user whose picture is requested.

        Returns:
            Response: The profile picture or an error message.
        """
        user = get_object_or_404(User, pk=user_id)

        if request.user != user and not request.user.is_staff:
            return Response(
                {"detail": "You do not have permission to view this profile picture."},
                status=status.HTTP_403_FORBIDDEN,
            )

        if not hasattr(user, "profile") or not user.profile.profile_picture:
            return Response(
                {"detail": "User does not have a profile picture."},
                status=status.HTTP_404_NOT_FOUND,
            )

        file_field = user.profile.profile_picture

        if not file_field or not file_field.storage.exists(file_field.name):
            raise Http404("File not found on server.")

        content_type, _ = mimetypes.guess_type(file_field.name)
        content_type = content_type or "application/octet-stream"
        filename = os.path.basename(file_field.name)

        if settings.DEBUG:
            return FileResponse(
                file_field,
                content_type=content_type,
                as_attachment=False,
                filename=filename,
            )
        else:
            response = HttpResponse(content_type=content_type)

            safe_name = posixpath.normpath(file_field.name)
            if safe_name.startswith("..") or safe_name.startswith("/"):
                raise Http404("Invalid file path.")

            internal_path = f"/internal-media/{safe_name}"
            response["X-Accel-Redirect"] = internal_path

            escaped_filename = escape_uri_path(filename)
            response["Content-Disposition"] = (
                f"inline; filename*=UTF-8''{escaped_filename}"
            )

            return response
