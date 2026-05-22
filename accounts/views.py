from django.contrib.auth.tokens import default_token_generator
from django.contrib.sessions.models import Session
from django.core.exceptions import ValidationError as DjangoValidationError
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import generics, status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import User, UserStatusLog
from .permissions import HasRBACPermission, IsSystemAdmin
from .rbac import PERMISSION_USERS_CREATE, PERMISSION_USERS_MANAGE_ROLES
from .serializers import (
    UserRegistrationSerializer,
    UserRoleUpdateResponseSerializer,
    UserRoleUpdateSerializer,
    UserStatusUpdateSerializer,
)
from .services import update_user_role


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

        return Response(
            {"detail": "Your account has been activated. You can now log in."},
            status=status.HTTP_200_OK,
        )


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
