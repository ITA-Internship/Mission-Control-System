"""Helpers for extracting trustworthy information from incoming HTTP requests."""

from django.conf import settings


def get_client_ip(request) -> str | None:
    """Resolve the real client IP address from the request.

    Trusts only the rightmost ``settings.TRUSTED_PROXY_COUNT`` entries of the
    ``X-Forwarded-For`` header. Each trusted proxy appends the IP of whoever
    connected to it, so after N trusted hops the real client sits at
    ``ips[-N]``. Everything to the left of that is client-controlled and must
    not be trusted. Falls back to ``REMOTE_ADDR`` whenever the request is
    missing, the header is absent, no proxy is trusted, or the header has
    fewer than N entries.

    Args:
        request (HttpRequest): The incoming HTTP request. May be None.

    Returns:
        str | None: The resolved client IP address, or None if it can't be
            determined at all.
    """
    if request is None:
        return None

    trusted_proxy_count = getattr(settings, "TRUSTED_PROXY_COUNT", 0)
    remote_addr = request.META.get("REMOTE_ADDR")

    if trusted_proxy_count <= 0:
        return remote_addr

    x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if not x_forwarded_for:
        return remote_addr

    ips = [ip.strip() for ip in x_forwarded_for.split(",") if ip.strip()]

    if len(ips) < trusted_proxy_count:
        return remote_addr

    return ips[-trusted_proxy_count]
