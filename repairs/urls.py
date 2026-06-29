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
    DroneRepairHistoryExportView,
    DroneRepairHistoryPageView,
    DroneRepairHistoryView,
    RepairOrderDetailView,
    RepairOrderListCreateView,
    RepairOrderReplacementView,
)

app_name = "repairs"

urlpatterns = [
    # Defects
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
    # Replacements
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
    # Repair Orders
    path(
        "orders/",
        RepairOrderListCreateView.as_view(),
        name="repair-order-list",
    ),
    path(
        "orders/<int:pk>/",
        RepairOrderDetailView.as_view(),
        name="repair-order-detail",
    ),
    path(
        "orders/<int:pk>/replacements/",
        RepairOrderReplacementView.as_view(),
        name="repair-order-replacement",
    ),
    # Drone History Timeline
    path(
        "drones/<int:drone_id>/history/",
        DroneRepairHistoryView.as_view(),
        name="drone-repair-history",
    ),
    path(
        "drones/<int:drone_id>/history/export/",
        DroneRepairHistoryExportView.as_view(),
        name="drone-repair-history-export",
    ),
    path(
        "drones/<int:drone_id>/history/view/",
        DroneRepairHistoryPageView.as_view(),
        name="drone-repair-history-page",
    ),
]
