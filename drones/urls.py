from django.urls import path

from .views import DroneDetailView, DroneListCreateView, DroneModelListCreateView

app_name = "drones"

urlpatterns = [
    path("", DroneListCreateView.as_view(), name="drone-create"),
    path("<int:pk>/", DroneDetailView.as_view(), name="drone-detail"),
    path("models/", DroneModelListCreateView.as_view(), name="drone-model-create"),
]
