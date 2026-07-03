from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from rest_framework.throttling import SimpleRateThrottle


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

    def get_cache_key(self, request, view):
        return self.cache_format % {
            "scope": self.scope,
            "ident": self.get_ident(request),
        }


class AccountActivationThrottle(_BaseIPThrottle):
    scope = "account_activation"


class PasswordResetRequestThrottle(_BaseIPThrottle):
    scope = "password_reset_request"


class PasswordResetConfirmThrottle(_BaseIPThrottle):
    scope = "password_reset_confirm"
