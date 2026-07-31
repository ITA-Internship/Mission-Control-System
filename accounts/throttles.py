"""Custom rate throttling classes for authentication and security endpoints.

Provides IP-based and user-based request throttling to protect sensitive
actions (like password resets and account activations) from brute-force
and spam attacks.
"""

import hashlib

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from rest_framework.throttling import SimpleRateThrottle


def _hash_cache_part(value):
    """Return an SHA-256 hash of the given value for safe cache key generation."""
    return hashlib.sha256(str(value).encode("utf-8")).hexdigest()


class _BaseIPThrottle(SimpleRateThrottle):
    """Base throttle class that falls back to IP address for unauthenticated users."""

    def get_rate(self):
        """Retrieve the throttle rate from settings.

        Raises:
            ImproperlyConfigured: If the throttle rate for the given scope is missing.
        """
        rest_framework_settings = getattr(settings, "REST_FRAMEWORK", {})
        throttle_rates = rest_framework_settings.get("DEFAULT_THROTTLE_RATES", {})
        rate = throttle_rates.get(self.scope)
        if rate is None:
            raise ImproperlyConfigured(
                f"Missing throttle rate for scope '{self.scope}'."
            )
        return rate

    def get_throttle_ident(self, request, view):
        """Return the user ID if authenticated, otherwise the client IP address."""
        user = getattr(request, "user", None)
        if user and user.is_authenticated:
            return f"user:{user.pk}"
        return f"ip:{self.get_ident(request)}"

    def get_cache_key(self, request, view):
        """Return the formatted cache key using the scope and identifier."""
        return self.cache_format % {
            "scope": self.scope,
            "ident": self.get_throttle_ident(request, view),
        }


class AccountActivationThrottle(_BaseIPThrottle):
    """Throttle limits for the account activation endpoint to prevent spam."""

    scope = "account_activation"

    def get_throttle_ident(self, request, view):
        """Append the hashed target user ID to the base identifier."""
        ident = super().get_throttle_ident(request, view)
        user_id = getattr(view, "kwargs", {}).get("user_id")
        if user_id is None:
            return ident
        return f"{ident}:target_user:{_hash_cache_part(user_id)}"


class PasswordResetRequestThrottle(_BaseIPThrottle):
    """Throttle limits for password reset requests to prevent email spam."""

    scope = "password_reset_request"

    def get_throttle_ident(self, request, view):
        """Append the hashed target email to the base identifier."""
        ident = super().get_throttle_ident(request, view)
        email = getattr(request, "data", {}).get("email", "")
        email = email.strip().lower()
        if not email:
            return ident
        return f"{ident}:email:{_hash_cache_part(email)}"


class PasswordResetConfirmThrottle(_BaseIPThrottle):
    """Throttle limits for password reset confirmations."""

    scope = "password_reset_confirm"

    def get_throttle_ident(self, request, view):
        """Append the hashed uidb64 to the base identifier."""
        ident = super().get_throttle_ident(request, view)
        uidb64 = getattr(view, "kwargs", {}).get("uidb64")
        if uidb64 is None:
            return ident
        return f"{ident}:uid:{_hash_cache_part(uidb64)}"


class LoginThrottle(_BaseIPThrottle):
    """Throttle limits for session login attempts."""

    scope = "login"

    def get_throttle_ident(self, request, view):
        """Append the hashed identifier to the base identifier when present."""
        ident = super().get_throttle_ident(request, view)
        identifier = getattr(request, "data", {}).get("identifier", "")
        identifier = identifier.strip().lower()
        if not identifier:
            return ident
        return f"{ident}:identifier:{_hash_cache_part(identifier)}"
