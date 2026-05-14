from rest_framework import generics

from accounts.permissions import IsSystemAdmin

from .models import Drone
from .serializers import DroneSerializer


class DroneCreateView(generics.CreateAPIView):
    queryset = Drone.objects.all()
    serializer_class = DroneSerializer
    permission_classes = [IsSystemAdmin]
