from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from drones.models import DroneStatusHistory, WriteOffRecord

from .factories import (
    AdminUserFactory,
    DroneFactory,
    MissionDroneFactory,
    MissionFactory,
    OperatorUserFactory,
    ViewerUserFactory,
)
from .models import AuditLog, Mission, MissionDrone


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
            {"result": "failure", "notes": "Failed extraction."},
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
            {"result": "failure"},
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

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

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

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

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

        log = AuditLog.objects.get(action="mission_outcome_recorded")

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
        self.assertEqual(writeoff.related_mission, self.mission)
        self.assertIn("lost", writeoff.reason.lower())

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

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

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

        log = AuditLog.objects.get(action="drone_condition_recorded")

        self.assertEqual(log.target_model, "MissionDrone")
        self.assertEqual(log.user, self.admin)
        self.assertEqual(log.changes["assignment_id"], self.assignment.id)
        self.assertEqual(log.changes["mission_id"], self.mission.id)
        self.assertEqual(log.changes["drone_id"], self.drone.id)
        self.assertIsNone(log.changes["previous_condition"])
        self.assertEqual(log.changes["new_condition"], "damaged")
        self.assertEqual(log.changes["previous_drone_status"], "ACTIVE")
        self.assertEqual(log.changes["new_drone_status"], "DAMAGED")


class MissionOutcomeFactoryIntegrityTests(APITestCase):
    """Sanity checks that the factories produce DB-valid objects so other
    tests above are trustworthy."""

    def test_factories_create_records(self):
        assignment = MissionDroneFactory()

        self.assertEqual(Mission.objects.count(), 1)
        self.assertEqual(MissionDrone.objects.count(), 1)
        self.assertIsNotNone(assignment.operator.role)
        self.assertEqual(assignment.operator.role.code, "OPERATOR")
