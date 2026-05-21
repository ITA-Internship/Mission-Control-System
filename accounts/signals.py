from django.contrib.auth import get_user_model
from django.contrib.auth.signals import (
    user_logged_in,
    user_logged_out,
    user_login_failed,
)
from django.dispatch import receiver

from .models import AuditLog
from .services import create_audit_log

User = get_user_model()


@receiver(user_logged_in)
def log_user_login(sender, request, user, **kwargs):
    create_audit_log(
        actor=user,
        action_type=AuditLog.ActionType.LOGIN_SUCCESS,
        result=AuditLog.ResultStatus.SUCCESS,
        target_user=user,
        description="User logged in successfully",
        request=request,
    )


@receiver(user_login_failed)
def log_user_login_failed(sender, credentials, request, **kwargs):
    username = credentials.get("username", "Unknown")

    target_user = None
    if username and username != "Unknown":
        try:
            target_user = User.objects.filter(username__iexact=username).first()
        except Exception:
            pass

    create_audit_log(
        actor=None,
        action_type=AuditLog.ActionType.LOGIN_FAILED,
        result=AuditLog.ResultStatus.FAILED,
        target_user=target_user,
        description=f"Failed login attempt for username: {username}",
        request=request,
    )


@receiver(user_logged_out)
def log_user_logout(sender, request, user, **kwargs):
    create_audit_log(
        actor=user,
        action_type=AuditLog.ActionType.LOGOUT,
        result=AuditLog.ResultStatus.SUCCESS,
        target_user=user,
        description="User logged out successfully",
        request=request,
    )
