from django.apps import apps
from django.db import transaction
from rest_framework import generics, permissions
from rest_framework.exceptions import ValidationError

from .models import Mission, Status, MissionDrone, AuditLog
from .permissions import IsDispatcherOrAdmin
from .serializers import MissionSerializer, MissionDroneSerializer


class MissionListCreateView(generics.ListCreateAPIView):
    serializer_class = MissionSerializer
    permission_classes = [permissions.IsAuthenticated, IsDispatcherOrAdmin]

    def get_queryset(self):
        queryset = Mission.objects.with_related()
        status = self.request.query_params.get("status")
        if status:
            if status not in Status.values:
                raise ValidationError(
                    {
                        "status": (
                            f"Invalid status '{status}'. "
                            f"Must be one of: {', '.join(Status.values)}."
                        )
                    }
                )
            queryset = queryset.filter(status=status)
        return queryset

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)


class MissionDetailView(generics.RetrieveAPIView):
    serializer_class = MissionSerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = Mission.objects.with_related()


class MissionAssignmentListCreateView(generics.ListCreateAPIView):
    serializer_class = MissionDroneSerializer
    permission_classes = [permissions.IsAuthenticated, IsDispatcherOrAdmin]

    def get_mission(self):
        if not hasattr(self, '_mission'):
            self._mission = generics.get_object_or_404(Mission, id=self.kwargs['id'])
        return self._mission

    def get_queryset(self):
        mission = self.get_mission()
        return MissionDrone.objects.filter(mission=mission).select_related('drone', 'operator')

    def get_serializer_context(self):
        context = super().get_serializer_context()
        if self.request.method in ['POST', 'PUT', 'PATCH']:
            context['mission'] = self.get_mission()
        return context

    def perform_create(self, serializer):
        mission = self.get_mission()
        serializer.save(mission=mission)


class MissionAssignmentDetailView(generics.DestroyAPIView):
    permission_classes = [permissions.IsAuthenticated, IsDispatcherOrAdmin]
    lookup_url_kwarg = 'assignment_id'

    def get_queryset(self):
        return MissionDrone.objects.filter(mission_id=self.kwargs['id']).select_related('mission')

    def perform_destroy(self, instance):
        if instance.mission.status != Status.PLANNED:
            raise ValidationError("Cannot delete assignment unless mission is planned.")
        
        with transaction.atomic():
            Drone = apps.get_model('drones', 'Drone')
            # Using instance.drone_id directly to avoid an extra DB query for the Drone object
            drone = Drone.objects.select_for_update().get(id=instance.drone_id)
            if drone.status == 'IN_MISSION':
                drone.status = 'ACTIVE'
                drone.save(update_fields=['status'])

            AuditLog.objects.create(
                action="assignment_deleted",
                target_model="MissionDrone",
                user=self.request.user,
                changes={
                    "drone_id": instance.drone_id,
                    "operator_id": instance.operator_id,
                }
            )
            instance.delete()
