"""API and HTML views for the repairs app.

Provides endpoints for creating and managing defect reports, repair orders,
component replacements, and retrieving historical timelines via REST and CSV.
All state-mutating logic is delegated to the service layer.
"""

import csv

from django.conf import settings
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.http import StreamingHttpResponse
from django.shortcuts import get_object_or_404
from django.views.generic import DetailView, TemplateView
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema_view
from rest_framework import filters, generics, status
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView

from accounts.permissions import user_has_permission
from accounts.rbac import PERMISSION_REPAIRS_VIEW
from common.pagination import StandardResultsSetPagination
from common.utils import EchoBuffer
from drones.models import Drone

from .api_details import (
    component_replacement_detail_schema,
    component_replacement_export_schema,
    component_replacement_get_schema,
    component_replacement_post_schema,
    defect_detail_schema,
    defect_get_schema,
    defect_history_get_schema,
    defect_post_schema,
    defect_status_update_post_schema,
    drone_repair_history_export_schema,
    drone_repair_history_get_schema,
    repair_order_detail_get_schema,
    repair_order_detail_patch_schema,
    repair_order_get_schema,
    repair_order_post_schema,
    repair_order_replacement_post_schema,
)
from .filters import ComponentReplacementFilter, DefectFilter, RepairOrderFilter
from .models import ComponentReplacement, DefectReport, RepairEvent, RepairOrder
from .permissions import (
    RepairHistoryExportPermission,
    RepairManagePermission,
    RepairPermission,
)
from .serializers import (
    ComponentReplacementListSerializer,
    ComponentReplacementSerializer,
    DateRangeSerializer,
    DefectReportListSerializer,
    DefectReportSerializer,
    DefectStatusUpdateSerializer,
    RepairEventSerializer,
    RepairHistoryTimelineSerializer,
    RepairOrderCreateSerializer,
    RepairOrderListSerializer,
    RepairOrderReplacementSerializer,
    RepairOrderSerializer,
    RepairOrderStatusUpdateSerializer,
)
from .services import (
    generate_repair_history_csv,
    get_drone_repair_history,
    update_defect_status,
)


@extend_schema_view(get=defect_get_schema, post=defect_post_schema)
class DefectListCreateView(generics.ListCreateAPIView):
    """List existing defect reports or create a new one."""

    serializer_class = DefectReportSerializer
    permission_classes = [RepairPermission]
    filter_backends = (
        DjangoFilterBackend,
        filters.OrderingFilter,
    )
    filterset_class = DefectFilter
    pagination_class = StandardResultsSetPagination
    ordering_fields = ["detected_at", "created_at", "severity"]

    def get_queryset(self):
        """Return the base queryset with relations pre-selected for performance."""
        return DefectReport.objects.select_related("drone", "reporter")

    def get_serializer_class(self):
        """Use a slim serializer for listing and a detailed one for creation."""
        if self.request.method == "GET":
            return DefectReportListSerializer

        return self.serializer_class


@defect_detail_schema
class DefectDetailView(generics.RetrieveAPIView):
    """Retrieve detailed information about a specific defect report."""

    queryset = DefectReport.objects.select_related("drone", "reporter").all()
    serializer_class = DefectReportSerializer
    permission_classes = [RepairPermission]
    http_method_names = ["get", "head", "options"]


@extend_schema_view(get=defect_history_get_schema)
class DefectHistoryView(generics.ListAPIView):
    """List the audit history of state changes for a specific defect report."""

    serializer_class = RepairEventSerializer
    permission_classes = [RepairPermission]
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        """Filter repair events to the defect requested in the URL."""
        defect_id = self.kwargs.get("pk")
        return RepairEvent.objects.select_related("technician").filter(
            defect_report_id=defect_id
        )


@extend_schema_view(post=defect_status_update_post_schema)
class DefectStatusUpdateView(APIView):
    """Transition a defect report to a new status."""

    permission_classes = [RepairPermission]

    @defect_status_update_post_schema
    def post(self, request, pk):
        """Apply the status transition via the service layer."""
        serializer = DefectStatusUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        event = update_defect_status(
            defect_id=pk,
            new_status=serializer.validated_data["status"],
            action_taken=serializer.validated_data["action_taken"],
            user=request.user,
        )

        response_serializer = RepairEventSerializer(event)
        return Response(response_serializer.data, status=status.HTTP_200_OK)


