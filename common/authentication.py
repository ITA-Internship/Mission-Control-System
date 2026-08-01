"""DRF authentication policies shared across API applications."""

from rest_framework.authentication import BasicAuthentication, SessionAuthentication
from rest_framework.exceptions import PermissionDenied

PASSWORD_CHANGE_ALLOWED_VIEW_NAMES = {
    "accounts:account-activate",
    "accounts:change-password",
    "accounts:login",
    "accounts:logout",
    "accounts:password-reset-confirm",
    "accounts:password-reset-request",
    "health-check",
    "redoc",
    "schema",
    "swagger-ui",
}


def enforce_required_password_change(request, user):
    """Restrict authenticated API access until a required password is changed."""
    if not getattr(user, "must_change_password", False):
        return

    resolver_match = getattr(request, "resolver_match", None)
    view_name = getattr(resolver_match, "view_name", None)

    if view_name in PASSWORD_CHANGE_ALLOWED_VIEW_NAMES:
        return

    if view_name == "accounts:user-me" and request.method in {
        "GET",
        "HEAD",
        "OPTIONS",
    }:
        return

    raise PermissionDenied(
        detail={
            "detail": "Password change is required before accessing this resource.",
            "code": "password_change_required",
        }
    )


class RequiredPasswordChangeAuthenticationMixin:
    """Apply the password-change policy after an authenticator resolves a user."""

    def authenticate(self, request):
        result = super().authenticate(request)
        if result is not None:
            user, _ = result
            enforce_required_password_change(request, user)
        return result


class RequiredPasswordChangeSessionAuthentication(
    RequiredPasswordChangeAuthenticationMixin,
    SessionAuthentication,
):
    """Session authentication with mandatory password-change enforcement."""


class RequiredPasswordChangeBasicAuthentication(
    RequiredPasswordChangeAuthenticationMixin,
    BasicAuthentication,
):
    """Development Basic authentication with password-change enforcement."""
