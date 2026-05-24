from django.db import transaction
from rest_framework import generics, permissions
from rest_framework.exceptions import ValidationError
from rest_framework.pagination import PageNumberPagination

from drones.models import Drone

from .models import Mission, MissionAuditLog, Status
from .permissions import CanUpdateMissionStatus, IsDispatcherOrAdmin
from .serializers import MissionSerializer, MissionStatusUpdateSerializer


class MissionPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = "page_size"
    max_page_size = 50


class MissionListCreateView(generics.ListCreateAPIView):
    serializer_class = MissionSerializer
    permission_classes = [permissions.IsAuthenticated, IsDispatcherOrAdmin]
    pagination_class = MissionPagination

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

        assigned_to = self.request.query_params.get("assigned_to")
        if assigned_to:
            if assigned_to != "me":
                raise ValidationError(
                    f"Invalid value '{assigned_to}'. The only allowed value is 'me'."
                )
            user = self.request.user
            queryset = queryset.filter(mission_drones__operator_id=user.id).distinct()

        return queryset

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)


class MissionDetailView(generics.RetrieveAPIView):
    serializer_class = MissionSerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = Mission.objects.with_related()


class MissionStatusUpdateView(generics.RetrieveUpdateAPIView):
    serializer_class = MissionStatusUpdateSerializer
    permission_classes = [permissions.IsAuthenticated, CanUpdateMissionStatus]
    queryset = Mission.objects.all()

    def perform_update(self, serializer):
        with transaction.atomic():
            old_status = serializer.instance.status
            mission = serializer.save()

            MissionAuditLog.objects.create(
                user=self.request.user,
                action="mission_status_changed",
                target_model="Mission",
                target_id=mission.id,
                changes={"previous": old_status, "new": mission.status},
            )

            if mission.status == Status.ACTIVE:
                assigned_drones_ids = mission.mission_drones.values_list(
                    "drone_id", flat=True
                )

                if assigned_drones_ids:
                    Drone.objects.filter(id__in=assigned_drones_ids).update(
                        status="ACTIVE"
                    )

            elif mission.status in [Status.COMPLETED, Status.ABORTED]:
                mission_drones = mission.mission_drones.select_related("drone").all()

                drones_to_update = []
                for link in mission_drones:
                    drone = link.drone
                    new_status = (
                        link.condition_after if link.condition_after else "ACTIVE"
                    )

                    if drone.status != new_status:
                        drone.status = new_status
                        drones_to_update.append(drone)

                if drones_to_update:
                    Drone.objects.bulk_update(drones_to_update, ["status"])
