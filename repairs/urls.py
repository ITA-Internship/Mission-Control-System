from django.urls import path

from .views import (
    DefectDetailView,
    DefectHistoryView,
    DefectListCreateView,
    DefectStatusUpdateView,
)

app_name = "repairs"

urlpatterns = [
    path("defects/", DefectListCreateView.as_view(), name="defect-create"),
    path("defects/<int:pk>/", DefectDetailView.as_view(), name="defect-detail"),
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
]
