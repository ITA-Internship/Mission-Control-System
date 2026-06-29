import csv

from django.conf import settings
from django.contrib.auth.tokens import default_token_generator
from django.contrib.sessions.models import Session
from django.core.exceptions import ValidationError as DjangoValidationError
from django.core.mail import send_mail
from django.db.models import Q
from django.http import StreamingHttpResponse
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from django_filters import rest_framework as filters
from rest_framework import generics, permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView

from common.utils import EchoBuffer

from .models import AuditLog, User, UserStatusLog
from .permissions import HasRBACPermission, IsSystemAdmin, user_has_permission
from .rbac import (
    PERMISSION_AUDIT_LOGS_VIEW_ALL,
    PERMISSION_AUDIT_LOGS_VIEW_OWN,
    PERMISSION_USERS_CREATE,
    PERMISSION_USERS_MANAGE_ROLES,
)
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
from .services import create_audit_log, update_user_role


class UserRegistrationView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserRegistrationSerializer
    permission_classes = [HasRBACPermission]
    required_permission = PERMISSION_USERS_CREATE


class UserRoleUpdateAPIView(APIView):
    permission_classes = [HasRBACPermission]
    required_permission = PERMISSION_USERS_MANAGE_ROLES

    def patch(self, request, user_id):
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


class ActivateAccountAPIView(APIView):
    permission_classes = [AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "account_activation"

    def post(self, request, user_id, token):
        user = get_object_or_404(User, pk=user_id)

        if not default_token_generator.check_token(user, token):
            return Response(
                {"detail": "Invalid or expired activation link."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        new_password = request.data.get("password")
        if not new_password:
            return Response(
                {"password": ["This field is required."]},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user.set_password(new_password)
        user.must_change_password = False
        user.save(update_fields=["password", "must_change_password"])

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


class AuditLogPagination(PageNumberPagination):
    page_size = 50
    page_size_query_param = "page_size"
    max_page_size = 500


class AuditLogFilter(filters.FilterSet):
    start_date = filters.DateFilter(field_name="created_at", lookup_expr="gte")
    end_date = filters.DateFilter(field_name="created_at", lookup_expr="lte")

    class Meta:
        model = AuditLog
        fields = ["actor", "target_user", "action_type", "result"]


class AuditLogViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = AuditLogSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = AuditLogPagination
    filter_backends = [filters.DjangoFilterBackend]
    filterset_class = AuditLogFilter

    throttle_scope = "audit_export"

    def get_queryset(self):
        user = self.request.user
        if user_has_permission(user, PERMISSION_AUDIT_LOGS_VIEW_ALL):
            return AuditLog.objects.all().select_related("actor", "target_user")

        if user_has_permission(user, PERMISSION_AUDIT_LOGS_VIEW_OWN):
            return AuditLog.objects.filter(
                Q(actor=user) | Q(target_user=user)
            ).select_related("actor", "target_user")

        return AuditLog.objects.none()

    @action(
        detail=False,
        methods=["get"],
        throttle_classes=[ScopedRateThrottle],
    )
    def export(self, request):
        MAX_EXPORT_LIMIT = 10000

        queryset = self.filter_queryset(self.get_queryset())[:MAX_EXPORT_LIMIT]

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


class UserStatusUpdateView(APIView):
    permission_classes = [IsSystemAdmin]

    def patch(self, request, pk):
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

        if not new_status:
            invalidate_user_sessions(target_user)

        return Response(
            {"detail": "User status updated successfully.", "is_active": new_status},
            status=status.HTTP_200_OK,
        )


class UserMeView(generics.RetrieveUpdateAPIView):
    serializer_class = UserMeSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user

    def perform_update(self, serializer):
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
    active_sessions = Session.objects.filter(expire_date__gte=timezone.now())
    for session in active_sessions:
        data = session.get_decoded()
        if str(user.pk) == str(data.get("_auth_user_id")):
            session.delete()


class ChangePasswordView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = ChangePasswordSerializer(
            data=request.data, context={"request": request}
        )

        if serializer.is_valid():
            user = request.user
            user.set_password(serializer.validated_data["new_password"])
            user.must_change_password = False
            user.save(update_fields=["password", "must_change_password"])

            invalidate_user_sessions(user)

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


class PasswordResetRequestView(APIView):
    permission_classes = [permissions.AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "password_reset_request"

    def post(self, request):
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

                send_mail(
                    subject="Password Reset Request",
                    message=f"You requested a password reset. "
                    f"Click the link below to reset your password:\n\n{reset_link}",
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[user.email],
                    fail_silently=False,
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


class PasswordResetConfirmView(APIView):
    permission_classes = [permissions.AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "password_reset_confirm"

    def post(self, request, uidb64, token):

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
            user.set_password(new_password)
            user.must_change_password = False
            user.save(update_fields=["password", "must_change_password"])

            invalidate_user_sessions(user)

            create_audit_log(
                actor=user,
                action_type=AuditLog.ActionType.PASSWORD_CHANGED,
                result=AuditLog.ResultStatus.SUCCESS,
                target_user=user,
                description="Password successfully reset via email link.",
                request=request,
            )

            send_mail(
                subject="Password Changed Successfully",
                message="Your password has been successfully updated. "
                "If you did not make this change, contact support immediately.",
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                fail_silently=True,
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
