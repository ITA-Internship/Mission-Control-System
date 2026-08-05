"""OpenAPI extensions for project-specific authentication classes."""

from drf_spectacular.extensions import (
    OpenApiAuthenticationExtension,
)


class RequiredPasswordChangeSessionAuthenticationScheme(
    OpenApiAuthenticationExtension,
):
    """Describe Django session-cookie authentication in OpenAPI."""

    target_class = (
        "common.authentication."
        "RequiredPasswordChangeSessionAuthentication"
    )
    name = "cookieAuth"
    priority = 1

    def get_security_definition(self, auto_schema):
        return {
            "type": "apiKey",
            "in": "cookie",
            "name": "sessionid",
        }


class RequiredPasswordChangeBasicAuthenticationScheme(
    OpenApiAuthenticationExtension,
):
    """Describe development-only HTTP Basic authentication."""

    target_class = (
        "common.authentication."
        "RequiredPasswordChangeBasicAuthentication"
    )
    name = "basicAuth"
    priority = 1

    def get_security_definition(self, auto_schema):
        return {
            "type": "http",
            "scheme": "basic",
        }