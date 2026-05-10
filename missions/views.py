from django.db import transaction
from rest_framework import generics, permissions

from .models import Mission, Status  
from .permissions import IsDispatcherOrAdmin
from .serializers import MissionSerializer


class MissionListCreateView(generics.ListCreateAPIView):
    serializer_class = MissionSerializer
    permission_classes = [permissions.IsAuthenticated, IsDispatcherOrAdmin]
    filterset_fields = ['status']

    def get_queryset(self):
        queryset = Mission.objects.select_related('commander', 'created_by').all()
        status_param = self.request.query_params.get('status')
        if status_param:
            queryset = queryset.filter(status=status_param)
        return queryset

    @transaction.atomic
    def perform_create(self, serializer):
        serializer.save(
            status=Status.PLANNED,
            created_by=self.request.user,
        )


class MissionDetailView(generics.RetrieveAPIView):
    serializer_class = MissionSerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = Mission.objects.select_related('commander', 'created_by').all()
