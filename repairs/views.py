import csv

from django.http import StreamingHttpResponse
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, generics

from common.pagination import StandardResultsSetPagination

from .filters import ComponentReplacementFilter, DefectFilter
from .models import ComponentReplacement, DefectReport
from .permissions import RepairPermission
from .serializers import (
    ComponentReplacementListSerializer,
    ComponentReplacementSerializer,
    DefectReportListSerializer,
    DefectReportSerializer,
)


class Echo:
    def write(self, value):
        return value


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
        max_export_limit = 10000
        queryset = self.filter_queryset(self.get_queryset())[:max_export_limit]

        def generate_csv():
            writer = csv.writer(Echo())

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
        return response
