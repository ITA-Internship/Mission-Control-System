import threading
from datetime import timedelta

from django.db import connection
from django.test import TransactionTestCase
from django.test.utils import CaptureQueriesContext
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.test import APITestCase

from accounts.models import User
from drones.models import Drone, DroneStatusHistory, WriteOffRecord
from roles.models import TECHNICIAN_CODE, Role

from .factories import (
    AdminUserFactory,
    CommanderUserFactory,
    DispatcherUserFactory,
    DroneFactory,
    MissionDroneFactory,
    MissionFactory,
    OperatorUserFactory,
    ViewerUserFactory,
)
from .models import Mission, MissionAuditLog, MissionDrone
from .services import assign_drone_to_mission


class MissionOutcomeTests(APITestCase):
    def setUp(self):
        self.admin = AdminUserFactory()
        self.operator = OperatorUserFactory()
        self.other_operator = OperatorUserFactory()
        self.viewer = ViewerUserFactory()

        self.mission = MissionFactory(status="completed")
        self.drone = DroneFactory(status="ACTIVE")
        self.assignment = MissionDroneFactory(
            mission=self.mission,
            drone=self.drone,
            operator=self.operator,
        )

        self.url = reverse(
            "missions:mission-outcome",
            kwargs={"pk": self.mission.pk},
        )

    def test_admin_records_outcome_on_completed_mission(self):
        self.client.force_authenticate(self.admin)

        response = self.client.patch(
            self.url,
            {
                "result": "success",
                "notes": "Targets eliminated.",
                "incident_notes": "Minor signal loss at 10:30.",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.mission.refresh_from_db()

        self.assertEqual(self.mission.result, "success")
        self.assertEqual(self.mission.notes, "Targets eliminated.")
        self.assertEqual(self.mission.incident_notes, "Minor signal loss at 10:30.")

    def test_assigned_operator_can_record_outcome(self):
        self.client.force_authenticate(self.operator)

        response = self.client.patch(
            self.url,
            {
                "result": "failure",
                "notes": "Failed extraction.",
                "incident_notes": "Operator lost contact during extraction.",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.mission.refresh_from_db()

        self.assertEqual(self.mission.result, "failure")

    def test_outcome_allowed_on_aborted_mission(self):
        self.mission.status = "aborted"
        self.mission.save(update_fields=["status"])

        self.client.force_authenticate(self.admin)

        response = self.client.patch(
            self.url,
            {
                "result": "failure",
                "incident_notes": "Mission aborted before objective.",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_outcome_rejected_on_planned_mission(self):
        self.mission.status = "planned"
        self.mission.save(update_fields=["status"])

        self.client.force_authenticate(self.admin)

        response = self.client.patch(
            self.url,
            {"result": "success"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("status", response.data)

    def test_outcome_rejected_on_active_mission(self):
        self.mission.status = "active"
        self.mission.save(update_fields=["status"])

        self.client.force_authenticate(self.admin)

        response = self.client.patch(
            self.url,
            {"result": "success"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_outcome_rejects_missing_result(self):
        self.client.force_authenticate(self.admin)

        response = self.client.patch(
            self.url,
            {"notes": "Just notes, no result."},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("result", response.data)

    def test_outcome_rejects_invalid_result_value(self):
        self.client.force_authenticate(self.admin)

        response = self.client.patch(
            self.url,
            {"result": "maybe"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("result", response.data)

    def test_unassigned_operator_forbidden(self):
        self.client.force_authenticate(self.other_operator)

        response = self.client.patch(
            self.url,
            {"result": "success"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_viewer_forbidden(self):
        self.client.force_authenticate(self.viewer)

        response = self.client.patch(
            self.url,
            {"result": "success"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_unauthenticated_request_rejected(self):
        response = self.client.patch(
            self.url,
            {"result": "success"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_outcome_creates_audit_log(self):
        self.client.force_authenticate(self.admin)

        self.client.patch(
            self.url,
            {
                "result": "success",
                "notes": "All clear.",
                "incident_notes": "",
            },
            format="json",
        )

        log = MissionAuditLog.objects.get(action="mission_outcome_recorded")

        self.assertEqual(log.target_model, "Mission")
        self.assertEqual(log.user, self.admin)
        self.assertEqual(log.changes["mission_id"], self.mission.id)
        self.assertIsNone(log.changes["previous_result"])
        self.assertEqual(log.changes["new_result"], "success")
        self.assertEqual(log.changes["notes"], "All clear.")

    def test_post_not_allowed(self):
        self.client.force_authenticate(self.admin)

        response = self.client.post(self.url, {"result": "success"}, format="json")

        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)


class MissionDroneConditionTests(APITestCase):
    def setUp(self):
        self.admin = AdminUserFactory()
        self.operator = OperatorUserFactory()
        self.other_operator = OperatorUserFactory()
        self.viewer = ViewerUserFactory()

        self.mission = MissionFactory(status="completed")
        self.drone = DroneFactory(status="ACTIVE")
        self.assignment = MissionDroneFactory(
            mission=self.mission,
            drone=self.drone,
            operator=self.operator,
        )

        self.url = reverse(
            "missions:mission-drone-condition",
            kwargs={
                "pk": self.mission.pk,
                "assignment_id": self.assignment.pk,
            },
        )

    def test_condition_ok_sets_drone_active_and_writes_history(self):
        self.drone.status = "DAMAGED"
        self.drone.save(update_fields=["status"])

        self.client.force_authenticate(self.admin)

        response = self.client.patch(
            self.url,
            {"condition_after": "ok", "condition_description": "Returned intact."},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.drone.refresh_from_db()
        self.assignment.refresh_from_db()

        self.assertEqual(self.drone.status, "ACTIVE")
        self.assertEqual(self.assignment.condition_after, "ok")
        self.assertEqual(self.assignment.condition_description, "Returned intact.")

        history = DroneStatusHistory.objects.get(drone=self.drone)
        self.assertEqual(history.from_status, "DAMAGED")
        self.assertEqual(history.to_status, "ACTIVE")
        self.assertEqual(history.related_mission, self.mission)
        self.assertEqual(history.changed_by, self.admin)

    def test_condition_damaged_sets_drone_damaged(self):
        self.client.force_authenticate(self.admin)

        response = self.client.patch(
            self.url,
            {
                "condition_after": "damaged",
                "condition_description": "Frame cracked.",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.drone.refresh_from_db()

        self.assertEqual(self.drone.status, "DAMAGED")
        self.assertEqual(DroneStatusHistory.objects.count(), 1)
        self.assertEqual(WriteOffRecord.objects.count(), 0)

    def test_condition_lost_writes_off_drone_and_creates_record(self):
        self.client.force_authenticate(self.admin)

        response = self.client.patch(
            self.url,
            {"condition_after": "lost", "condition_description": "Lost over water."},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.drone.refresh_from_db()

        self.assertEqual(self.drone.status, "WRITTEN_OFF")
        writeoff = WriteOffRecord.objects.get(drone=self.drone)
        self.assertEqual(writeoff.reason, "LOSS")
        self.assertEqual(writeoff.related_mission, self.mission)
        self.assertEqual(writeoff.reason, WriteOffRecord.Reason.LOSS)
        self.assertIn("lost", writeoff.reason_description.lower())

        history = DroneStatusHistory.objects.get(drone=self.drone)
        self.assertEqual(history.from_status, "ACTIVE")
        self.assertEqual(history.to_status, "WRITTEN_OFF")
        self.assertEqual(history.related_writeoff, writeoff)
        self.assertEqual(history.related_mission, self.mission)

    def test_assigned_operator_can_record_condition(self):
        self.client.force_authenticate(self.operator)

        response = self.client.patch(
            self.url,
            {"condition_after": "ok"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_unassigned_operator_forbidden(self):
        self.client.force_authenticate(self.other_operator)

        response = self.client.patch(
            self.url,
            {"condition_after": "ok"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_viewer_forbidden(self):
        self.client.force_authenticate(self.viewer)

        response = self.client.patch(
            self.url,
            {"condition_after": "ok"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_unauthenticated_request_rejected(self):
        response = self.client.patch(
            self.url,
            {"condition_after": "ok"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_condition_rejected_on_planned_mission(self):
        self.mission.status = "planned"
        self.mission.save(update_fields=["status"])

        self.client.force_authenticate(self.admin)

        response = self.client.patch(
            self.url,
            {"condition_after": "ok"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_condition_allowed_on_aborted_mission(self):
        self.mission.status = "aborted"
        self.mission.save(update_fields=["status"])

        self.client.force_authenticate(self.admin)

        response = self.client.patch(
            self.url,
            {"condition_after": "damaged"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_invalid_condition_value_rejected(self):
        self.client.force_authenticate(self.admin)

        response = self.client.patch(
            self.url,
            {"condition_after": "broken"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("condition_after", response.data)

    def test_assignment_from_other_mission_returns_404(self):
        other_mission = MissionFactory(status="completed")
        other_assignment = MissionDroneFactory(mission=other_mission)

        wrong_url = reverse(
            "missions:mission-drone-condition",
            kwargs={
                "pk": self.mission.pk,
                "assignment_id": other_assignment.pk,
            },
        )

        self.client.force_authenticate(self.admin)

        response = self.client.patch(
            wrong_url,
            {"condition_after": "ok"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_condition_creates_audit_log(self):
        self.client.force_authenticate(self.admin)

        self.client.patch(
            self.url,
            {"condition_after": "damaged", "condition_description": "Bent rotor"},
            format="json",
        )

        log = MissionAuditLog.objects.get(action="drone_condition_recorded")

        self.assertEqual(log.target_model, "MissionDrone")
        self.assertEqual(log.user, self.admin)
        self.assertEqual(log.changes["assignment_id"], self.assignment.id)
        self.assertEqual(log.changes["mission_id"], self.mission.id)
        self.assertEqual(log.changes["drone_id"], self.drone.id)
        self.assertIsNone(log.changes["previous_condition"])
        self.assertEqual(log.changes["new_condition"], "damaged")
        self.assertEqual(log.changes["previous_drone_status"], "ACTIVE")
        self.assertEqual(log.changes["new_drone_status"], "DAMAGED")


class MissionStatusLifecycleTests(APITestCase):
    def setUp(self):
        self.admin = AdminUserFactory()
        self.operator = OperatorUserFactory()

        self.mission = MissionFactory(status="planned")
        self.drone = DroneFactory(status=Drone.STATUS_ACTIVE)

        MissionDroneFactory(
            mission=self.mission,
            drone=self.drone,
            operator=self.operator,
        )

        self.url = reverse(
            "missions:mission-status-update",
            kwargs={"pk": self.mission.pk},
        )

    def test_starting_mission_marks_assigned_drone_as_in_mission(self):
        self.client.force_authenticate(self.admin)

        response = self.client.patch(
            self.url,
            {"status": "active"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.mission.refresh_from_db()
        self.drone.refresh_from_db()

        self.assertEqual(self.mission.status, "active")
        self.assertEqual(self.drone.status, Drone.STATUS_IN_MISSION)

        history = DroneStatusHistory.objects.get(drone=self.drone)

        self.assertEqual(history.from_status, Drone.STATUS_ACTIVE)
        self.assertEqual(history.to_status, Drone.STATUS_IN_MISSION)
        self.assertEqual(history.reason, "Mission started")
        self.assertEqual(history.related_mission, self.mission)
        self.assertEqual(history.changed_by, self.admin)

    def test_completing_mission_returns_in_mission_drone_to_active(self):
        self.mission.status = "active"
        self.mission.save(update_fields=["status"])

        self.drone.status = Drone.STATUS_IN_MISSION
        self.drone.save(update_fields=["status"])

        self.client.force_authenticate(self.admin)

        response = self.client.patch(
            self.url,
            {"status": "completed"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.mission.refresh_from_db()
        self.drone.refresh_from_db()

        self.assertEqual(self.mission.status, "completed")
        self.assertEqual(self.drone.status, Drone.STATUS_ACTIVE)

        history = DroneStatusHistory.objects.get(drone=self.drone)

        self.assertEqual(history.from_status, Drone.STATUS_IN_MISSION)
        self.assertEqual(history.to_status, Drone.STATUS_ACTIVE)
        self.assertEqual(history.reason, "Mission finished")
        self.assertEqual(history.related_mission, self.mission)

    def test_finishing_mission_does_not_overwrite_damaged_drone_status(self):
        self.mission.status = "active"
        self.mission.save(update_fields=["status"])

        self.drone.status = Drone.STATUS_DAMAGED
        self.drone.save(update_fields=["status"])

        self.client.force_authenticate(self.admin)

        response = self.client.patch(
            self.url,
            {"status": "completed"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.mission.refresh_from_db()
        self.drone.refresh_from_db()

        self.assertEqual(self.mission.status, "completed")
        self.assertEqual(self.drone.status, Drone.STATUS_DAMAGED)
        self.assertEqual(
            DroneStatusHistory.objects.filter(drone=self.drone).count(),
            0,
        )

    def test_cannot_start_mission_with_non_active_assigned_drone(self):
        self.drone.status = Drone.STATUS_MAINTENANCE
        self.drone.save(update_fields=["status"])

        self.client.force_authenticate(self.admin)

        response = self.client.patch(
            self.url,
            {"status": "active"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.mission.refresh_from_db()
        self.drone.refresh_from_db()

        self.assertEqual(self.mission.status, "planned")
        self.assertEqual(self.drone.status, Drone.STATUS_MAINTENANCE)
        self.assertEqual(
            DroneStatusHistory.objects.filter(drone=self.drone).count(),
            0,
        )


class MissionOutcomeFactoryIntegrityTests(APITestCase):
    """Sanity checks that the factories produce DB-valid objects so other
    tests above are trustworthy."""

    def test_factories_create_records(self):
        assignment = MissionDroneFactory()

        self.assertEqual(Mission.objects.count(), 1)
        self.assertEqual(MissionDrone.objects.count(), 1)
        self.assertIsNotNone(assignment.operator.role)
        self.assertEqual(assignment.operator.role.code, "OPERATOR")


def _future_datetime(hours=1):
    return timezone.now() + timedelta(hours=hours)


def _create_technician_user():
    technician_role, _ = Role.objects.get_or_create(
        code=TECHNICIAN_CODE,
        defaults={"name": "Technician"},
    )
    return User.objects.create_user(
        username="technician_user",
        email="technician_user@example.com",
        password="password",
        role=technician_role,
    )


def _create_user_without_role():
    return User.objects.create_user(
        username="user_without_role",
        email="user_without_role@example.com",
        password="password",
    )


class MissionCreateTests(APITestCase):
    """POST /api/missions/ — create endpoint, validation, permissions."""

    def setUp(self):
        self.dispatcher = DispatcherUserFactory()
        self.admin = AdminUserFactory()
        self.operator = OperatorUserFactory()
        self.viewer = ViewerUserFactory()
        self.commander = CommanderUserFactory()

        self.url = reverse("missions:mission-list-create")

        self.valid_payload = {
            "title": "Recon Sweep",
            "started_at": _future_datetime(2).isoformat(),
            "location_description": "Sector 7",
        }

    def test_dispatcher_can_create_mission(self):
        self.client.force_authenticate(self.dispatcher)

        response = self.client.post(self.url, self.valid_payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Mission.objects.count(), 1)

        mission = Mission.objects.get()
        self.assertEqual(mission.title, "Recon Sweep")
        self.assertEqual(mission.location_description, "Sector 7")
        self.assertEqual(mission.created_by, self.dispatcher)
        self.assertEqual(mission.status, "planned")

    def test_admin_can_create_mission(self):
        self.client.force_authenticate(self.admin)

        response = self.client.post(self.url, self.valid_payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Mission.objects.get().created_by, self.admin)

    def test_create_with_coordinates_only(self):
        self.client.force_authenticate(self.dispatcher)

        payload = {
            "title": "Coord Mission",
            "started_at": _future_datetime(2).isoformat(),
            "latitude": "50.450001",
            "longitude": "30.523333",
        }

        response = self.client.post(self.url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        mission = Mission.objects.get()
        self.assertEqual(str(mission.latitude), "50.450001")
        self.assertEqual(str(mission.longitude), "30.523333")

    def test_create_with_commander_id(self):
        self.client.force_authenticate(self.dispatcher)

        payload = {**self.valid_payload, "commander_id": self.commander.id}

        response = self.client.post(self.url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Mission.objects.get().commander, self.commander)

    def test_commander_id_must_be_commander_role(self):
        self.client.force_authenticate(self.dispatcher)

        payload = {**self.valid_payload, "commander_id": self.viewer.id}

        response = self.client.post(self.url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("commander_id", response.data)

    def test_operator_cannot_create(self):
        self.client.force_authenticate(self.operator)

        response = self.client.post(self.url, self.valid_payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(Mission.objects.count(), 0)

    def test_viewer_cannot_create(self):
        self.client.force_authenticate(self.viewer)

        response = self.client.post(self.url, self.valid_payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_commander_cannot_create(self):
        self.client.force_authenticate(self.commander)

        response = self.client.post(self.url, self.valid_payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_unauthenticated_cannot_create(self):
        response = self.client.post(self.url, self.valid_payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_missing_title_rejected(self):
        self.client.force_authenticate(self.dispatcher)

        payload = {
            key: val for key, val in self.valid_payload.items() if key != "title"
        }

        response = self.client.post(self.url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("title", response.data)

    def test_blank_title_rejected(self):
        self.client.force_authenticate(self.dispatcher)

        payload = {**self.valid_payload, "title": "   "}

        response = self.client.post(self.url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("title", response.data)

    def test_short_title_rejected(self):
        self.client.force_authenticate(self.dispatcher)

        payload = {**self.valid_payload, "title": "ab"}

        response = self.client.post(self.url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("title", response.data)

    def test_missing_location_and_coordinates_rejected(self):
        self.client.force_authenticate(self.dispatcher)

        payload = {
            "title": "No Location Mission",
            "started_at": _future_datetime(2).isoformat(),
        }

        response = self.client.post(self.url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_latitude_without_longitude_rejected(self):
        self.client.force_authenticate(self.dispatcher)

        payload = {
            "title": "Half Coords",
            "started_at": _future_datetime(2).isoformat(),
            "latitude": "50.0",
        }

        response = self.client.post(self.url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_started_at_in_past_rejected(self):
        self.client.force_authenticate(self.dispatcher)

        payload = {
            **self.valid_payload,
            "started_at": (timezone.now() - timedelta(days=1)).isoformat(),
        }

        response = self.client.post(self.url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("started_at", response.data)

    def test_status_field_is_read_only_on_create(self):
        self.client.force_authenticate(self.dispatcher)

        payload = {**self.valid_payload, "status": "active"}

        response = self.client.post(self.url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Mission.objects.get().status, "planned")


class MissionAssignmentAccessTests(APITestCase):
    def setUp(self):
        self.dispatcher = DispatcherUserFactory()
        self.viewer = ViewerUserFactory()
        self.mission = MissionFactory()
        MissionDroneFactory(mission=self.mission)
        self.url = reverse(
            "missions:mission-assignment-list-create",
            kwargs={"mission_pk": self.mission.pk},
        )

    def test_dispatcher_can_list_assignments(self):
        self.client.force_authenticate(self.dispatcher)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_viewer_cannot_list_assignments(self):
        self.client.force_authenticate(self.viewer)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class MissionListTests(APITestCase):
    """GET /api/missions/ — list, status filter, pagination."""

    def setUp(self):
        self.commander = CommanderUserFactory()
        self.dispatcher = DispatcherUserFactory()
        self.operator = OperatorUserFactory()
        self.viewer = ViewerUserFactory()
        self.technician = _create_technician_user()
        self.user_without_role = _create_user_without_role()

        self.url = reverse("missions:mission-list-create")

    def test_unauthenticated_cannot_list(self):
        MissionFactory()

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_dispatcher_can_list_all_missions(self):
        MissionFactory()
        MissionFactory()

        self.client.force_authenticate(self.dispatcher)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 2)

    def test_commander_can_list_all_missions(self):
        MissionFactory()
        MissionFactory()

        self.client.force_authenticate(self.commander)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 2)

    def test_operator_only_sees_assigned_missions(self):
        assigned_mission = MissionFactory()
        other_mission = MissionFactory()
        MissionDroneFactory(mission=assigned_mission, operator=self.operator)
        MissionDroneFactory(mission=other_mission)

        self.client.force_authenticate(self.operator)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(response.data["results"][0]["id"], assigned_mission.id)

    def test_viewer_cannot_list_missions(self):
        MissionFactory()

        self.client.force_authenticate(self.viewer)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_filter_by_status(self):
        MissionFactory(status="planned")
        MissionFactory(status="planned")
        MissionFactory(status="completed")

        self.client.force_authenticate(self.dispatcher)

        response = self.client.get(self.url, {"status": "completed"})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(response.data["results"][0]["status"], "completed")

    def test_invalid_status_filter_rejected(self):
        self.client.force_authenticate(self.dispatcher)

        response = self.client.get(self.url, {"status": "bogus"})

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("status", response.data)

    def test_pagination_default_page_size(self):
        for _ in range(12):
            MissionFactory()

        self.client.force_authenticate(self.dispatcher)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 12)
        self.assertEqual(len(response.data["results"]), 10)
        self.assertIsNotNone(response.data["next"])

    def test_pagination_second_page(self):
        for _ in range(12):
            MissionFactory()

        self.client.force_authenticate(self.dispatcher)

        response = self.client.get(self.url, {"page": 2})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 2)
        self.assertIsNone(response.data["next"])

    def test_pagination_custom_page_size(self):
        for _ in range(7):
            MissionFactory()

        self.client.force_authenticate(self.dispatcher)

        response = self.client.get(self.url, {"page_size": 3})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 3)

    def test_pagination_page_size_capped_at_max(self):
        for _ in range(3):
            MissionFactory()

        self.client.force_authenticate(self.dispatcher)

        response = self.client.get(self.url, {"page_size": 500})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 3)

    def test_filter_assigned_to_me(self):
        operator = OperatorUserFactory()

        mission_assigned = MissionFactory()
        MissionDroneFactory(mission=mission_assigned, operator=operator)
        MissionDroneFactory(mission=mission_assigned, operator=operator)

        mission_not_assigned = MissionFactory()
        MissionDroneFactory(mission=mission_not_assigned)

        self.client.force_authenticate(operator)

        response = self.client.get(self.url, {"assigned_to": "me"})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(response.data["results"][0]["id"], mission_assigned.id)

    def test_invalid_assigned_to_filter_rejected(self):
        self.client.force_authenticate(self.dispatcher)

        response = self.client.get(self.url, {"assigned_to": "other_user"})

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("assigned_to", response.data)

    def test_mission_list_avoids_n_plus_one_queries(self):
        self.client.force_authenticate(self.dispatcher)

        for _ in range(5):
            mission = MissionFactory()
            MissionDroneFactory.create_batch(3, mission=mission)

        with CaptureQueriesContext(connection) as queries:
            response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertLess(
            len(queries), 8, "Виявлено проблему N+1 запитів у MissionListCreateView!"
        )

    def test_technician_without_missions_view_cannot_list(self):
        MissionFactory()
        self.client.force_authenticate(self.technician)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_user_without_role_cannot_list(self):
        MissionFactory()
        self.client.force_authenticate(self.user_without_role)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class MissionDetailTests(APITestCase):
    """GET /api/missions/{id}/ — retrieve detail."""

    def setUp(self):
        self.dispatcher = DispatcherUserFactory()
        self.operator = OperatorUserFactory()
        self.other_operator = OperatorUserFactory()
        self.viewer = ViewerUserFactory()
        self.mission = MissionFactory(title="Detail Mission")
        self.technician = _create_technician_user()
        self.user_without_role = _create_user_without_role()
        self.assignment = MissionDroneFactory(
            mission=self.mission,
            operator=self.operator,
        )

        self.url = reverse(
            "missions:mission-detail",
            kwargs={"pk": self.mission.pk},
        )

    def test_unauthenticated_cannot_retrieve(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_dispatcher_can_retrieve(self):
        self.client.force_authenticate(self.dispatcher)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["id"], self.mission.pk)
        self.assertEqual(response.data["title"], "Detail Mission")

    def test_assigned_operator_can_retrieve(self):
        self.client.force_authenticate(self.operator)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["id"], self.mission.pk)

    def test_unassigned_operator_gets_404(self):
        self.client.force_authenticate(self.other_operator)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_viewer_cannot_retrieve(self):
        self.client.force_authenticate(self.viewer)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_nonexistent_mission_returns_404(self):
        self.client.force_authenticate(self.dispatcher)

        url = reverse("missions:mission-detail", kwargs={"pk": 99999})

        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_technician_without_missions_view_cannot_retrieve(self):
        self.client.force_authenticate(self.technician)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_user_without_role_cannot_retrieve(self):
        self.client.force_authenticate(self.user_without_role)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class MissionAssignmentListCreatePermissionTests(APITestCase):
    def setUp(self):
        self.admin = AdminUserFactory()
        self.dispatcher = DispatcherUserFactory()
        self.viewer = ViewerUserFactory()
        self.operator = OperatorUserFactory()
        self.mission = MissionFactory()
        self.drone = DroneFactory(status=Drone.STATUS_ACTIVE)

        self.url = reverse(
            "missions:mission-assignment-list-create",
            kwargs={"mission_pk": self.mission.pk},
        )

    def test_viewer_cannot_list_assignments_without_missions_view(self):
        MissionDroneFactory(
            mission=self.mission,
            drone=self.drone,
            operator=self.operator,
        )

        self.client.force_authenticate(self.viewer)
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_viewer_cannot_create_assignment_with_only_missions_view(self):
        self.client.force_authenticate(self.viewer)

        response = self.client.post(
            self.url,
            {
                "drone": self.drone.id,
                "operator": self.operator.id,
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(MissionDrone.objects.count(), 0)

    def test_dispatcher_can_create_assignment(self):
        self.client.force_authenticate(self.dispatcher)

        response = self.client.post(
            self.url,
            {
                "drone": self.drone.id,
                "operator": self.operator.id,
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(MissionDrone.objects.count(), 1)
        
    def test_operator_cannot_list_assignments_for_unassigned_mission(self):
        MissionDroneFactory(
            mission=self.mission,
            drone=self.drone,
        )

        self.client.force_authenticate(self.operator)
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class MissionAssignmentConcurrencyTests(TransactionTestCase):
    def setUp(self):
        self.operator = OperatorUserFactory()
        self.drone = DroneFactory(status=Drone.STATUS_ACTIVE)

        now = timezone.now()

        self.mission_1 = MissionFactory(
            status="planned", started_at=now, ended_at=now + timedelta(hours=2)
        )
        self.mission_2 = MissionFactory(
            status="planned",
            started_at=now + timedelta(hours=1),
            ended_at=now + timedelta(hours=3),
        )

    def test_concurrent_assignment_race_condition(self):

        exceptions = []
        results = []

        def worker_assign(mission, drone, operator):
            connection.close()
            try:
                result = assign_drone_to_mission(
                    mission=mission,
                    drone=drone,
                    operator=operator,
                )
                results.append(result)
            except Exception as e:
                exceptions.append(e)
            finally:
                connection.close()

        thread1 = threading.Thread(
            target=worker_assign, args=(self.mission_1, self.drone, self.operator)
        )
        thread2 = threading.Thread(
            target=worker_assign, args=(self.mission_2, self.drone, self.operator)
        )

        thread1.start()
        thread2.start()

        thread1.join()
        thread2.join()

        self.assertEqual(
            len(results),
            1,
            "Race Condition! The drone is assigned to both missions at the same time!",
        )
        self.assertEqual(len(exceptions), 1)
        self.assertIsInstance(exceptions[0], ValidationError)

