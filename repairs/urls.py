from django.urls import path

from .views import (
    ComponentReplacementDetailView,
    ComponentReplacementExportView,
    ComponentReplacementListCreateView,
    DefectDetailView,
    DefectHistoryView,
    DefectListCreateView,
    DefectStatusUpdateView,
    DefectUIDetailView,
)

app_name = "repairs"

urlpatterns = [
    path("defects/", DefectListCreateView.as_view(), name="defect-create"),
    path("defects/<int:pk>/", DefectDetailView.as_view(), name="defect-detail"),
    path(
        "defects/<int:pk>/ui/",
        DefectUIDetailView.as_view(),
        name="defect-ui",
    ),
    path(
        "defects/<int:pk>/history/",
        DefectHistoryView.as_view(),
        name="defect-history",
    ),
    path(
        "defects/<int:pk>/update-status/",
        DefectStatusUpdateView.as_view(),
        name="defect-update-status",
    ),
    path(
        "replacements/",
        ComponentReplacementListCreateView.as_view(),
        name="replacement-list-create",
    ),
    path(
        "replacements/export/",
        ComponentReplacementExportView.as_view(),
        name="replacement-export",
    ),
    path(
        "replacements/<int:pk>/",
        ComponentReplacementDetailView.as_view(),
        name="replacement-detail",
    ),
]
