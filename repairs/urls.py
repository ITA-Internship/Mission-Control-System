from django.urls import path

from .views import (
    ComponentReplacementDetailView,
    ComponentReplacementListCreateView,
    DefectDetailView,
    DefectListCreateView,
)

app_name = "repairs"

urlpatterns = [
    path("defects/", DefectListCreateView.as_view(), name="defect-create"),
    path("defects/<int:pk>/", DefectDetailView.as_view(), name="defect-detail"),
    path(
        "replacements/",
        ComponentReplacementListCreateView.as_view(),
        name="replacement-list-create",
    ),
    path(
        "replacements/<int:pk>/",
        ComponentReplacementDetailView.as_view(),
        name="replacement-detail",
    ),
]