@extend_schema_view(
    get=component_replacement_get_schema, post=component_replacement_post_schema
)
class ComponentReplacementListCreateView(generics.ListCreateAPIView):
    """List hardware replacements or record a new one."""

    serializer_class = ComponentReplacementSerializer
    permission_classes = [RepairPermission]
    filter_backends = (
        DjangoFilterBackend,
        filters.OrderingFilter,
    )
    filterset_class = ComponentReplacementFilter
    pagination_class = StandardResultsSetPagination
    ordering_fields = ["replaced_at", "created_at", "component_type"]

    def get_queryset(self):
        """Return the base queryset with relations pre-selected for performance."""
        return ComponentReplacement.objects.select_related("drone", "replaced_by")

    def get_serializer_class(self):
        """Use a slim serializer for listing and a detailed one for creation."""
        if self.request.method == "GET":
            return ComponentReplacementListSerializer

        return self.serializer_class


@component_replacement_detail_schema
class ComponentReplacementDetailView(generics.RetrieveAPIView):
    """Retrieve detailed information about a specific component replacement."""

    queryset = ComponentReplacement.objects.select_related("drone", "replaced_by").all()
    serializer_class = ComponentReplacementSerializer
    permission_classes = [RepairPermission]
    http_method_names = ["get", "head", "options"]


@component_replacement_export_schema
class ComponentReplacementExportView(generics.GenericAPIView):
    """Stream a CSV export of filtered component replacements."""

    permission_classes = [RepairPermission]
    filter_backends = (DjangoFilterBackend,)
    filterset_class = ComponentReplacementFilter

    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "component_replacement_export"

    def get_queryset(self):
        """Return the base queryset configured for the export generator."""
        return ComponentReplacement.objects.select_related("drone", "replaced_by")

    def get(self, request, *args, **kwargs):
        """Assemble and stream the CSV response chunk by chunk."""
        max_export_limit = getattr(settings, "MAX_EXPORT_LIMIT", 10000)
        queryset = self.filter_queryset(self.get_queryset())[:max_export_limit]

        def generate_csv():
            writer = csv.writer(EchoBuffer())

            yield writer.writerow(
                [
                    "ID",
                    "Drone ID",
                    "Drone Serial Number",
                    "Component Type",
                    "Component Name",
                    "Old Serial Number",
                    "New Serial Number",
                    "Reason",
                    "Replaced At",
                    "Replaced By",
                ]
            )

            for replacement in queryset.iterator(chunk_size=2000):
                yield writer.writerow(
                    [
                        replacement.id,
                        replacement.drone_id,
                        replacement.drone.serial_number,
                        replacement.component_type,
                        replacement.component_name or "N/A",
                        replacement.old_serial_number or "N/A",
                        replacement.new_serial_number,
                        replacement.reason,
                        replacement.replaced_at.strftime("%Y-%m-%d %H:%M:%S"),
                        (
                            replacement.replaced_by.username
                            if replacement.replaced_by
                            else "N/A"
                        ),
                    ]
                )

        response = StreamingHttpResponse(generate_csv(), content_type="text/csv")
        response["Content-Disposition"] = (
            'attachment; filename="component_replacements.csv"'
        )
        response["X-Export-Limit"] = str(max_export_limit)

        return response


