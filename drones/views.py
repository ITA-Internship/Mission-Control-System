"""Expose drone inventory, comparison, import/export, and write-off endpoints.

Classes:
    DroneComparisonView: Render and export side-by-side drone comparisons.
    DroneListCreateView: List active drones and create drones with specifications.
    DroneDetailView: Retrieve and partially update drone records.
    DroneModelListCreateView: List and create drone model catalog entries.
    WriteOffHistoryListView: Expose read-only write-off audit records.
    WriteOffHistoryReportView: Render write-off audit history as an HTML report.
    DroneDataExportView: Stream filtered drone inventory as CSV.
    DroneDataImportView: Import drone inventory records from CSV.
    WriteOffRecordListCreateView: List or create write-off records.
"""

import csv

from django.conf import settings
from django.core.exceptions import PermissionDenied
from django.db.models import Max, Min
from django.http import (
    HttpResponse,
    HttpResponseBadRequest,
    HttpResponseForbidden,
    StreamingHttpResponse,
)
from django.shortcuts import get_object_or_404
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from django.views.generic import ListView, TemplateView
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema_view
from rest_framework import filters, generics, status
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle

from accounts.permissions import HasRBACPermission
from accounts.rbac import PERMISSION_SPECIFICATIONS_COMPARE
from common.pagination import StandardResultsSetPagination

from .api_details import (
    drone_data_export_schema,
    drone_data_import_schema,
    drone_detail_get_schema,
    drone_detail_patch_schema,
    drone_get_schema,
    drone_model_get_schema,
    drone_model_post_schema,
    drone_post_schema,
)
from .filters import DroneFilter, WriteOffRecordFilter
from .models import (
    Drone,
    DroneModel,
    DroneSpecChangeLog,
    DroneStatusHistory,
    WriteOffRecord,
)
from .permissions import DronePermission, WriteOffHistoryPermission, WriteOffPermission
from .serializers import (
    DroneImportSerializer,
    DroneListSerializer,
    DroneModelSerializer,
    DroneSerializer,
    DroneSpecChangeLogSerializer,
    DroneStatusHistorySerializer,
    DroneUpdateSerializer,
    WriteOffAuditSerializer,
    WriteOffRecordCreateSerializer,
    WriteOffRecordSerializer,
)
from .services import generate_drones_csv, import_drones_csv


class DroneComparisonView(TemplateView):
    """Render and export a side-by-side comparison of selected drones.

    Access is protected by the specifications comparison RBAC permission. The
    selected drone count is capped so the comparison table and CSV export remain
    manageable.
    """

    template_name = "drones/compare.html"

    MAX_COMPARE_COUNT = 5

    required_permission = PERMISSION_SPECIFICATIONS_COMPARE

    def dispatch(self, request, *args, **kwargs):
        """Override dispatch to reject users without comparison permission."""
        permission_validator = HasRBACPermission()
        if not permission_validator.has_permission(request, self):
            return HttpResponseForbidden(
                "You do not have permission to access this tool."
            )

        return super().dispatch(request, *args, **kwargs)

    def _parse_drone_ids(self, ids_param):
        """Parse a comma-separated query parameter into integer drone IDs."""
        if not ids_param:
            return []
        try:
            return [int(x.strip()) for x in ids_param.split(",") if x.strip()]
        except ValueError:
            return []

    def get_drones_queryset(self, drone_ids):
        """Return selected drones with related objects needed for comparison."""
        if not drone_ids:
            return Drone.objects.none()

        return (
            Drone.objects.select_related("military_unit", "spec")
            .filter(id__in=drone_ids)
            .order_by("id")
        )

    def get(self, request, *args, **kwargs):
        """Render the comparison page or export selected drones as CSV."""
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
        """Build comparison context and aggregate metrics for selected drones."""
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
        """Return a CSV response for the selected comparison drones."""
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


@extend_schema_view(get=drone_get_schema, post=drone_post_schema)
class DroneListCreateView(generics.ListCreateAPIView):
    """List drone inventory records and create drones with nested specifications."""

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
        """Return drones with related data needed by list and create responses."""
        return Drone.objects.select_related(
            "military_unit", "spec", "drone_model"
        ).order_by("id")

    def get_serializer_class(self):
        """
        Use the compact serializer for list requests and the full serializer
        otherwise."""
        if self.request.method == "GET":
            return DroneListSerializer

        return self.serializer_class


@extend_schema_view(get=drone_detail_get_schema, patch=drone_detail_patch_schema)
class DroneDetailView(generics.RetrieveUpdateAPIView):
    """Retrieve drone details and apply partial updates or lifecycle transitions."""

    permission_classes = [DronePermission]
    http_method_names = ["get", "patch", "head", "options"]

    queryset = Drone.objects.select_related(
        "military_unit", "drone_model", "spec"
    ).all()

    def get_serializer_class(self):
        """Use the update serializer for PATCH requests."""
        if self.request.method == "PATCH":
            return DroneUpdateSerializer

        return DroneSerializer


class DroneStatusHistoryPagination(StandardResultsSetPagination):
    page_size = 50
    max_page_size = 200


