from rest_framework import generics, permissions
from rest_framework.pagination import PageNumberPagination

from .models import Mission
from .permissions import IsDispatcherOrAdmin
from .serializers import MissionSerializer, MissionStatusUpdateSerializer

class MissionPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 50

class MissionListCreateView(generics.ListCreateAPIView):
    serializer_class = MissionSerializer
    permission_classes = [permissions.IsAuthenticated, IsDispatcherOrAdmin]
    pagination_class = MissionPagination

    def get_queryset(self):
        queryset = Mission.objects.with_related()
        status = self.request.query_params.get("status")
        if status:
            queryset = queryset.filter(status=status)
    
        assigned_to = self.request.query_params.get("assigned_to")
        if assigned_to == "me":
            user = self.request.user
            queryset = queryset.filter(mission_drones__operator_id=user.id).distinct()

        return queryset

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)


class MissionDetailView(generics.RetrieveAPIView):
    serializer_class = MissionSerializer
    permission_classes = [permissions.IsAuthenticated, IsDispatcherOrAdmin]
    queryset = Mission.objects.with_related()


class MissionStatusUpdateView(generics.UpdateAPIView):
    serializer_class = MissionStatusUpdateSerializer
    permission_classes = [permissions.IsAuthenticated, IsDispatcherOrAdmin]
    queryset = Mission.objects.all()

    