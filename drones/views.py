from rest_framework import generics
from .models import Drone
from .serializers import DroneSerializer
from rest_framework.permissions import IsAdminUser


class DroneCreateView(generics.CreateAPIView):
    queryset = Drone.objects.all()
    serializer_class = DroneSerializer
    permission_classes = [IsAdminUser]