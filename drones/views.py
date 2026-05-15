from rest_framework import generics

from accounts.permissions import HasRBACPermission
from accounts.rbac import PERMISSION_DRONES_CREATE

from .models import Drone
from .serializers import DroneSerializer


class DroneCreateView(generics.CreateAPIView):
    queryset = Drone.objects.all()
    serializer_class = DroneSerializer
    permission_classes = [HasRBACPermission]
    required_permission = PERMISSION_DRONES_CREATE
