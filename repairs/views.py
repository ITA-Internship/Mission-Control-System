from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, generics, status
from rest_framework.response import Response
from rest_framework.views import APIView

from common.pagination import StandardResultsSetPagination

from .filters import DefectFilter
from .models import DefectReport, RepairEvent
from .permissions import RepairPermission
from .serializers import (
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
    permission_classes = [RepairPermission]

    def post(self, request, pk):
        defect = get_object_or_404(DefectReport, pk=pk)

        serializer = DefectStatusUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        event = update_defect_status(
            defect=defect,
            new_status=serializer.validated_data["status"],
            action_taken=serializer.validated_data["action_taken"],
            user=request.user,
        )

        response_serializer = RepairEventSerializer(event)
        return Response(response_serializer.data, status=status.HTTP_200_OK)
