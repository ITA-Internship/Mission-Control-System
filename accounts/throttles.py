import hashlib

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from rest_framework.throttling import SimpleRateThrottle


def _hash_cache_part(value):
    return hashlib.sha256(str(value).encode("utf-8")).hexdigest()


class _BaseIPThrottle(SimpleRateThrottle):
    def get_rate(self):
        rest_framework_settings = getattr(settings, "REST_FRAMEWORK", {})
        throttle_rates = rest_framework_settings.get("DEFAULT_THROTTLE_RATES", {})
        rate = throttle_rates.get(self.scope)
        if rate is None:
            raise ImproperlyConfigured(
                f"Missing throttle rate for scope '{self.scope}'."
            )
        return rate

    def get_throttle_ident(self, request, view):
        user = getattr(request, "user", None)
        if user and user.is_authenticated:
            return f"user:{user.pk}"
        return f"ip:{self.get_ident(request)}"

    def get_cache_key(self, request, view):
        return self.cache_format % {
            "scope": self.scope,
            "ident": self.get_throttle_ident(request, view),
        }


class AccountActivationThrottle(_BaseIPThrottle):
    scope = "account_activation"

    def get_throttle_ident(self, request, view):
        ident = super().get_throttle_ident(request, view)
        user_id = getattr(view, "kwargs", {}).get("user_id")
        if user_id is None:
            return ident
        return f"{ident}:target_user:{_hash_cache_part(user_id)}"


class PasswordResetRequestThrottle(_BaseIPThrottle):
    scope = "password_reset_request"

    def get_throttle_ident(self, request, view):
        ident = super().get_throttle_ident(request, view)
        email = getattr(request, "data", {}).get("email", "")
        email = email.strip().lower()
        if not email:
            return ident
        return f"{ident}:email:{_hash_cache_part(email)}"


class PasswordResetConfirmThrottle(_BaseIPThrottle):
    scope = "password_reset_confirm"

    def get_throttle_ident(self, request, view):
        ident = super().get_throttle_ident(request, view)
        uidb64 = getattr(view, "kwargs", {}).get("uidb64")
        if uidb64 is None:
            return ident
        return f"{ident}:uid:{_hash_cache_part(uidb64)}"
