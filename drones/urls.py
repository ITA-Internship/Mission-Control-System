from django.urls import path

from .views import (
    DroneDataExportView,
    DroneDataImportView,
    DroneDetailView,
    DroneListCreateView,
    DroneModelListCreateView
)

app_name = "drones"

urlpatterns = [
    path("", DroneListCreateView.as_view(), name="drone-create"),
    path("<int:pk>/", DroneDetailView.as_view(), name="drone-detail"),
    path("models/", DroneModelListCreateView.as_view(), name="drone-model-create"),
    path("import/", DroneDataImportView.as_view(), name="drone-import"),
    path("export/", DroneDataExportView.as_view(), name="drone-export"),
]
