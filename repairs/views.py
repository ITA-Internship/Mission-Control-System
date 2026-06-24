import csv

from django.conf import settings
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.http import StreamingHttpResponse
from django.shortcuts import get_object_or_404
from django.views.generic import DetailView, TemplateView
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, generics, status
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.permissions import user_has_permission
from accounts.rbac import PERMISSION_REPAIRS_VIEW
from common.pagination import StandardResultsSetPagination
from common.utils import EchoBuffer
from drones.models import Drone

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


class DefectListCreateView(generics.ListCreateAPIView):
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
        return DefectReport.objects.select_related("drone", "reporter")

    def get_serializer_class(self):
        if self.request.method == "GET":
            return DefectReportListSerializer

        return self.serializer_class


class DefectDetailView(generics.RetrieveAPIView):
    queryset = DefectReport.objects.select_related("drone", "reporter").all()
    serializer_class = DefectReportSerializer
    permission_classes = [RepairPermission]
    http_method_names = ["get", "head", "options"]


class DefectHistoryView(generics.ListAPIView):
    serializer_class = RepairEventSerializer
    permission_classes = [RepairPermission]
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        defect_id = self.kwargs.get("pk")
        return RepairEvent.objects.select_related("technician").filter(
            defect_report_id=defect_id
        )


class DefectStatusUpdateView(APIView):
    permission_classes = [RepairPermission]

    def post(self, request, pk):
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


class ComponentReplacementListCreateView(generics.ListCreateAPIView):
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
        return ComponentReplacement.objects.select_related("drone", "replaced_by")

    def get_serializer_class(self):
        if self.request.method == "GET":
            return ComponentReplacementListSerializer

        return self.serializer_class


class ComponentReplacementDetailView(generics.RetrieveAPIView):
    queryset = ComponentReplacement.objects.select_related("drone", "replaced_by").all()
    serializer_class = ComponentReplacementSerializer
    permission_classes = [RepairPermission]
    http_method_names = ["get", "head", "options"]


class ComponentReplacementExportView(generics.GenericAPIView):
    permission_classes = [RepairPermission]
    filter_backends = (DjangoFilterBackend,)
    filterset_class = ComponentReplacementFilter

    def get_queryset(self):
        return ComponentReplacement.objects.select_related("drone", "replaced_by")

    def get(self, request, *args, **kwargs):
        max_export_limit = getattr(settings, "MAX_EXPORT_LIMIT", 10000)
        queryset = self.filter_queryset(self.get_queryset())
        total_count = queryset.count()
        export_truncated = total_count > max_export_limit

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

            for index, replacement in enumerate(
                queryset.iterator(chunk_size=2000),
                start=1,
            ):
                if index > max_export_limit:
                    break

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
        response["X-Export-Truncated"] = str(export_truncated).lower()
        return response


class DefectUIDetailView(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    model = DefectReport
    template_name = "repairs/defect_detail.html"
    context_object_name = "defect"

    def test_func(self):
        return user_has_permission(self.request.user, PERMISSION_REPAIRS_VIEW)


class RepairOrderListCreateView(generics.ListCreateAPIView):
    permission_classes = [RepairManagePermission]
    filter_backends = (DjangoFilterBackend, filters.OrderingFilter)
    filterset_class = RepairOrderFilter
    pagination_class = StandardResultsSetPagination
    ordering_fields = ["created_at", "status"]

    def get_queryset(self):
        return RepairOrder.objects.select_related(
            "drone", "defect_report", "assigned_to", "created_by"
        )

    def get_serializer_class(self):
        if self.request.method == "GET":
            return RepairOrderListSerializer
        return RepairOrderCreateSerializer


class RepairOrderDetailView(generics.RetrieveAPIView):
    permission_classes = [RepairManagePermission]
    http_method_names = ["get", "patch", "head", "options"]

    def get_queryset(self):
        return RepairOrder.objects.select_related(
            "drone", "defect_report", "assigned_to", "created_by"
        )

    def get_serializer_class(self):
        if self.request.method == "PATCH":
            return RepairOrderStatusUpdateSerializer
        return RepairOrderSerializer

    def patch(self, request, *args, **kwargs):
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


class RepairOrderReplacementView(generics.CreateAPIView):
    permission_classes = [RepairManagePermission]
    serializer_class = RepairOrderReplacementSerializer

    def get_repair_order(self):
        return get_object_or_404(RepairOrder, pk=self.kwargs["pk"])

    def perform_create(self, serializer):
        serializer.save(repair_order=self.get_repair_order())


class DroneRepairHistoryView(generics.GenericAPIView):
    permission_classes = [RepairPermission]
    serializer_class = RepairHistoryTimelineSerializer
    pagination_class = StandardResultsSetPagination

    def get(self, request, drone_id):
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


class DroneRepairHistoryExportView(generics.GenericAPIView):
    permission_classes = [RepairHistoryExportPermission]

    def get(self, request, drone_id):
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
    template_name = "repairs/history.html"

    def test_func(self):
        return user_has_permission(self.request.user, PERMISSION_REPAIRS_VIEW)

    def get_context_data(self, **kwargs):
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
