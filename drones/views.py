from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, generics

from common.pagination import StandardResultsSetPagination

from .filters import DroneFilter, WriteOffRecordFilter
from .models import Drone, DroneModel, WriteOffRecord
from .permissions import DronePermission, WriteOffHistoryPermission
from .serializers import (
    DroneListSerializer,
    DroneModelSerializer,
    DroneSerializer,
    DroneUpdateSerializer,
    WriteOffAuditSerializer,
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
    
    
class WriteOffHistoryListView(generics.ListAPIView):
    serializer_class = WriteOffAuditSerializer
    permission_classes = [WriteOffHistoryPermission]
    pagination_class = StandardResultsSetPagination
    filter_backends = (
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    )
    filterset_class = WriteOffRecordFilter
    search_fields = (
        "drone__name",
        "drone__serial_number",
        "drone__inventory_number",
        "reason",
        "reason_description",
        "document_number",
        "authorized_by__username",
    )
    ordering_fields = (
        "created_at",
        "written_off_at",
        "drone__serial_number",
        "drone__inventory_number",
        "document_number",
    )
    ordering = ("-created_at",)

    def get_queryset(self):
        queryset = (
            WriteOffRecord.objects
            .select_related("drone", "authorized_by", "related_mission")
            .order_by("-created_at")
        )

        drone_pk = self.kwargs.get("drone_pk")
        if drone_pk is not None:
            queryset = queryset.filter(drone_id=drone_pk)

        return queryset
