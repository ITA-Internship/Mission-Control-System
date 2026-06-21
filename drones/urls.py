from django.urls import path

from .views import (
    DroneComparisonView,
    DroneDataExportView,
    DroneDataImportView,
    DroneDetailView,
    DroneListCreateView,
    DroneModelListCreateView,
    WriteOffHistoryListView,
    WriteOffHistoryReportView,
)

app_name = "drones"

urlpatterns = [
    path("", DroneListCreateView.as_view(), name="drone-create"),
    path(
        "write-offs/report/",
        WriteOffHistoryReportView.as_view(),
        name="writeoff-history-report",
    ),
    path(
        "write-offs/",
        WriteOffHistoryListView.as_view(),
        name="writeoff-history",
    ),
    path(
        "<int:drone_pk>/write-offs/report/",
        WriteOffHistoryReportView.as_view(),
        name="drone-writeoff-history-report",
    ),
    path(
        "<int:drone_pk>/write-offs/",
        WriteOffHistoryListView.as_view(),
        name="drone-writeoff-history",
    ),
    path("compare/", DroneComparisonView.as_view(), name="drone-compare"),
    path("models/", DroneModelListCreateView.as_view(), name="drone-model-create"),
    path("import/", DroneDataImportView.as_view(), name="drone-import"),
    path("export/", DroneDataExportView.as_view(), name="drone-export"),
    path("<int:pk>/", DroneDetailView.as_view(), name="drone-detail"),
]
