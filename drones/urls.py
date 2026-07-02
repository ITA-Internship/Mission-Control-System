from django.urls import path

from .views import (
    DroneComparisonView,
    DroneDataExportView,
    DroneDataImportView,
    DroneDetailView,
    DroneListCreateView,
    DroneModelListCreateView,
    DroneSpecChangeLogListView,
    DroneStatusHistoryListView,
    WriteOffRecordListCreateView,
)

app_name = "drones"

urlpatterns = [
    path("", DroneListCreateView.as_view(), name="drone-create"),
    path("compare/", DroneComparisonView.as_view(), name="drone-compare"),
    path("<int:pk>/", DroneDetailView.as_view(), name="drone-detail"),
    path(
        "<int:pk>/history/",
        DroneStatusHistoryListView.as_view(),
        name="drone-status-history",
    ),
    path(
        "<int:pk>/spec-changes/",
        DroneSpecChangeLogListView.as_view(),
        name="drone-spec-changes",
    ),
    path("models/", DroneModelListCreateView.as_view(), name="drone-model-create"),
    path("import/", DroneDataImportView.as_view(), name="drone-import"),
    path("export/", DroneDataExportView.as_view(), name="drone-export"),
    path(
        "write-offs/", WriteOffRecordListCreateView.as_view(), name="write-off-create"
    ),
]
