from rest_framework import generics, permissions

from .models import Mission
from .permissions import IsDispatcherOrAdmin
from .serializers import MissionSerializer


class MissionListCreateView(generics.ListCreateAPIView):
    serializer_class = MissionSerializer
    permission_classes = [permissions.IsAuthenticated, IsDispatcherOrAdmin]

    def get_queryset(self):
        queryset = Mission.objects.with_related()
        status = self.request.query_params.get("status")
        if status:
            queryset = queryset.filter(status=status)
        return queryset

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)


class MissionDetailView(generics.RetrieveAPIView):
    serializer_class = MissionSerializer
    permission_classes = [permissions.IsAuthenticated, IsDispatcherOrAdmin]
    queryset = Mission.objects.with_related()