class DefectUIDetailView(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    """Render the HTML detail page for a specific defect report."""

    model = DefectReport
    template_name = "repairs/defect_detail.html"
    context_object_name = "defect"

    def test_func(self):
        """Ensure the user possesses the required viewing permission."""
        return user_has_permission(self.request.user, PERMISSION_REPAIRS_VIEW)


@extend_schema_view(get=repair_order_get_schema, post=repair_order_post_schema)
class RepairOrderListCreateView(generics.ListCreateAPIView):
    """List existing repair orders or create a new one."""

    permission_classes = [RepairManagePermission]
    filter_backends = (DjangoFilterBackend, filters.OrderingFilter)
    filterset_class = RepairOrderFilter
    pagination_class = StandardResultsSetPagination
    ordering_fields = ["created_at", "status"]

    def get_queryset(self):
        """Return the base queryset with relations pre-selected for performance."""
        return RepairOrder.objects.select_related(
            "drone", "defect_report", "assigned_to", "created_by"
        )

    def get_serializer_class(self):
        """Use a slim serializer for listing and a detailed one for creation."""
        if self.request.method == "GET":
            return RepairOrderListSerializer
        return RepairOrderCreateSerializer


@extend_schema_view(
    get=repair_order_detail_get_schema, patch=repair_order_detail_patch_schema
)
class RepairOrderDetailView(generics.RetrieveAPIView):
    """Retrieve or transition a specific repair order."""

    permission_classes = [RepairManagePermission]
    http_method_names = ["get", "patch", "head", "options"]

    def get_queryset(self):
        """Return the base queryset for retrieval."""
        return RepairOrder.objects.select_related(
            "drone", "defect_report", "assigned_to", "created_by"
        )

    def get_serializer_class(self):
        """Route to the transition serializer for PATCH requests."""
        if self.request.method == "PATCH":
            return RepairOrderStatusUpdateSerializer
        return RepairOrderSerializer

    def patch(self, request, *args, **kwargs):
        """Delegate state transitions to the dedicated service method."""
        repair_order = self.get_object()
        serializer = RepairOrderStatusUpdateSerializer(
            data=request.data,
            context={"request": request, "repair_order": repair_order},
        )
        serializer.is_valid(raise_exception=True)
        updated = serializer.save()
        return Response(
            RepairOrderSerializer(updated).data,
            status=status.HTTP_200_OK,
        )


@extend_schema_view(post=repair_order_replacement_post_schema)
class RepairOrderReplacementView(generics.CreateAPIView):
    """Attach a new component replacement to an existing repair order."""

    permission_classes = [RepairManagePermission]
    serializer_class = RepairOrderReplacementSerializer

    def get_repair_order(self):
        """Fetch the parent repair order from the URL kwargs."""
        return get_object_or_404(RepairOrder, pk=self.kwargs["pk"])

    def perform_create(self, serializer):
        """Inject the parent order into the serializer prior to creation."""
        serializer.save(repair_order=self.get_repair_order())


@extend_schema_view(get=drone_repair_history_get_schema)
class DroneRepairHistoryView(generics.GenericAPIView):
    """Retrieve a chronological, aggregated timeline of repair events for a drone."""

    permission_classes = [RepairPermission]
    serializer_class = RepairHistoryTimelineSerializer
    pagination_class = StandardResultsSetPagination

    def get(self, request, drone_id):
        """Fetch, validate, and paginate the unified drone history timeline."""
        get_object_or_404(Drone, pk=drone_id)

        date_serializer = DateRangeSerializer(data=request.query_params)
        date_serializer.is_valid(raise_exception=True)
        date_from = date_serializer.validated_data.get("date_from")
        date_to = date_serializer.validated_data.get("date_to")

        event_type = request.query_params.get("event_type")
        event_types = (
            [t.strip() for t in event_type.split(",") if t.strip()]
            if event_type
            else None
        )

        timeline = get_drone_repair_history(
            drone_id,
            date_from=date_from,
            date_to=date_to,
            event_types=event_types,
        )

        paginator = self.pagination_class()
        page = paginator.paginate_queryset(timeline, request)
        serializer = RepairHistoryTimelineSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)


@extend_schema_view(get=drone_repair_history_export_schema)
class DroneRepairHistoryExportView(generics.GenericAPIView):
    """Stream a CSV export of a drone's complete repair timeline."""

    permission_classes = [RepairHistoryExportPermission]
    serializer_class = RepairHistoryTimelineSerializer

    def get(self, request, drone_id):
        """Fetch the timeline and assemble the CSV streaming response."""
        drone = get_object_or_404(Drone, pk=drone_id)

        date_serializer = DateRangeSerializer(data=request.query_params)
        date_serializer.is_valid(raise_exception=True)
        date_from = date_serializer.validated_data.get("date_from")
        date_to = date_serializer.validated_data.get("date_to")

        event_type = request.query_params.get("event_type")
        event_types = (
            [t.strip() for t in event_type.split(",") if t.strip()]
            if event_type
            else None
        )

        timeline = get_drone_repair_history(
            drone_id,
            date_from=date_from,
            date_to=date_to,
            event_types=event_types,
        )

        filename = f"repair_history_drone_{drone.serial_number}.csv"
        response = StreamingHttpResponse(
            generate_repair_history_csv(timeline),
            content_type="text/csv",
        )
        response["Content-Disposition"] = f'attachment; filename="{filename}"'
        return response


class DroneRepairHistoryPageView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    """Render the HTML timeline page for a drone's repair history."""

    template_name = "repairs/history.html"

    def test_func(self):
        """Ensure the user possesses the required viewing permission."""
        return user_has_permission(self.request.user, PERMISSION_REPAIRS_VIEW)

    def get_context_data(self, **kwargs):
        """Assemble the drone, filter states, and timeline list for the template."""
        context = super().get_context_data(**kwargs)
        drone_id = self.kwargs["drone_id"]
        context["drone"] = get_object_or_404(Drone, pk=drone_id)

        date_serializer = DateRangeSerializer(data=self.request.GET)
        date_from = None
        date_to = None
        if date_serializer.is_valid():
            date_from = date_serializer.validated_data.get("date_from")
            date_to = date_serializer.validated_data.get("date_to")

        event_type = self.request.GET.get("event_type")
        event_types = (
            [t.strip() for t in event_type.split(",") if t.strip()]
            if event_type
            else None
        )

        context["filters"] = {
            "date_from": self.request.GET.get("date_from", ""),
            "date_to": self.request.GET.get("date_to", ""),
            "event_type": event_type or "",
        }
        context["timeline"] = get_drone_repair_history(
            drone_id,
            date_from=date_from,
            date_to=date_to,
            event_types=event_types,
        )
        return context
