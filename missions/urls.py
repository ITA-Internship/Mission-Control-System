from django.urls import include, path

from .views import (
    MissionAssignmentDetailView,
    MissionAssignmentListCreateView,
    MissionDetailView,
    MissionDroneConditionView,
    MissionListCreateView,
    MissionOutcomeView,
    MissionStatusUpdateView,
)

app_name = "missions"

urlpatterns = [
    path("", MissionListCreateView.as_view(), name="mission-list-create"),
    path("<int:pk>/", MissionDetailView.as_view(), name="mission-detail"),
    path(
        "<int:pk>/outcome/",
        MissionOutcomeView.as_view(),
        name="mission-outcome",
    ),
    path(
        "<int:pk>/status/",
        MissionStatusUpdateView.as_view(),
        name="mission-status-update",
    ),
    path(
        "<int:mission_pk>/assignments/",
        MissionAssignmentListCreateView.as_view(),
        name="mission-assignment-list-create",
    ),
    path(
        "<int:mission_pk>/assignments/<int:pk>/",
        MissionAssignmentDetailView.as_view(),
        name="mission-assignment-detail",
    ),
    path(
        "<int:pk>/assignments/<int:assignment_id>/condition/",
        MissionDroneConditionView.as_view(),
        name="mission-drone-condition",
    ),
    path(
        "<int:mission_pk>/artifacts/",
        include("media.urls"),
    ),
]
