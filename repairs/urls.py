from django.urls import path

from .views import DefectDetailView, DefectListCreateView

app_name = "repairs"

urlpatterns = [
    path("", DefectListCreateView.as_view(), name="defect-create"),
    path("<int:pk>/", DefectDetailView.as_view(), name="defect-detail"),
]
