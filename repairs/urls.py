from django.urls import path

from .views import DefectDetailView, DefectListCreateView

app_name = "repairs"

urlpatterns = [
    path("defects/", DefectListCreateView.as_view(), name="defect-create"),
    path("defects/<int:pk>/", DefectDetailView.as_view(), name="defect-detail"),
]
