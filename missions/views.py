"""API views for the missions app.

Expose endpoints for listing and creating missions, retrieving detail, updating
status, recording outcomes and drone conditions, and managing assignments. RBAC
permission mixins gate each action.
"""

from django.db import transaction
from rest_framework import generics, permissions
from rest_framework.exceptions import ValidationError

from accounts.permissions import HasRBACPermission
from accounts.rbac import (
    PERMISSION_MISSIONS_ASSIGN,
    PERMISSION_MISSIONS_CREATE,
    PERMISSION_MISSIONS_RECORD_CONDITION,
    PERMISSION_MISSIONS_RECORD_OUTCOME,
    PERMISSION_MISSIONS_UPDATE_STATUS,
    PERMISSION_MISSIONS_VIEW,
)
from common.pagination import StandardResultsSetPagination
from roles.models import OPERATOR_CODE

from .models import Mission, MissionAuditLog, MissionDrone, Status
from .permissions import (
    CanUpdateMissionStatus,
    CanViewMission,
    IsAssignedOperatorOrAdmin,
    IsDispatcherOrAdmin,
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
    """Scope a mission queryset to what ``user`` is allowed to see.

    Operators only see missions they are assigned to (via a drone); every
    other role sees the queryset unchanged. Applied by the mission read views
    so object-level ownership is enforced at the queryset level.
    """
    role_code = getattr(getattr(user, "role", None), "code", None)
    if role_code == OPERATOR_CODE:
        return queryset.filter(mission_drones__operator_id=user.id).distinct()
    return queryset


class MissionsUpdateStatusRBAC(HasRBACPermission):
    """Require the mission status-update RBAC permission."""

    required_permission = PERMISSION_MISSIONS_UPDATE_STATUS


class MissionsRecordOutcomeRBAC(HasRBACPermission):
    """Require the mission record-outcome RBAC permission."""

    required_permission = PERMISSION_MISSIONS_RECORD_OUTCOME


class MissionsRecordConditionRBAC(HasRBACPermission):
    """Require the mission record-condition RBAC permission."""

    required_permission = PERMISSION_MISSIONS_RECORD_CONDITION


class MissionsViewRBAC(HasRBACPermission):
    """Require the mission view RBAC permission."""

    required_permission = PERMISSION_MISSIONS_VIEW


class MissionsCreateRBAC(HasRBACPermission):
    """Require the mission create RBAC permission."""

    required_permission = PERMISSION_MISSIONS_CREATE


class MissionsAssignRBAC(HasRBACPermission):
    """Require the mission assign RBAC permission."""

    required_permission = PERMISSION_MISSIONS_ASSIGN


class MissionListCreateView(generics.ListCreateAPIView):
    """List missions or create one.

    GET is open to any authenticated user with the view permission and supports
    ``status`` and ``assigned_to=me`` query filters. POST is restricted to
    Dispatcher/Admin with the create permission.
    """

    serializer_class = MissionSerializer
    pagination_class = StandardResultsSetPagination

    def get_permissions(self):
        """Gate reads behind the view permission; POST behind create."""
        if self.request.method in permissions.SAFE_METHODS:
            permission_classes = [permissions.IsAuthenticated, CanViewMission]
        else:
            permission_classes = [
                permissions.IsAuthenticated,
                IsDispatcherOrAdmin,
                MissionsCreateRBAC,
            ]
        return [permission() for permission in permission_classes]

    def get_queryset(self):
        """Return missions visible to the user, applying the query filters.

        Restricts to the user's own missions when they are an operator, then
        applies the optional ``status`` and ``assigned_to=me`` filters. Raises
        ValidationError for an unknown ``status`` or an ``assigned_to`` value
        other than ``me``.
        """
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
        """Save the mission, stamping the requesting user as ``created_by``."""
        serializer.save(created_by=self.request.user)


class MissionDetailView(generics.RetrieveAPIView):
    """Retrieve a single mission (requires the view permission)."""

    serializer_class = MissionSerializer
    permission_classes = [permissions.IsAuthenticated, CanViewMission]

    def get_queryset(self):
        """Return only missions the requesting user is allowed to view."""
        return restrict_missions_for_user(
            Mission.objects.with_related(),
            self.request.user,
        )


class MissionOutcomeView(generics.UpdateAPIView):
    """Record the outcome of a completed/aborted mission via PATCH.

    Restricted to the assigned operator or an admin with the record-outcome
    permission.
    """

    serializer_class = MissionOutcomeSerializer
    permission_classes = [
        permissions.IsAuthenticated,
        MissionsRecordOutcomeRBAC,
        IsAssignedOperatorOrAdmin,
    ]
    http_method_names = ["patch", "options", "head"]

    def get_queryset(self):
        """Return only missions the requesting user is allowed to act on."""
        return restrict_missions_for_user(
            Mission.objects.with_related().prefetch_related("mission_drones"),
            self.request.user,
        )


class MissionDroneConditionView(generics.UpdateAPIView):
    """Record a drone's post-mission condition for one assignment via PATCH.

    Restricted to the assigned operator or an admin with the record-condition
    permission.
    """

    serializer_class = MissionDroneConditionSerializer
    permission_classes = [
        permissions.IsAuthenticated,
        MissionsRecordConditionRBAC,
        IsAssignedOperatorOrAdmin,
    ]
    lookup_url_kwarg = "assignment_id"
    http_method_names = ["patch", "options", "head"]

    def get_queryset(self):
        """Scope assignments to the mission in the URL.

        An ``assignment_id`` belonging to a different mission resolves to 404
        rather than being editable through the wrong mission's endpoint.
        """
        # Scope assignments to the mission in the URL so an assignment_id
        # belonging to a different mission resolves to 404 rather than being
        # editable through the wrong mission's endpoint.
        return MissionDrone.objects.filter(
            mission_id=self.kwargs["pk"],
        ).select_related("mission", "drone", "operator")


class MissionStatusUpdateView(generics.RetrieveUpdateAPIView):
    """Retrieve or update a mission's status through its lifecycle.

    Gated by ``CanUpdateMissionStatus`` (Admin/Commander any mission, Operator
    only their own). Updates lock the mission row and run in a transaction.
    """

    serializer_class = MissionStatusUpdateSerializer
    permission_classes = [permissions.IsAuthenticated, CanUpdateMissionStatus]

    def get_queryset(self):
        """Return only missions the requesting user is allowed to act on."""
        return restrict_missions_for_user(
            Mission.objects.prefetch_related("mission_drones"),
            self.request.user,
        )

    def update(self, request, *args, **kwargs):
        """Extend the base update to wrap it in a transaction."""
        with transaction.atomic():
            return super().update(request, *args, **kwargs)

    def get_object(self):
        """Lock the mission row with ``select_for_update`` on PUT/PATCH.

        Falls back to the default lookup for safe methods.
        """
        queryset = self.filter_queryset(self.get_queryset())

        if self.request.method in ["PUT", "PATCH"]:
            return queryset.select_for_update().get(pk=self.kwargs["pk"])

        return super().get_object()

    def perform_update(self, serializer):
        """Save the status change and write a ``mission_status_changed`` audit entry."""
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
    """List a mission's drone assignments or create one.

    GET is open to any authenticated user with the view permission; POST is
    restricted to Dispatcher/Admin with the assign permission.
    """

    serializer_class = MissionDroneSerializer

    pagination_class = StandardResultsSetPagination

    def get_permissions(self):
        """Gate POST behind assign permissions; other methods behind view."""
        if self.request.method == "POST":
            permission_classes = [
                permissions.IsAuthenticated,
                IsDispatcherOrAdmin,
                MissionsAssignRBAC,
            ]
        else:
            permission_classes = [
                permissions.IsAuthenticated,
                MissionsViewRBAC,
            ]

        return [permission() for permission in permission_classes]

    def get_mission(self):
        """Return the mission named in the URL (cached per request), or 404."""
        if not hasattr(self, "_mission"):
            self._mission = generics.get_object_or_404(
                restrict_missions_for_user(Mission.objects.all(), self.request.user),
                id=self.kwargs["mission_pk"],
            )
        return self._mission

    def get_queryset_for_list(self):
        """Return the assignments belonging to the mission in the URL."""
        mission = self.get_mission()
        return MissionDrone.objects.filter(mission=mission).select_related(
            "drone",
            "operator",
        )

    def get_queryset(self):
        """Return the assignment list for safe methods; empty otherwise."""
        if self.request.method in permissions.SAFE_METHODS:
            return self.get_queryset_for_list()

        return MissionDrone.objects.none()

    def get_serializer_context(self):
        """Extend the context with the target mission on POST."""
        context = super().get_serializer_context()

        if self.request.method == "POST":
            context["mission"] = self.get_mission()

        return context

    def perform_create(self, serializer):
        """Create the assignment against the mission in the URL."""
        mission = self.get_mission()
        serializer.save(mission=mission)


class MissionAssignmentDetailView(generics.DestroyAPIView):
    """Delete a drone assignment from a mission (Dispatcher/Admin only)."""

    permission_classes = [
        permissions.IsAuthenticated,
        IsDispatcherOrAdmin,
        MissionsAssignRBAC,
    ]
    lookup_url_kwarg = "pk"

    def get_queryset(self):
        """Return assignments scoped to the mission named in the URL."""
        return MissionDrone.objects.filter(
            mission_id=self.kwargs["mission_pk"]
        ).select_related("mission", "drone")

    def perform_destroy(self, instance):
        """Delete the assignment via the ``unassign_drone_from_mission`` service.

        The service enforces that the mission is still planned and writes an
        audit entry.
        """
        unassign_drone_from_mission(
            assignment=instance,
            action_user=self.request.user,
        )
