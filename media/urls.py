from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import ArtifactDetailView, ArtifactListCreateView, MediaAuditLogViewSet

app_name = "media"

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

_router = DefaultRouter()
_router.register("audit-logs", MediaAuditLogViewSet, basename="media-audit-log")
audit_urlpatterns = _router.urls
