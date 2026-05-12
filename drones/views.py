from rest_framework import generics
from rest_framework.permissions import IsAdminUser

from .models import Drone
from .serializers import DroneSerializer


class DroneCreateView(generics.CreateAPIView):
    queryset = Drone.objects.all()
    serializer_class = DroneSerializer
    permission_classes = [IsAdminUser]
