from django.urls import path

from .views import DroneCreateView, DroneDetailView

app_name = "drones"

urlpatterns = [
    path("", DroneCreateView.as_view(), name="drone-create"),
    path("<int:pk>/", DroneDetailView.as_view(), name="drone-detail"),
]
