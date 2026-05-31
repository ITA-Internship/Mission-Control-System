import csv

from django.contrib.auth.tokens import default_token_generator
from django.contrib.sessions.models import Session
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db.models import Q
from django.http import StreamingHttpResponse
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django_filters import rest_framework as filters
from rest_framework import generics, permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView

from .models import AuditLog, User, UserStatusLog
from .permissions import HasRBACPermission, IsSystemAdmin
from .rbac import PERMISSION_USERS_CREATE, PERMISSION_USERS_MANAGE_ROLES
from .serializers import (
    AuditLogSerializer,
    ChangePasswordSerializer,
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
        user.save()

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


class Echo:
    def write(self, value):
        return value


class AuditLogViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = AuditLogSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = AuditLogPagination
    filter_backends = [filters.DjangoFilterBackend]
    filterset_class = AuditLogFilter

    throttle_scope = "audit_export"

    def get_queryset(self):
        user = self.request.user
        if user.is_staff or user.is_superuser:
            return AuditLog.objects.all().select_related("actor", "target_user")

        return AuditLog.objects.filter(
            Q(actor=user) | Q(target_user=user)
        ).select_related("actor", "target_user")

    @action(
        detail=False,
        methods=["get"],
        throttle_classes=[ScopedRateThrottle],
    )
    def export(self, request):
        MAX_EXPORT_LIMIT = 10000

        queryset = self.filter_queryset(self.get_queryset())[:MAX_EXPORT_LIMIT]

        def generate_csv():
            writer = csv.writer(Echo())

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
            self.invalidate_user_sessions(target_user)

        return Response(
            {"detail": "User status updated successfully.", "is_active": new_status},
            status=status.HTTP_200_OK,
        )

    def invalidate_user_sessions(self, user):
        active_sessions = Session.objects.filter(expire_date__gte=timezone.now())
        for session in active_sessions:
            data = session.get_decoded()
            if str(user.pk) == str(data.get("_auth_user_id")):
                session.delete()


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


class ChangePasswordView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = ChangePasswordSerializer(
            data=request.data, context={"request": request}
        )

        if serializer.is_valid():
            user = request.user
            user.set_password(serializer.validated_data["new_password"])
            user.save()

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
