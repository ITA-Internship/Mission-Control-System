from django.urls import path

from .views import (
    MissionDetailView,
    MissionListCreateView,
    MissionAssignmentListCreateView,
    MissionAssignmentDetailView,
)

app_name = "missions"

urlpatterns = [
    path("", MissionListCreateView.as_view(), name="mission-list-create"),
    path("<int:pk>/", MissionDetailView.as_view(), name="mission-detail"),
    path("<int:id>/assignments/", MissionAssignmentListCreateView.as_view(), name="mission-assignment-list-create"),
    path("<int:id>/assignments/<int:assignment_id>/", MissionAssignmentDetailView.as_view(), name="mission-assignment-detail"),
]
