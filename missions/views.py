from django.db import transaction
from rest_framework import generics, permissions
from rest_framework.exceptions import ValidationError

from drones.models import Drone, DroneStatus

from .models import AuditLog, Mission, MissionDrone, Status
from .permissions import IsDispatcherOrAdmin
from .serializers import MissionDroneSerializer, MissionSerializer


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
        if not hasattr(self, "_mission"):
            self._mission = generics.get_object_or_404(
                Mission, id=self.kwargs["mission_pk"]
            )
        return self._mission

    def get_queryset(self):
        mission = self.get_mission()
        return MissionDrone.objects.filter(mission=mission).select_related(
            "drone", "operator"
        )

    def get_serializer_context(self):
        context = super().get_serializer_context()
        if self.request.method in ["POST", "PUT", "PATCH"]:
            context["mission"] = self.get_mission()
        return context

    def perform_create(self, serializer):
        mission = self.get_mission()
        serializer.save(mission=mission)


class MissionAssignmentDetailView(generics.DestroyAPIView):
    permission_classes = [permissions.IsAuthenticated, IsDispatcherOrAdmin]
    lookup_url_kwarg = "pk"

    def get_queryset(self):
        return MissionDrone.objects.filter(
            mission_id=self.kwargs["mission_pk"]
        ).select_related("mission", "drone")

    def perform_destroy(self, instance):
        with transaction.atomic():
            mission = Mission.objects.select_for_update().get(
                id=instance.mission_id
            )
            if mission.status != Status.PLANNED:
                raise ValidationError(
                    "Cannot delete assignment unless mission is planned."
                )

            drone_id = instance.drone_id
            operator_id = instance.operator_id
            mission_id = instance.mission_id

            drone = Drone.objects.select_for_update().get(id=drone_id)
            if drone.status == DroneStatus.IN_MISSION:
                drone.status = DroneStatus.ACTIVE
                drone.save(update_fields=["status"])

            AuditLog.objects.create(
                action="assignment_deleted",
                target_model="MissionDrone",
                user=self.request.user,
                changes={
                    "mission_id": mission_id,
                    "drone_id": drone_id,
                    "operator_id": operator_id,
                },
            )
            instance.delete()
