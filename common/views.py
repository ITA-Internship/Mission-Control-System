"""Infrastructure health-check endpoint."""

import logging

from django.core.cache import cache
from django.db import connection
from django.http import JsonResponse
from django.views.decorators.http import require_GET

logger = logging.getLogger(__name__)


@require_GET
def health_check(request):
    """Return the health status of core dependencies.

    Checks PostgreSQL and Redis (cache backend) connectivity.
    Returns HTTP 200 when all dependencies are reachable,
    HTTP 503 otherwise.
    """
    health = {"status": "healthy", "dependencies": {}}
    is_healthy = True

    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        health["dependencies"]["database"] = "ok"
    except Exception as exc:
        logger.warning("Health check: database unreachable — %s", exc)
        health["dependencies"]["database"] = "unavailable"
        is_healthy = False

    try:
        cache.set("_health_check", "ok", timeout=5)
        if cache.get("_health_check") == "ok":
            health["dependencies"]["cache"] = "ok"
        else:
            health["dependencies"]["cache"] = "unexpected_value"
            is_healthy = False
        cache.delete("_health_check")
    except Exception as exc:
        logger.warning("Health check: cache unreachable — %s", exc)
        health["dependencies"]["cache"] = "unavailable"
        is_healthy = False

    if not is_healthy:
        health["status"] = "unhealthy"
        return JsonResponse(health, status=503)

    return JsonResponse(health, status=200)
