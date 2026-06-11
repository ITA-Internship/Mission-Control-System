from django.urls import path

from .views import DroneComparisonView, DroneDetailView, DroneListCreateView

app_name = "drones"

urlpatterns = [
    path("", DroneListCreateView.as_view(), name="drone-create"),
    path("compare/", DroneComparisonView.as_view(), name="drone-compare"),
    path("<int:pk>/", DroneDetailView.as_view(), name="drone-detail"),
]
