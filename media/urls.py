from django.urls import path

from .views import ArtifactDetailView, ArtifactListCreateView

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
