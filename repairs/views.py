import csv

from django.conf import settings
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.http import StreamingHttpResponse
from django.views.generic import DetailView
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from common.pagination import StandardResultsSetPagination
from common.utils import EchoBuffer

from .filters import ComponentReplacementFilter, DefectFilter
from .models import ComponentReplacement, DefectReport, RepairEvent
from .permissions import RepairPermission
from .serializers import (
    ComponentReplacementListSerializer,
    ComponentReplacementSerializer,
    DefectReportListSerializer,
    DefectReportSerializer,
    DefectStatusUpdateSerializer,
    RepairEventSerializer,
)
from .services import update_defect_status


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
    permission_classes = [IsAuthenticated, RepairPermission]

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
        permission = RepairPermission()
        return permission.has_permission(self.request, self)