class DroneStatusHistoryListView(generics.ListAPIView):
    serializer_class = DroneStatusHistorySerializer
    permission_classes = [DronePermission]
    pagination_class = DroneStatusHistoryPagination

    def get_queryset(self):
        get_object_or_404(Drone, pk=self.kwargs["pk"])
        return (
            DroneStatusHistory.objects.filter(drone_id=self.kwargs["pk"])
            .select_related("changed_by")
            .order_by("-created_at")
        )


class DroneSpecChangeLogPagination(StandardResultsSetPagination):
    page_size = 20
    max_page_size = 100


class DroneSpecChangeLogListView(generics.ListAPIView):
    serializer_class = DroneSpecChangeLogSerializer
    permission_classes = [DronePermission]
    pagination_class = DroneSpecChangeLogPagination

    def get_queryset(self):
        get_object_or_404(Drone, pk=self.kwargs["pk"])
        return (
            DroneSpecChangeLog.objects.filter(drone_spec__drone_id=self.kwargs["pk"])
            .select_related("changed_by")
            .order_by("-created_at")
        )


@extend_schema_view(get=drone_model_get_schema, post=drone_model_post_schema)
class DroneModelListCreateView(generics.ListCreateAPIView):
    """List and create drone model catalog entries."""

    serializer_class = DroneModelSerializer
    permission_classes = [DronePermission]
    queryset = DroneModel.objects.all()
    pagination_class = StandardResultsSetPagination

    @method_decorator(cache_page(60 * 5))
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)


class WriteOffHistoryListView(generics.ListAPIView):
    """Expose read-only write-off audit records.

    The endpoint can return all write-off records or records scoped to a selected
    drone when the URL contains a drone primary key.
    """

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
        """Return write-off records filtered to a selected drone when provided."""
        queryset = WriteOffRecord.objects.select_related(
            "drone", "authorized_by", "related_mission"
        ).order_by("-created_at")

        drone_pk = self.kwargs.get("drone_pk")
        if drone_pk is not None:
            queryset = queryset.filter(drone_id=drone_pk)

        return queryset


class WriteOffHistoryReportView(ListView):
    """Render an HTML report of write-off audit records."""

    model = WriteOffRecord
    template_name = "drones/writeoff_history_report.html"
    context_object_name = "writeoff_records"
    paginate_by = 50

    def dispatch(self, request, *args, **kwargs):
        """Override dispatch to protect the report with write-off history permission."""
        permission = WriteOffHistoryPermission()

        if not permission._has_permission(request.user):
            raise PermissionDenied(permission.message)

        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        """Return filtered write-off records for the report page."""
        queryset = WriteOffRecord.objects.select_related(
            "drone",
            "authorized_by",
            "related_mission",
        ).order_by("-created_at")

        drone_pk = self.kwargs.get("drone_pk")
        if drone_pk is not None:
            queryset = queryset.filter(drone_id=drone_pk)

        self.filterset = WriteOffRecordFilter(
            self.request.GET,
            queryset=queryset,
        )

        return self.filterset.qs

    def get_context_data(self, **kwargs):
        """Add filter query state and selected drone context to the report."""
        context = super().get_context_data(**kwargs)

        query_params = self.request.GET.copy()
        query_params.pop("page", None)

        context["querystring"] = query_params.urlencode()
        context["drone_pk"] = self.kwargs.get("drone_pk")

        return context


@drone_data_export_schema
class DroneDataExportView(generics.ListAPIView):
    """Stream a filtered drone inventory export as CSV."""

    permission_classes = [DronePermission]

    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "drone_export"

    filter_backends = (
        DjangoFilterBackend,
        filters.OrderingFilter,
    )

    filterset_class = DroneFilter
    ordering_fields = ["created_at", "status", "name", "classification"]

    pagination_class = None

    MAX_EXPORT_LIMIT = getattr(settings, "MAX_EXPORT_LIMIT", 10000)

    def get_queryset(self):
        """Return drones ordered for CSV export."""
        return Drone.objects.select_related("military_unit").order_by("id")

    def list(self, request, *args, **kwargs):
        """Stream the filtered queryset while respecting the configured export limit."""
        queryset = self.filter_queryset(self.get_queryset())

        limited_queryset = queryset[: self.MAX_EXPORT_LIMIT]

        response = StreamingHttpResponse(
            generate_drones_csv(limited_queryset), content_type="text/csv"
        )

        response["Content-Disposition"] = 'attachment; filename="drones_export.csv"'

        return response


@drone_data_import_schema
class DroneDataImportView(generics.GenericAPIView):
    """Import drone inventory records from an uploaded CSV file."""

    permission_classes = [DronePermission]
    serializer_class = DroneImportSerializer

    def post(self, request, *args, **kwargs):
        """Validate the upload and return import counts with row-level errors."""
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


class WriteOffRecordListCreateView(generics.ListCreateAPIView):
    """List existing write-offs or create a new immutable write-off record."""

    permission_classes = [WriteOffPermission]

    def get_queryset(self):
        """Return write-offs with related drone, author, and mission data."""
        return WriteOffRecord.objects.select_related(
            "drone",
            "authorized_by",
            "related_mission",
        ).order_by("-written_off_at")

    def get_serializer_class(self):
        """Use the create serializer for POST and the read serializer otherwise."""
        if self.request.method == "POST":
            return WriteOffRecordCreateSerializer
        return WriteOffRecordSerializer
