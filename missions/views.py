from rest_framework import generics, permissions
from rest_framework.exceptions import ValidationError

from accounts.permissions import HasRBACPermission
from accounts.rbac import PERMISSION_MISSIONS_UPDATE_STATUS

from .models import Mission, MissionDrone, Status
from .permissions import IsAssignedOperatorOrAdmin, IsDispatcherOrAdmin
from .serializers import (
    MissionDroneConditionSerializer,
    MissionDroneSerializer,
    MissionOutcomeSerializer,
    MissionSerializer,
)
from .services import unassign_drone_from_mission


class MissionsUpdateStatusRBAC(HasRBACPermission):
    required_permission = PERMISSION_MISSIONS_UPDATE_STATUS


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


class MissionOutcomeView(generics.UpdateAPIView):
    serializer_class = MissionOutcomeSerializer
    permission_classes = [
        permissions.IsAuthenticated,
        MissionsUpdateStatusRBAC,
        IsAssignedOperatorOrAdmin,
    ]
    queryset = Mission.objects.with_related()
    http_method_names = ["patch", "options", "head"]


class MissionDroneConditionView(generics.UpdateAPIView):
    serializer_class = MissionDroneConditionSerializer
    permission_classes = [
        permissions.IsAuthenticated,
        MissionsUpdateStatusRBAC,
        IsAssignedOperatorOrAdmin,
    ]
    lookup_url_kwarg = "assignment_id"
    http_method_names = ["patch", "options", "head"]

    def get_queryset(self):
        return MissionDrone.objects.filter(
            mission_id=self.kwargs["pk"],
        ).select_related("mission", "drone", "operator")


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
        unassign_drone_from_mission(
            assignment=instance,
            action_user=self.request.user,
        )
