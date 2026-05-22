from django.urls import path

from .views import MissionDetailView, MissionListCreateView, MissionStatusUpdateView

app_name = "missions"

urlpatterns = [
    path("", MissionListCreateView.as_view(), name="mission-list-create"),
    path("<int:pk>/", MissionDetailView.as_view(), name="mission-detail"),
    path(
        "<int:pk>/status/",
        MissionStatusUpdateView.as_view(),
        name="mission-status-update",
    ),
]
