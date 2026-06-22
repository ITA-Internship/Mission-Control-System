from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import (
    ArtifactDetailView,
    ArtifactListCreateView,
    MediaAuditLogViewSet,
)

app_name = "media"

# Per-mission artifact endpoints, mounted by missions under
# /api/missions/<mission_pk>/artifacts/
urlpatterns = [
    path(
        "",
        ArtifactListCreateView.as_view(),
        name="artifact-list-create",
    ),
    path(
        "<int:artifact_pk>/",
        ArtifactDetailView.as_view(),
        name="artifact-detail",
    ),
]

# Global media endpoints, mounted in config under /api/media/
_router = DefaultRouter()
_router.register("audit-logs", MediaAuditLogViewSet, basename="media-audit-log")
audit_urlpatterns = _router.urls
