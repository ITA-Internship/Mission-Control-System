from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, generics

from .filters import DroneFilter
from .models import Drone
from .pagination import StandardResultsSetPagination
from .permissions import DronePermission
from .serializers import DroneSerializer, DroneUpdateSerializer


class DroneListCreateView(generics.ListCreateAPIView):
    serializer_class = DroneSerializer
    permission_classes = [DronePermission]
    filter_backends = (
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    )
    filterset_class = DroneFilter
    pagination_class = StandardResultsSetPagination
    search_fields = ["serial_number", "inventory_number"]
    ordering_fields = ["created_at", "status", "name"]

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
