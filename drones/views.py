from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, generics

from common.pagination import StandardResultsSetPagination

from .filters import DroneFilter
from .models import Drone, DroneModel, WriteOffRecord
from .permissions import DronePermission, WriteOffPermission
from .serializers import (
    DroneListSerializer,
    DroneModelSerializer,
    DroneSerializer,
    DroneUpdateSerializer,
    WriteOffRecordCreateSerializer,
    WriteOffRecordSerializer,
)


class DroneListCreateView(generics.ListCreateAPIView):
    serializer_class = DroneSerializer
    permission_classes = [DronePermission]
    filter_backends = (
        DjangoFilterBackend,
        filters.OrderingFilter,
    )
    filterset_class = DroneFilter
    pagination_class = StandardResultsSetPagination
    ordering_fields = ["created_at", "status", "name", "classification"]

    def get_queryset(self):
        return (
            Drone.objects.select_related("military_unit", "spec")
            .prefetch_related("status_history")
            .order_by("id")
        )

    def get_serializer_class(self):
        if self.request.method == "GET":
            return DroneListSerializer

        return self.serializer_class


class DroneDetailView(generics.RetrieveUpdateAPIView):
    queryset = (
        Drone.objects.select_related("military_unit", "spec")
        .prefetch_related("status_history")
        .all()
    )
    permission_classes = [DronePermission]
    http_method_names = ["get", "patch", "head", "options"]

    def get_serializer_class(self):
        if self.request.method == "PATCH":
            return DroneUpdateSerializer

        return DroneSerializer


class DroneModelListCreateView(generics.ListCreateAPIView):
    serializer_class = DroneModelSerializer
    permission_classes = [DronePermission]
    queryset = DroneModel.objects.all()


class WriteOffRecordListCreateView(generics.ListCreateAPIView):
    permission_classes = [WriteOffPermission]

    def get_queryset(self):
        return WriteOffRecord.objects.select_related(
            "drone",
            "authorized_by",
            "related_mission",
        ).order_by("-written_off_at")

    def get_serializer_class(self):
        if self.request.method == "POST":
            return WriteOffRecordCreateSerializer
        return WriteOffRecordSerializer
