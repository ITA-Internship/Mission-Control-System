from django.urls import path
from .views import DroneCreateView

app_name = 'drones'

urlpatterns = [
    path("", DroneCreateView.as_view(), name="drone-create"),
]
