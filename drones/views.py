import csv

from django.conf import settings
from django.db.models import Max, Min
from django.http import (
    HttpResponse,
    HttpResponseBadRequest,
    HttpResponseForbidden,
    StreamingHttpResponse,
)
from django.views.generic import TemplateView
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, generics, status
from rest_framework.response import Response

from accounts.permissions import HasRBACPermission
from accounts.rbac import PERMISSION_SPECIFICATIONS_COMPARE
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


class DroneComparisonView(TemplateView):
    template_name = "drones/compare.html"

    MAX_COMPARE_COUNT = 5

    required_permission = PERMISSION_SPECIFICATIONS_COMPARE

    def dispatch(self, request, *args, **kwargs):
        permission_validator = HasRBACPermission()
        if not permission_validator.has_permission(request, self):
            return HttpResponseForbidden(
                "You do not have permission to access this tool."
            )

        return super().dispatch(request, *args, **kwargs)

    def _parse_drone_ids(self, ids_param):
        if not ids_param:
            return []
        try:
            return [int(x.strip()) for x in ids_param.split(",") if x.strip()]
        except ValueError:
            return []

    def get_drones_queryset(self, drone_ids):
        if not drone_ids:
            return Drone.objects.none()

        return (
            Drone.objects.select_related("military_unit", "spec")
            .filter(id__in=drone_ids)
            .order_by("id")
        )

    def get(self, request, *args, **kwargs):
        ids_param = request.GET.get("ids", "")
        drone_ids = self._parse_drone_ids(ids_param)

        if request.GET.get("export") == "csv":
            if len(drone_ids) > self.MAX_COMPARE_COUNT:
                return HttpResponseBadRequest(
                    "Export failed. You can compare and export a"
                    f" maximum of {self.MAX_COMPARE_COUNT} drones."
                )

            queryset = self.get_drones_queryset(drone_ids)
            if not queryset.exists():
                return HttpResponseBadRequest("No drones available for export.")
            return self.export_to_csv(queryset)

        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        ids_param = self.request.GET.get("ids", "")
        drone_ids = self._parse_drone_ids(ids_param)

        context["ids_param"] = ids_param
        context["drones"] = None
        context["error"] = None

        if len(drone_ids) > self.MAX_COMPARE_COUNT:
            context["error"] = (
                "Too many drones selected. You can compare a maximum "
                f"of {self.MAX_COMPARE_COUNT} drones at a time."
            )
            return context

        queryset = self.get_drones_queryset(drone_ids)
        context["drones"] = queryset

        if not queryset.exists() and ids_param:
            context["error"] = "Provided drone IDs are invalid or do not exist."
        elif not ids_param:
            context["error"] = (
                "Please provide drone IDs in the query parameters. Example: ?ids=1,2,3"
            )

        if queryset.count() > 1:
            metrics = queryset.aggregate(
                max_flight_time=Max("spec__max_flight_time_min"),
                min_flight_time=Min("spec__max_flight_time_min"),
                max_speed=Max("spec__max_speed_kmh"),
                min_speed=Min("spec__max_speed_kmh"),
                max_payload=Max("spec__payload_capacity_g"),
                min_payload=Min("spec__payload_capacity_g"),
            )

            context["max_flight_time"] = metrics["max_flight_time"] or 0
            context["min_flight_time"] = metrics["min_flight_time"] or 0
            context["max_speed"] = metrics["max_speed"] or 0
            context["min_speed"] = metrics["min_speed"] or 0
            context["max_payload"] = metrics["max_payload"] or 0
            context["min_payload"] = metrics["min_payload"] or 0
        else:
            context["max_flight_time"] = context["max_speed"] = context[
                "max_payload"
            ] = 0
            context["min_flight_time"] = context["min_speed"] = context[
                "min_payload"
            ] = 0

        return context

    def export_to_csv(self, queryset):
        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = 'attachment; filename="drone_comparison.csv"'
        writer = csv.writer(response)

        writer.writerow(
            [
                "ID",
                "Name",
                "Model",
                "Classification",
                "Status",
                "Firmware Version",
                "Max Speed (km/h)",
                "Max Flight Time (min)",
                "Payload Capacity (g)",
            ]
        )

        for drone in queryset:
            spec = getattr(drone, "spec", None)

            fw = getattr(spec, "firmware_version", None) if spec else None
            speed = getattr(spec, "max_speed_kmh", None) if spec else None
            time = getattr(spec, "max_flight_time_min", None) if spec else None
            payload = getattr(spec, "payload_capacity_g", None) if spec else None

            writer.writerow(
                [
                    drone.id,
                    drone.name,
                    drone.drone_model,
                    drone.classification,
                    drone.status,
                    fw if fw is not None else "N/A",
                    speed if speed is not None else "N/A",
                    time if time is not None else "N/A",
                    payload if payload is not None else "N/A",
                ]
            )

        return response


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
