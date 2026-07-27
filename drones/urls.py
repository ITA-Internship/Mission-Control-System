"""Route drone inventory, comparison, import/export, and write-off endpoints."""

from django.urls import path

from .views import (
    DroneComparisonView,
    DroneDataExportView,
    DroneDataImportView,
    DroneDetailView,
    DroneListCreateView,
    DroneModelListCreateView,
    DroneScopedWriteOffHistoryListView,
    DroneSpecChangeLogListView,
    DroneStatusHistoryListView,
    WriteOffHistoryListView,
    WriteOffHistoryReportView,
    WriteOffRecordListCreateView,
)

app_name = "drones"

urlpatterns = [
    path("", DroneListCreateView.as_view(), name="drone-create"),
    path(
        "write-offs/",
        WriteOffRecordListCreateView.as_view(),
        name="write-off-create",
    ),
    path(
        "write-offs/history/",
        WriteOffHistoryListView.as_view(),
        name="writeoff-history",
    ),
    path(
        "write-offs/history/report/",
        WriteOffHistoryReportView.as_view(),
        name="writeoff-history-report",
    ),
    path(
        "<int:drone_pk>/write-offs/history/",
        DroneScopedWriteOffHistoryListView.as_view(),
        name="drone-writeoff-history",
    ),
    path(
        "<int:drone_pk>/write-offs/history/report/",
        WriteOffHistoryReportView.as_view(),
        name="drone-writeoff-history-report",
    ),
    path("compare/", DroneComparisonView.as_view(), name="drone-compare"),
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
    path("<int:pk>/", DroneDetailView.as_view(), name="drone-detail"),
]
