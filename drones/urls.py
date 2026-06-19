from django.urls import path

from .views import DroneDetailView, DroneListCreateView, DroneModelListCreateView, WriteOffHistoryListView

app_name = "drones"

urlpatterns = [
    path("", DroneListCreateView.as_view(), name="drone-create"),
    path("write-offs/", WriteOffHistoryListView.as_view(), name="writeoff-history"),
    path("<int:drone_pk>/write-offs/", WriteOffHistoryListView.as_view(), name="drone-writeoff-history"),
    path("<int:pk>/", DroneDetailView.as_view(), name="drone-detail"),
    path("models/", DroneModelListCreateView.as_view(), name="drone-model-create"),
]
