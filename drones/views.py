from rest_framework import generics

from .models import Drone
from .permissions import DronePermission
from .serializers import DroneSerializer, DroneUpdateSerializer


class DroneCreateView(generics.ListCreateAPIView):
    serializer_class = DroneSerializer
    permission_classes = [DronePermission]

    def get_queryset(self):
        return (
            Drone.objects.select_related("military_unit")
            .prefetch_related("status_history")
            .exclude(status__in=Drone.INACTIVE_STATUSES)
            .order_by("id")
        )
        
        
class DroneDetailView(generics.RetrieveUpdateAPIView):
    queryset = (
        Drone.objects.select_related("military_unit")
        .prefetch_related("status_history")
        .all()
    )
    permission_classes = [DronePermission]
    http_method_names = ["get", "patch", "head", "options"]

    def get_serializer_class(self):
        if self.request.method == "PATCH":
            return DroneUpdateSerializer

        return DroneSerializer
