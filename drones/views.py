from rest_framework import generics
from .models import Drone
from .serializers import DroneSerializer


class DroneCreateView(generics.CreateAPIView):
    queryset = Drone.objects.all()
    serializer_class = DroneSerializer