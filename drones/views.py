from django.conf import settings
from django.http import StreamingHttpResponse
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, generics, status
from rest_framework.response import Response

from common.pagination import StandardResultsSetPagination

from .filters import DroneFilter
from .models import Drone, DroneModel
from .permissions import DronePermission
from .serializers import (
    DroneImportSerializer,
    DroneListSerializer,
    DroneModelSerializer,
    DroneSerializer,
    DroneUpdateSerializer,
)
from .services import generate_drones_csv, import_drones_csv


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


class DroneDataExportView(generics.ListAPIView):
    permission_classes = [DronePermission]

    filter_backends = (
        DjangoFilterBackend,
        filters.OrderingFilter,
    )

    filterset_class = DroneFilter
    ordering_fields = ["created_at", "status", "name", "classification"]

    pagination_class = None

    MAX_EXPORT_LIMIT = getattr(settings, "MAX_EXPORT_LIMIT", 10000)

    def get_queryset(self):
        return Drone.objects.select_related("military_unit").order_by("id")

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())

        limited_queryset = queryset[: self.MAX_EXPORT_LIMIT]

        response = StreamingHttpResponse(
            generate_drones_csv(limited_queryset), content_type="text/csv"
        )

        response["Content-Disposition"] = 'attachment; filename="drones_export.csv"'

        return response


class DroneDataImportView(generics.GenericAPIView):
    permission_classes = [DronePermission]
    serializer_class = DroneImportSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        uploaded_file = serializer.validated_data["file"]

        import_result = import_drones_csv(uploaded_file, request.user)

        if not import_result.get("success"):
            return Response(
                {"error": import_result.get("error")},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(
            {
                "message": "Import processing completed.",
                "added_count": import_result.get("added_count"),
                "errors": import_result.get("errors"),
            },
            status=status.HTTP_200_OK,
        )
