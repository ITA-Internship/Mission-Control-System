"""Project-wide request guards."""

from django.http import JsonResponse


class MustChangePasswordMiddleware:
    """Restrict authenticated API access until the password is changed."""

    allowed_view_names = {
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

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        return self.get_response(request)

    def process_view(self, request, view_func, view_args, view_kwargs):
        """Block protected API views for users with a required password change."""
        if not request.path_info.startswith("/api/"):
            return None

        user = getattr(request, "user", None)
        if not user or not user.is_authenticated:
            return None

        if not getattr(user, "must_change_password", False):
            return None

        view_name = getattr(request.resolver_match, "view_name", None)
        if view_name in self.allowed_view_names:
            return None

        if view_name == "accounts:user-me" and request.method in {
            "GET",
            "HEAD",
            "OPTIONS",
        }:
            return None

        return JsonResponse(
            {
                "detail": "Password change is required before accessing this resource.",
                "code": "password_change_required",
            },
            status=403,
        )
