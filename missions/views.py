from django.db import transaction
from rest_framework import generics, permissions
from rest_framework.exceptions import ValidationError

from common.pagination import StandardResultsSetPagination
from roles.models import OPERATOR_CODE

from .models import Mission, MissionAuditLog, MissionDrone, Status
from .permissions import (
    CanAssignMission,
    CanCreateMission,
    CanRecordCondition,
    CanRecordOutcome,
    CanUpdateMissionStatus,
    CanViewMission,
    IsAssignedOperatorOrAdmin,
    IsAssignedToMissionOrAdmin,
)
from .serializers import (
    MissionDroneConditionSerializer,
    MissionDroneSerializer,
    MissionOutcomeSerializer,
    MissionSerializer,
    MissionStatusUpdateSerializer,
)
from .services import unassign_drone_from_mission


def restrict_missions_for_user(queryset, user):
    role_code = getattr(getattr(user, "role", None), "code", None)
    if role_code == OPERATOR_CODE:
        return queryset.filter(mission_drones__operator_id=user.id).distinct()
    return queryset


class MissionListCreateView(generics.ListCreateAPIView):
    serializer_class = MissionSerializer
    pagination_class = StandardResultsSetPagination

    def get_permissions(self):
        if self.request.method in permissions.SAFE_METHODS:
            permission_classes = [permissions.IsAuthenticated, CanViewMission]
        else:
            permission_classes = [
                permissions.IsAuthenticated,
                CanCreateMission,
            ]
        return [permission() for permission in permission_classes]

    def get_queryset(self):
        queryset = restrict_missions_for_user(
            Mission.objects.with_related(),
            self.request.user,
        )

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
                    {
                        "assigned_to": f"Invalid value '{assigned_to}'."
                        " The only allowed value is 'me'."
                    }
                )

            user = self.request.user
            user_mission_ids = MissionDrone.objects.filter(operator_id=user.id).values(
                "mission_id"
            )
            queryset = queryset.filter(id__in=user_mission_ids)

        return queryset

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)


class MissionDetailView(generics.RetrieveAPIView):
    serializer_class = MissionSerializer
    permission_classes = [permissions.IsAuthenticated, CanViewMission]

    def get_queryset(self):
        return restrict_missions_for_user(
            Mission.objects.with_related(),
            self.request.user,
        )


class MissionOutcomeView(generics.UpdateAPIView):
    serializer_class = MissionOutcomeSerializer
    permission_classes = [
        permissions.IsAuthenticated,
        CanRecordOutcome,
        IsAssignedOperatorOrAdmin,
    ]
    queryset = Mission.objects.with_related()
    http_method_names = ["patch", "options", "head"]

    def get_queryset(self):
        return restrict_missions_for_user(
            Mission.objects.with_related(),
            self.request.user,
        )


class MissionDroneConditionView(generics.UpdateAPIView):
    serializer_class = MissionDroneConditionSerializer
    permission_classes = [
        permissions.IsAuthenticated,
        CanRecordCondition,
        IsAssignedOperatorOrAdmin,
    ]
    lookup_url_kwarg = "assignment_id"
    http_method_names = ["patch", "options", "head"]

    def get_queryset(self):
        return MissionDrone.objects.filter(
            mission_id=self.kwargs["pk"],
        ).select_related("mission", "drone", "operator")


class MissionStatusUpdateView(generics.RetrieveUpdateAPIView):
    serializer_class = MissionStatusUpdateSerializer
    permission_classes = [
        permissions.IsAuthenticated,
        CanUpdateMissionStatus,
        IsAssignedToMissionOrAdmin,
    ]
    queryset = Mission.objects.prefetch_related("mission_drones")

    def get_queryset(self):
        return restrict_missions_for_user(
            self.queryset,
            self.request.user,
        )

    def update(self, request, *args, **kwargs):
        with transaction.atomic():
            return super().update(request, *args, **kwargs)

    def get_object(self):
        queryset = self.filter_queryset(self.get_queryset())

        if self.request.method in ["PUT", "PATCH"]:
            return queryset.select_for_update().get(pk=self.kwargs["pk"])

        return super().get_object()

    def perform_update(self, serializer):
        old_status = serializer.instance.status
        mission = serializer.save()

        MissionAuditLog.objects.create(
            user=self.request.user,
            action="mission_status_changed",
            target_model="Mission",
            target_id=mission.id,
            changes={"previous": old_status, "new": mission.status},
        )


class MissionAssignmentListCreateView(generics.ListCreateAPIView):
    serializer_class = MissionDroneSerializer

    pagination_class = StandardResultsSetPagination

    def get_permissions(self):
        if self.request.method == "POST":
            permission_classes = [
                permissions.IsAuthenticated,
                CanAssignMission,
            ]
        else:
            permission_classes = [
                permissions.IsAuthenticated,
                CanViewMission,
            ]

        return [permission() for permission in permission_classes]

    def get_mission(self):
        if not hasattr(self, "_mission"):
            self._mission = generics.get_object_or_404(
                restrict_missions_for_user(Mission.objects.all(), self.request.user),
                id=self.kwargs["mission_pk"],
            )
        return self._mission

    def get_queryset_for_list(self):
        mission = self.get_mission()
        return (
            MissionDrone.objects.filter(mission=mission)
            .select_related(
                "drone",
                "operator",
            )
            .order_by("id")
        )

    def get_queryset(self):
        if self.request.method in permissions.SAFE_METHODS:
            return self.get_queryset_for_list()

        return MissionDrone.objects.none()

    def get_serializer_context(self):
        context = super().get_serializer_context()

        if self.request.method == "POST":
            context["mission"] = self.get_mission()

        return context

    def perform_create(self, serializer):
        mission = self.get_mission()
        serializer.save(mission=mission)


class MissionAssignmentDetailView(generics.DestroyAPIView):
    permission_classes = [
        permissions.IsAuthenticated,
        CanAssignMission,
    ]
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
