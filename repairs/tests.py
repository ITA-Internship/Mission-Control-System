"""
Test repair operations including defect reporting, component replacements,
repair orders, role-based access control, timelines, and CSV exports.
"""

import csv
import datetime
import io
from unittest.mock import patch

from django.contrib.auth.models import AnonymousUser
from django.core import mail
from django.core.exceptions import ValidationError
from django.db.models import ProtectedError
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from common.pagination import StandardResultsSetPagination
from drones.factories import ViewerUserFactory
from roles.models import COMMANDER_CODE, TECHNICIAN_CODE, VIEWER_CODE, Role

from .factories import (
    AdminUserFactory,
    ComponentReplacementFactory,
    DefectReportFactory,
    DroneFactory,
    RepairOrderFactory,
)
from .models import (
    ComponentReplacement,
    ComponentType,
    DefectReport,
    DefectType,
    RepairEvent,
    RepairOrder,
    RepairOrderStatus,
    RepairStatus,
    Severity,
)
from .services import (
    create_component_replacement,
    create_defect_report,
    create_repair_order,
    get_drone_repair_history,
    update_repair_order_status,
)


def _base_payload(drone):
    """Return a valid base payload for creating a defect report."""
    return {
        "drone": drone.id,
        "defect_type": DefectType.MOTOR,
        "severity": Severity.HIGH,
        "description": "Rear-left motor stutters under load and overheats.",
        "detected_at": "2026-06-03T14:30:00Z",
    }


def _replacement_payload(drone):
    """Return a valid base payload for creating a component replacement."""
    return {
        "drone": drone.id,
        "component_type": ComponentType.MOTOR,
        "old_serial_number": "MOTOR-OLD-001",
        "new_serial_number": "MOTOR-NEW-001",
        "reason": "Motor replaced after vibration and overheating.",
        "replaced_at": "2026-06-10T11:00:00Z",
    }


def _repair_order_payload(drone, defect=None):
    """Return a valid base payload for creating a repair order."""
    payload = {
        "drone": drone.id,
        "description": "Replaced damaged motor after mission impact.",
    }
    if defect:
        payload["defect_report"] = defect.id
    return payload


class DefectReportCreateTests(APITestCase):
    """Verify defect report creation and automatic field population."""

    def setUp(self):
        """Prepare the test client, user, and drone for defect creation."""
        self.url = reverse("repairs:defect-create")
        self.drone = DroneFactory()
        self.user = AdminUserFactory()
        self.client.force_authenticate(self.user)

    def test_create_defect_report(self):
        """
        Verify that a defect report is successfully created with correct
        attributes.
        """
        response = self.client.post(self.url, _base_payload(self.drone), format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(DefectReport.objects.count(), 1)

        defect = DefectReport.objects.get()

        self.assertEqual(defect.drone, self.drone)
        self.assertEqual(defect.defect_type, DefectType.MOTOR)
        self.assertEqual(defect.severity, Severity.HIGH)
        self.assertEqual(defect.reporter, self.user)
        self.assertEqual(
            defect.detected_at,
            datetime.datetime(2026, 6, 3, 14, 30, tzinfo=datetime.timezone.utc),
        )

    def test_create_returns_full_representation(self):
        """
        Verify that the creation response returns the full serialized defect
        report.
        """
        response = self.client.post(self.url, _base_payload(self.drone), format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn("id", response.data)
        self.assertEqual(response.data["reporter"], self.user.id)
        self.assertIn("created_at", response.data)
        self.assertIn("updated_at", response.data)

    def test_description_is_trimmed(self):
        """
        Verify that leading and trailing whitespace is stripped from the
        description.
        """
        payload = _base_payload(self.drone)
        payload["description"] = "   Camera feed drops out intermittently.   "

        response = self.client.post(self.url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        defect = DefectReport.objects.get()
        self.assertEqual(defect.description, "Camera feed drops out intermittently.")

    def test_reporter_is_server_set_and_cannot_be_spoofed(self):
        """
        Verify that the reporter is securely inferred from the request,
        ignoring payload.
        """
        other_user = ViewerUserFactory()
        payload = _base_payload(self.drone)
        payload["reporter"] = other_user.id

        response = self.client.post(self.url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        defect = DefectReport.objects.get()
        self.assertEqual(defect.reporter, self.user)
        self.assertNotEqual(defect.reporter, other_user)

    def test_create_accepts_recent_detected_at(self):
        """Verify that a recent detection timestamp is accepted."""
        payload = _base_payload(self.drone)
        payload["detected_at"] = timezone.now().isoformat()

        response = self.client.post(self.url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)


class DefectReportValidationTests(APITestCase):
    """Verify payload validation for defect report creation."""

    def setUp(self):
        """Prepare the test client, user, and drone for payload validation."""
        self.url = reverse("repairs:defect-create")
        self.drone = DroneFactory()
        self.user = AdminUserFactory()
        self.client.force_authenticate(self.user)

    def test_missing_required_fields(self):
        """Verify that missing required fields trigger validation errors."""
        for field in (
            "drone",
            "defect_type",
            "severity",
            "description",
            "detected_at",
        ):
            with self.subTest(field=field):
                payload = _base_payload(self.drone)
                payload.pop(field)

                response = self.client.post(self.url, payload, format="json")

                self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
                self.assertIn(field, response.data)

    def test_invalid_defect_type(self):
        """Verify that an invalid defect type is rejected."""
        payload = _base_payload(self.drone)
        payload["defect_type"] = "NOT_A_REAL_TYPE"

        response = self.client.post(self.url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("defect_type", response.data)

    def test_invalid_severity(self):
        """Verify that an invalid severity level is rejected."""
        payload = _base_payload(self.drone)
        payload["severity"] = "SUPER_CRITICAL"

        response = self.client.post(self.url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("severity", response.data)

    def test_blank_description(self):
        """Verify that a completely blank description is rejected."""
        payload = _base_payload(self.drone)
        payload["description"] = ""

        response = self.client.post(self.url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("description", response.data)

    def test_whitespace_only_description(self):
        """Verify that a whitespace-only description is rejected."""
        payload = _base_payload(self.drone)
        payload["description"] = "          "

        response = self.client.post(self.url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("description", response.data)

    def test_too_short_description(self):
        """Verify that a description below the minimum length is rejected."""
        payload = _base_payload(self.drone)
        payload["description"] = "broken"

        response = self.client.post(self.url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("description", response.data)

    def test_detected_at_in_the_future_is_rejected(self):
        """
        Verify that a detection time beyond the grace period in the future is
        rejected.
        """
        payload = _base_payload(self.drone)
        payload["detected_at"] = (
            timezone.now() + datetime.timedelta(hours=1)
        ).isoformat()

        response = self.client.post(self.url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("detected_at", response.data)

    def test_nonexistent_drone_is_rejected(self):
        """Verify that referencing a non-existent drone ID is rejected."""
        payload = _base_payload(self.drone)
        payload["drone"] = 9999999

        response = self.client.post(self.url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("drone", response.data)


class DefectReportAuthTests(APITestCase):
    """Verify RBAC permissions for viewing and creating defect reports."""

    def setUp(self):
        """Prepare models and URLs for defect authorization tests."""
        self.url = reverse("repairs:defect-create")
        self.drone = DroneFactory()
        self.defect = DefectReportFactory(drone=self.drone)
        self.detail_url = reverse(
            "repairs:defect-detail", kwargs={"pk": self.defect.pk}
        )

    def test_unauthenticated_cannot_list(self):
        """Verify that anonymous users cannot list defects."""
        response = self.client.get(self.url)

        self.assertIn(
            response.status_code,
            (status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN),
        )

    def test_unauthenticated_cannot_create(self):
        """Verify that anonymous users cannot create defects."""
        response = self.client.post(self.url, _base_payload(self.drone), format="json")

        self.assertIn(
            response.status_code,
            (status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN),
        )

    def test_role_without_create_permission_cannot_post(self):
        """Verify that users lacking repair creation permissions are blocked."""
        viewer = ViewerUserFactory()
        self.client.force_authenticate(viewer)

        response = self.client.post(self.url, _base_payload(self.drone), format="json")

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_role_without_create_permission_can_still_view(self):
        """
        Verify that users lacking create permissions can still view defects
        if authorized.
        """
        viewer = ViewerUserFactory()
        self.client.force_authenticate(viewer)

        list_response = self.client.get(self.url)
        detail_response = self.client.get(self.detail_url)

        self.assertEqual(list_response.status_code, status.HTTP_200_OK)
        self.assertEqual(detail_response.status_code, status.HTTP_200_OK)

    def test_role_without_view_permission_is_forbidden(self):
        """Verify that users without viewing permissions cannot access defects."""
        roleless_user = AdminUserFactory(role=None)
        self.client.force_authenticate(roleless_user)

        list_response = self.client.get(self.url)
        detail_response = self.client.get(self.detail_url)

        self.assertEqual(list_response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(detail_response.status_code, status.HTTP_403_FORBIDDEN)


class DefectReportListTests(APITestCase):
    """Verify defect report listing, filtering, pagination, and ordering."""

    def setUp(self):
        """Prepare multiple defects and authenticate a viewer user."""
        self.url = reverse("repairs:defect-create")
        self.user = ViewerUserFactory()
        self.client.force_authenticate(self.user)

        self.drone_a = DroneFactory()
        self.drone_b = DroneFactory()

        self.defect_a = DefectReportFactory(
            drone=self.drone_a,
            severity=Severity.HIGH,
            defect_type=DefectType.MOTOR,
            detected_at=datetime.datetime(
                2026, 6, 1, 10, 0, tzinfo=datetime.timezone.utc
            ),
        )
        self.defect_b = DefectReportFactory(
            drone=self.drone_b,
            severity=Severity.LOW,
            defect_type=DefectType.CAMERA,
            detected_at=datetime.datetime(
                2026, 6, 5, 10, 0, tzinfo=datetime.timezone.utc
            ),
        )

    def test_list_returns_paginated_envelope(self):
        """Verify that the list endpoint returns a paginated structure."""
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("count", response.data)
        self.assertIn("results", response.data)
        self.assertEqual(response.data["count"], 2)

    def test_filter_by_drone(self):
        """Verify that defects can be filtered by drone ID."""
        response = self.client.get(self.url, {"drone": self.drone_a.id})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        ids = [item["id"] for item in response.data["results"]]
        self.assertEqual(ids, [self.defect_a.id])

    def test_filter_by_severity(self):
        """Verify that defects can be filtered by severity level."""
        response = self.client.get(self.url, {"severity": Severity.LOW})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        ids = [item["id"] for item in response.data["results"]]
        self.assertEqual(ids, [self.defect_b.id])

    def test_filter_by_defect_type(self):
        """Verify that defects can be filtered by component defect type."""
        response = self.client.get(self.url, {"defect_type": DefectType.CAMERA})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        ids = [item["id"] for item in response.data["results"]]
        self.assertEqual(ids, [self.defect_b.id])

    def test_filter_by_reporter(self):
        """Verify that defects can be filtered by the reporting user ID."""
        response = self.client.get(self.url, {"reporter": self.defect_a.reporter_id})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        ids = [item["id"] for item in response.data["results"]]
        self.assertIn(self.defect_a.id, ids)

    def test_ordering_by_detected_at(self):
        """Verify that defects can be ordered explicitly by detection time."""
        response = self.client.get(self.url, {"ordering": "detected_at"})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        ids = [item["id"] for item in response.data["results"]]
        self.assertEqual(ids, [self.defect_a.id, self.defect_b.id])

    def test_default_ordering_is_most_recent_first(self):
        """Verify that defects are ordered by most recent detection time by default."""
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        ids = [item["id"] for item in response.data["results"]]
        self.assertEqual(ids, [self.defect_b.id, self.defect_a.id])

    def test_list_uses_slim_serializer(self):
        """Verify that list views return a reduced field set to save bandwidth."""
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        first = response.data["results"][0]
        self.assertNotIn("description", first)
        self.assertNotIn("updated_at", first)

    def test_list_pagination(self):
        """Verify that the list endpoint paginates properly when limits are exceeded."""
        page_size = StandardResultsSetPagination.page_size
        DefectReportFactory.create_batch(page_size, drone=self.drone_a)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], page_size + 2)
        self.assertEqual(len(response.data["results"]), page_size)
        self.assertIsNotNone(response.data["next"])


class DefectReportDetailTests(APITestCase):
    """Verify detailed retrieval and immutability of defect records."""

    def setUp(self):
        """Prepare an authenticated user and an existing defect report."""
        self.user = AdminUserFactory()
        self.client.force_authenticate(self.user)
        self.defect = DefectReportFactory()
        self.detail_url = reverse(
            "repairs:defect-detail", kwargs={"pk": self.defect.pk}
        )

    def test_retrieve_existing_defect(self):
        """Verify that an existing defect can be retrieved in full detail."""
        response = self.client.get(self.detail_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["id"], self.defect.id)
        self.assertEqual(response.data["description"], self.defect.description)

    def test_retrieve_unknown_defect_returns_404(self):
        """Verify that requesting a non-existent defect returns a 404."""
        url = reverse("repairs:defect-detail", kwargs={"pk": 9999999})

        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_update_is_not_allowed(self):
        """Verify that defect reports are immutable via standard DRF updates."""
        for method in ("put", "patch", "delete"):
            with self.subTest(method=method):
                response = getattr(self.client, method)(
                    self.detail_url, {}, format="json"
                )

                self.assertIn(
                    response.status_code,
                    (
                        status.HTTP_403_FORBIDDEN,
                        status.HTTP_405_METHOD_NOT_ALLOWED,
                    ),
                )


class DefectReportProtectTests(APITestCase):
    """Verify database-level deletion protection for drones with defects."""

    def test_drone_with_defects_cannot_be_deleted(self):
        """Verify that a drone cannot be deleted if it has associated defect reports."""
        defect = DefectReportFactory()

        with self.assertRaises(ProtectedError):
            defect.drone.delete()


class CreateDefectReportServiceTests(APITestCase):
    """Verify the business logic and side effects in the defect creation service."""

    def setUp(self):
        """Prepare dependencies for the defect service."""
        self.drone = DroneFactory()
        self.user = AdminUserFactory()

    def test_create_defect_report_happy_path(self):
        """Verify that the service layer successfully creates a valid defect."""
        detected_at = datetime.datetime(
            2026, 6, 3, 14, 30, tzinfo=datetime.timezone.utc
        )

        defect = create_defect_report(
            drone=self.drone,
            reporter=self.user,
            defect_type=DefectType.BATTERY,
            severity=Severity.CRITICAL,
            description="Battery swelling detected after landing.",
            detected_at=detected_at,
        )

        self.assertEqual(DefectReport.objects.count(), 1)
        self.assertEqual(defect.reporter, self.user)
        self.assertEqual(defect.drone, self.drone)
        self.assertEqual(defect.defect_type, DefectType.BATTERY)
        self.assertEqual(defect.severity, Severity.CRITICAL)
        self.assertEqual(defect.detected_at, detected_at)

    def test_anonymous_reporter_is_stored_as_null(self):
        """Verify that an AnonymousUser is safely stored as NULL in the database."""
        defect = create_defect_report(
            drone=self.drone,
            reporter=AnonymousUser(),
            defect_type=DefectType.OTHER,
            severity=Severity.LOW,
            description="Unclassified anomaly during pre-flight check.",
            detected_at=timezone.now(),
        )

        self.assertIsNone(defect.reporter)

    def test_none_reporter_is_stored_as_null(self):
        """Verify that providing None for a reporter is safely stored as NULL."""
        defect = create_defect_report(
            drone=self.drone,
            reporter=None,
            defect_type=DefectType.OTHER,
            severity=Severity.LOW,
            description="Unclassified anomaly during pre-flight check.",
            detected_at=timezone.now(),
        )

        self.assertIsNone(defect.reporter)


class DefectReportFactoryIntegrityTests(APITestCase):
    """Verify that the factory produces valid test data."""

    def test_factory_produces_valid_row(self):
        """Verify that the factory generates a database-valid defect report."""
        defect = DefectReportFactory()

        self.assertIsNotNone(defect.pk)
        self.assertEqual(DefectReport.objects.count(), 1)

        defect.full_clean()


class ComponentReplacementCreateTests(APITestCase):
    """Verify component replacement creation and field population."""

    def setUp(self):
        """Prepare the environment for component replacement tests."""
        self.url = reverse("repairs:replacement-list-create")
        self.drone = DroneFactory()
        self.user = AdminUserFactory()
        self.client.force_authenticate(self.user)

    def test_create_component_replacement(self):
        """Verify that a component replacement is created successfully."""
        response = self.client.post(
            self.url,
            _replacement_payload(self.drone),
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(ComponentReplacement.objects.count(), 1)

        replacement = ComponentReplacement.objects.get()
        self.assertEqual(replacement.drone, self.drone)
        self.assertEqual(replacement.component_type, ComponentType.MOTOR)
        self.assertEqual(replacement.old_serial_number, "MOTOR-OLD-001")
        self.assertEqual(replacement.new_serial_number, "MOTOR-NEW-001")
        self.assertEqual(replacement.replaced_by, self.user)

    def test_create_returns_full_representation(self):
        """
        Verify that creating a replacement returns the full serialized object.
        """
        response = self.client.post(
            self.url,
            _replacement_payload(self.drone),
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn("id", response.data)
        self.assertEqual(response.data["replaced_by"], self.user.id)
        self.assertIn("created_at", response.data)
        self.assertIn("updated_at", response.data)

    def test_reason_is_trimmed(self):
        """Verify that whitespace is trimmed from the replacement reason."""
        payload = _replacement_payload(self.drone)
        payload["reason"] = "   Replaced due to bent shaft and overheating.   "

        response = self.client.post(self.url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        replacement = ComponentReplacement.objects.get()
        self.assertEqual(
            replacement.reason,
            "Replaced due to bent shaft and overheating.",
        )

    def test_replaced_by_is_server_set_and_cannot_be_spoofed(self):
        """Verify that replaced_by is pulled securely from the request context."""
        other_user = ViewerUserFactory()
        payload = _replacement_payload(self.drone)
        payload["replaced_by"] = other_user.id

        response = self.client.post(self.url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        replacement = ComponentReplacement.objects.get()
        self.assertEqual(replacement.replaced_by, self.user)
        self.assertNotEqual(replacement.replaced_by, other_user)

    def test_other_component_requires_name(self):
        """Verify that 'OTHER' component types mandate a custom component name."""
        payload = _replacement_payload(self.drone)
        payload["component_type"] = ComponentType.OTHER

        response = self.client.post(self.url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("component_name", response.data)

    def test_other_component_accepts_custom_name(self):
        """Verify that 'OTHER' component types accept and save custom names."""
        payload = _replacement_payload(self.drone)
        payload["component_type"] = ComponentType.OTHER
        payload["component_name"] = "GPS antenna"

        response = self.client.post(self.url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        replacement = ComponentReplacement.objects.get()
        self.assertEqual(replacement.component_name, "GPS antenna")


class ComponentReplacementValidationTests(APITestCase):
    """Verify validation logic for component replacement payloads."""

    def setUp(self):
        """Prepare the environment for validation testing."""
        self.url = reverse("repairs:replacement-list-create")
        self.drone = DroneFactory()
        self.user = AdminUserFactory()
        self.client.force_authenticate(self.user)

    def test_missing_required_fields(self):
        """Verify that omitting required fields yields validation errors."""
        for field in (
            "drone",
            "component_type",
            "new_serial_number",
            "reason",
            "replaced_at",
        ):
            with self.subTest(field=field):
                payload = _replacement_payload(self.drone)
                payload.pop(field)

                response = self.client.post(self.url, payload, format="json")

                self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
                self.assertIn(field, response.data)

    def test_invalid_component_type(self):
        """Verify that invalid component types are rejected."""
        payload = _replacement_payload(self.drone)
        payload["component_type"] = "NOT_A_REAL_COMPONENT"

        response = self.client.post(self.url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("component_type", response.data)

    def test_blank_new_serial_number(self):
        """Verify that blank serial numbers are rejected."""
        payload = _replacement_payload(self.drone)
        payload["new_serial_number"] = "    "

        response = self.client.post(self.url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("new_serial_number", response.data)

    def test_blank_reason(self):
        """Verify that blank reasons are rejected."""
        payload = _replacement_payload(self.drone)
        payload["reason"] = "   "

        response = self.client.post(self.url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("reason", response.data)

    def test_replaced_at_in_the_future_is_rejected(self):
        """Verify that replacement dates in the future are rejected."""
        payload = _replacement_payload(self.drone)
        payload["replaced_at"] = (
            timezone.now() + datetime.timedelta(minutes=5)
        ).isoformat()

        response = self.client.post(self.url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("replaced_at", response.data)

    def test_nonexistent_drone_is_rejected(self):
        """Verify that pointing to a nonexistent drone ID fails."""
        payload = _replacement_payload(self.drone)
        payload["drone"] = 9999999

        response = self.client.post(self.url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("drone", response.data)

    def test_model_validation_with_missing_replaced_at_does_not_crash(self):
        """Verify that full_clean handles a missing replaced_at gracefully."""
        replacement = ComponentReplacement(
            drone=self.drone,
            component_type=ComponentType.MOTOR,
            old_serial_number="MOTOR-OLD-001",
            new_serial_number="MOTOR-NEW-001",
            reason="Motor replaced after vibration and overheating.",
            replaced_at=None,
            replaced_by=self.user,
        )

        with self.assertRaises(ValidationError) as exc_info:
            replacement.full_clean()

        self.assertIn("replaced_at", exc_info.exception.message_dict)


class ComponentReplacementAuthTests(APITestCase):
    """Verify RBAC permissions for component replacements."""

    def setUp(self):
        """Prepare authentication data and initial replacement records."""
        self.url = reverse("repairs:replacement-list-create")
        self.drone = DroneFactory()
        self.replacement = ComponentReplacementFactory(drone=self.drone)
        self.detail_url = reverse(
            "repairs:replacement-detail",
            kwargs={"pk": self.replacement.pk},
        )

    def test_unauthenticated_cannot_list(self):
        """Verify that anonymous users cannot list replacements."""
        response = self.client.get(self.url)

        self.assertIn(
            response.status_code,
            (status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN),
        )

    def test_unauthenticated_cannot_create(self):
        """Verify that anonymous users cannot create replacements."""
        response = self.client.post(
            self.url,
            _replacement_payload(self.drone),
            format="json",
        )

        self.assertIn(
            response.status_code,
            (status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN),
        )

    def test_role_without_create_permission_cannot_post(self):
        """Verify that viewers cannot post new replacement records."""
        viewer = ViewerUserFactory()
        self.client.force_authenticate(viewer)

        response = self.client.post(
            self.url,
            _replacement_payload(self.drone),
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_role_without_create_permission_can_still_view(self):
        """Verify that viewers can read replacement data."""
        viewer = ViewerUserFactory()
        self.client.force_authenticate(viewer)

        list_response = self.client.get(self.url)
        detail_response = self.client.get(self.detail_url)

        self.assertEqual(list_response.status_code, status.HTTP_200_OK)
        self.assertEqual(detail_response.status_code, status.HTTP_200_OK)


class ComponentReplacementListTests(APITestCase):
    """Verify component replacement listing, filtering, and pagination."""

    def setUp(self):
        """Prepare batch data for replacement list tests."""
        self.url = reverse("repairs:replacement-list-create")
        self.user = ViewerUserFactory()
        self.client.force_authenticate(self.user)

        self.drone_a = DroneFactory()
        self.drone_b = DroneFactory()
        self.reporter_a = AdminUserFactory()
        self.reporter_b = AdminUserFactory()

        self.replacement_a = ComponentReplacementFactory(
            drone=self.drone_a,
            component_type=ComponentType.MOTOR,
            replaced_by=self.reporter_a,
            replaced_at=datetime.datetime(
                2026, 6, 10, 11, 0, tzinfo=datetime.timezone.utc
            ),
        )
        self.replacement_b = ComponentReplacementFactory(
            drone=self.drone_b,
            component_type=ComponentType.BATTERY,
            replaced_by=self.reporter_b,
            new_serial_number="BATTERY-NEW-001",
            replaced_at=datetime.datetime(
                2026, 6, 12, 11, 0, tzinfo=datetime.timezone.utc
            ),
        )

    def test_list_returns_paginated_envelope(self):
        """Verify that the list endpoint returns a paginated structure."""
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("count", response.data)
        self.assertIn("results", response.data)
        self.assertEqual(response.data["count"], 2)

    def test_filter_by_drone(self):
        """Verify that replacements can be filtered by drone ID."""
        response = self.client.get(self.url, {"drone": self.drone_a.id})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        ids = [item["id"] for item in response.data["results"]]
        self.assertEqual(ids, [self.replacement_a.id])

    def test_filter_by_component_type(self):
        """Verify that replacements can be filtered by component type."""
        response = self.client.get(
            self.url,
            {"component_type": ComponentType.BATTERY},
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        ids = [item["id"] for item in response.data["results"]]
        self.assertEqual(ids, [self.replacement_b.id])

    def test_filter_by_replaced_by(self):
        """Verify that replacements can be filtered by the technician ID."""
        response = self.client.get(
            self.url,
            {"replaced_by": self.reporter_a.id},
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        ids = [item["id"] for item in response.data["results"]]
        self.assertEqual(ids, [self.replacement_a.id])

    def test_filter_by_date_range(self):
        """Verify that replacements can be filtered by a specific date range."""
        response = self.client.get(
            self.url,
            {
                "start_date": "2026-06-11T00:00:00Z",
                "end_date": "2026-06-13T00:00:00Z",
            },
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        ids = [item["id"] for item in response.data["results"]]
        self.assertEqual(ids, [self.replacement_b.id])

    def test_default_ordering_is_most_recent_first(self):
        """
        Verify that the default ordering returns the most recent replacements
        first.
        """
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        ids = [item["id"] for item in response.data["results"]]
        self.assertEqual(ids, [self.replacement_b.id, self.replacement_a.id])

    def test_list_uses_slim_serializer(self):
        """Verify that the list view uses a reduced payload to save bandwidth."""
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        first = response.data["results"][0]
        self.assertNotIn("old_serial_number", first)
        self.assertNotIn("reason", first)
        self.assertNotIn("updated_at", first)

    def test_list_pagination(self):
        """Verify that large datasets are paginated correctly."""
        page_size = StandardResultsSetPagination.page_size
        ComponentReplacementFactory.create_batch(page_size, drone=self.drone_a)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], page_size + 2)
        self.assertEqual(len(response.data["results"]), page_size)
        self.assertIsNotNone(response.data["next"])


class ComponentReplacementDetailTests(APITestCase):
    """Verify detailed retrieval and immutability of replacements."""

    def setUp(self):
        """Prepare authentication and replacement data."""
        self.user = AdminUserFactory()
        self.client.force_authenticate(self.user)
        self.replacement = ComponentReplacementFactory()
        self.detail_url = reverse(
            "repairs:replacement-detail",
            kwargs={"pk": self.replacement.pk},
        )

    def test_retrieve_existing_replacement(self):
        """Verify that a replacement can be retrieved in full detail."""
        response = self.client.get(self.detail_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["id"], self.replacement.id)
        self.assertEqual(
            response.data["old_serial_number"],
            self.replacement.old_serial_number,
        )
        self.assertEqual(response.data["reason"], self.replacement.reason)

    def test_retrieve_unknown_replacement_returns_404(self):
        """Verify that a 404 is returned for an unknown replacement ID."""
        url = reverse("repairs:replacement-detail", kwargs={"pk": 9999999})

        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_update_is_not_allowed(self):
        """Verify that component replacements are completely immutable."""
        for method in ("put", "patch", "delete"):
            with self.subTest(method=method):
                response = getattr(self.client, method)(
                    self.detail_url, {}, format="json"
                )

                self.assertIn(
                    response.status_code,
                    (
                        status.HTTP_403_FORBIDDEN,
                        status.HTTP_405_METHOD_NOT_ALLOWED,
                    ),
                )


class CreateComponentReplacementServiceTests(APITestCase):
    """Verify the business logic and side effects in the replacement service."""

    def setUp(self):
        """Prepare dependencies for the replacement service."""
        self.drone = DroneFactory()
        self.user = AdminUserFactory()

    def test_create_component_replacement_happy_path(self):
        """Verify that the service successfully creates a replacement record."""
        replaced_at = datetime.datetime(
            2026, 6, 10, 11, 0, tzinfo=datetime.timezone.utc
        )

        replacement = create_component_replacement(
            drone=self.drone,
            component_type=ComponentType.CAMERA,
            component_name="",
            old_serial_number="CAM-OLD-001",
            new_serial_number="CAM-NEW-001",
            reason="Camera replaced after image distortion.",
            replaced_at=replaced_at,
            replaced_by=self.user,
        )

        self.assertEqual(ComponentReplacement.objects.count(), 1)
        self.assertEqual(replacement.drone, self.drone)
        self.assertEqual(replacement.component_type, ComponentType.CAMERA)
        self.assertEqual(replacement.replaced_by, self.user)
        self.assertEqual(replacement.replaced_at, replaced_at)

    def test_anonymous_replaced_by_is_stored_as_null(self):
        """Verify that an AnonymousUser is safely stored as NULL."""
        replacement = create_component_replacement(
            drone=self.drone,
            component_type=ComponentType.OTHER,
            component_name="GPS antenna",
            old_serial_number="GPS-OLD-001",
            new_serial_number="GPS-NEW-001",
            reason="GPS antenna replaced after connector damage.",
            replaced_at=timezone.now(),
            replaced_by=AnonymousUser(),
        )

        self.assertIsNone(replacement.replaced_by)

    def test_future_replaced_at_is_rejected_on_service_layer(self):
        """
        Verify that the service layer explicitly enforces model validation
        to catch logic errors.
        """
        with self.assertRaises(ValidationError):
            create_component_replacement(
                drone=self.drone,
                component_type=ComponentType.CAMERA,
                component_name="",
                old_serial_number="CAM-OLD-001",
                new_serial_number="CAM-NEW-001",
                reason="Camera replaced after image distortion.",
                replaced_at=timezone.now() + datetime.timedelta(minutes=5),
                replaced_by=self.user,
            )

    def test_other_component_without_name_is_rejected_on_service_layer(self):
        """Verify that the service layer rejects 'OTHER' components lacking a name."""
        with self.assertRaises(ValidationError):
            create_component_replacement(
                drone=self.drone,
                component_type=ComponentType.OTHER,
                component_name="",
                old_serial_number="GPS-OLD-001",
                new_serial_number="GPS-NEW-001",
                reason="GPS antenna replaced after connector damage.",
                replaced_at=timezone.now(),
                replaced_by=self.user,
            )


class ComponentReplacementProtectTests(APITestCase):
    """Verify database-level deletion protection for drones with replacements."""

    def test_drone_with_replacements_cannot_be_deleted(self):
        """Verify that a drone cannot be deleted if it has replacement history."""
        replacement = ComponentReplacementFactory()

        with self.assertRaises(ProtectedError):
            replacement.drone.delete()


class ComponentReplacementExportTests(APITestCase):
    """Verify CSV streaming functionality for component replacements."""

    def setUp(self):
        self.export_url = reverse("repairs:replacement-export")
        self.admin_user = AdminUserFactory()
        self.replacement = ComponentReplacementFactory(reason="@cmd|'/C calc'!A0")

        self.client.force_authenticate(self.admin_user)

    def test_replacement_export_sanitized(self):
        response = self.client.get(self.export_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        content = b"".join(response.streaming_content).decode("utf-8")
        csv_reader = csv.reader(io.StringIO(content))
        rows = list(csv_reader)

        self.assertGreater(len(rows), 1)

        injected_value = next(val for val in rows[1] if "@cmd" in val)

        self.assertEqual(injected_value, "'@cmd|'/C calc'!A0")


class ComponentReplacementFactoryIntegrityTests(APITestCase):
    """Verify that the replacement factory produces valid test data."""

    def test_factory_produces_valid_row(self):
        """Verify that the factory generates a database-valid replacement."""
        replacement = ComponentReplacementFactory()

        self.assertIsNotNone(replacement.pk)
        self.assertEqual(ComponentReplacement.objects.count(), 1)

        replacement.full_clean()


class ComponentReplacementReportTests(APITestCase):
    """Verify CSV streaming functionality for component replacements."""

    def setUp(self):
        """Prepare authentication and replacement data for export."""
        self.url = reverse("repairs:replacement-export")
        self.user = ViewerUserFactory()
        self.client.force_authenticate(self.user)

        self.drone_a = DroneFactory(serial_number="DRONE-A-001")
        self.drone_b = DroneFactory(serial_number="DRONE-B-001")
        self.reporter_a = AdminUserFactory(username="tech.alpha")
        self.reporter_b = AdminUserFactory(username="tech.bravo")

        self.replacement_a = ComponentReplacementFactory(
            drone=self.drone_a,
            component_type=ComponentType.MOTOR,
            component_name="",
            old_serial_number="MOTOR-OLD-001",
            new_serial_number="MOTOR-NEW-001",
            replaced_by=self.reporter_a,
            replaced_at=datetime.datetime(
                2026, 6, 10, 11, 0, tzinfo=datetime.timezone.utc
            ),
        )
        self.replacement_b = ComponentReplacementFactory(
            drone=self.drone_b,
            component_type=ComponentType.BATTERY,
            component_name="Battery Pack",
            old_serial_number="BAT-OLD-001",
            new_serial_number="BAT-NEW-001",
            replaced_by=self.reporter_b,
            replaced_at=datetime.datetime(
                2026, 6, 12, 11, 0, tzinfo=datetime.timezone.utc
            ),
        )

    def _decode_rows(self, response):
        """Extract and return rows from a streaming CSV response."""
        content = b"".join(response.streaming_content).decode("utf-8")
        return [row for row in content.strip().splitlines() if row]

    def test_report_returns_csv_response(self):
        """Verify that the export endpoint correctly returns a CSV content type."""
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response["Content-Type"], "text/csv")
        self.assertIn("component_replacements.csv", response["Content-Disposition"])

    def test_report_returns_correct_replacement_records(self):
        """Verify that the CSV report contains the expected data rows."""
        response = self.client.get(self.url)
        rows = self._decode_rows(response)

        self.assertEqual(len(rows), 3)
        self.assertIn("Drone Serial Number", rows[0])
        joined_rows = "\n".join(rows[1:])
        self.assertIn("DRONE-A-001", joined_rows)
        self.assertIn("MOTOR-NEW-001", joined_rows)
        self.assertIn("tech.alpha", joined_rows)
        self.assertIn("DRONE-B-001", joined_rows)
        self.assertIn("BAT-NEW-001", joined_rows)
        self.assertIn("tech.bravo", joined_rows)

    def test_report_filters_by_drone(self):
        """Verify that the CSV export can be filtered by drone ID."""
        response = self.client.get(self.url, {"drone": self.drone_a.id})
        rows = self._decode_rows(response)

        self.assertEqual(len(rows), 2)
        self.assertIn("DRONE-A-001", rows[1])
        self.assertNotIn("DRONE-B-001", "\n".join(rows))

    def test_report_filters_by_component_type(self):
        """Verify that the CSV export can be filtered by component type."""
        response = self.client.get(
            self.url,
            {"component_type": ComponentType.BATTERY},
        )
        rows = self._decode_rows(response)

        self.assertEqual(len(rows), 2)
        self.assertIn("BATTERY", rows[1])
        self.assertNotIn("MOTOR", "\n".join(rows[1:]))

    def test_report_filters_by_user(self):
        """Verify that the CSV export can be filtered by technician."""
        response = self.client.get(
            self.url,
            {"replaced_by": self.reporter_a.id},
        )
        rows = self._decode_rows(response)

        self.assertEqual(len(rows), 2)
        self.assertIn("tech.alpha", rows[1])
        self.assertNotIn("tech.bravo", "\n".join(rows))

    def test_report_filters_by_date_range(self):
        """Verify that the CSV export can be filtered by a date range."""
        response = self.client.get(
            self.url,
            {
                "start_date": "2026-06-11T00:00:00Z",
                "end_date": "2026-06-13T00:00:00Z",
            },
        )
        rows = self._decode_rows(response)

        self.assertEqual(len(rows), 2)
        self.assertIn("DRONE-B-001", rows[1])
        self.assertNotIn("DRONE-A-001", "\n".join(rows))

    def test_unauthenticated_user_cannot_export_report(self):
        """Verify that anonymous users cannot download the CSV export."""
        self.client.force_authenticate(None)

        response = self.client.get(self.url)

        self.assertIn(
            response.status_code,
            (status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN),
        )


class RepairOrderCreateTests(APITestCase):
    """Verify repair order creation and related validation."""

    def setUp(self):
        """Prepare authentication and initial drone data."""
        self.url = reverse("repairs:repair-order-list")
        self.drone = DroneFactory()
        self.user = AdminUserFactory()
        self.client.force_authenticate(self.user)

    def test_create_repair_order(self):
        """Verify that a repair order is created successfully."""
        response = self.client.post(
            self.url,
            _repair_order_payload(self.drone),
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(RepairOrder.objects.count(), 1)

        order = RepairOrder.objects.get()
        self.assertEqual(order.drone, self.drone)
        self.assertEqual(order.status, RepairOrderStatus.PENDING)
        self.assertEqual(order.created_by, self.user)

    def test_create_with_defect_report(self):
        """
        Verify that a repair order can optionally link to an existing defect
        report.
        """
        defect = DefectReportFactory(drone=self.drone)
        response = self.client.post(
            self.url,
            _repair_order_payload(self.drone, defect),
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        order = RepairOrder.objects.get()
        self.assertEqual(order.defect_report, defect)

    def test_short_description_rejected(self):
        """Verify that descriptions failing minimum length requirements are rejected."""
        payload = _repair_order_payload(self.drone)
        payload["description"] = "short"

        response = self.client.post(self.url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_viewer_cannot_create(self):
        """Verify that users without creation permissions are blocked."""
        viewer = ViewerUserFactory()
        self.client.force_authenticate(viewer)

        response = self.client.post(
            self.url,
            _repair_order_payload(self.drone),
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_staff_without_manage_permission_cannot_create(self):
        """Verify that Django staff status alone
        does not grant repair order creation."""
        staff_viewer = ViewerUserFactory()
        staff_viewer.is_staff = True
        staff_viewer.save(update_fields=["is_staff"])
        self.client.force_authenticate(staff_viewer)

        response = self.client.post(
            self.url,
            _repair_order_payload(self.drone),
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class RepairOrderListTests(APITestCase):
    """Verify repair order listing, filtering, and pagination."""

    def setUp(self):
        """Prepare the base URL and authenticate an administrator."""
        self.url = reverse("repairs:repair-order-list")
        self.user = AdminUserFactory()
        self.client.force_authenticate(self.user)
        self.drone = DroneFactory()

    def test_list_returns_paginated_results(self):
        """Verify that listing repair orders returns a paginated structure."""
        RepairOrderFactory(drone=self.drone)
        RepairOrderFactory(drone=self.drone)

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 2)

    def test_filter_by_drone(self):
        """Verify that repair orders can be filtered by drone ID."""
        RepairOrderFactory(drone=self.drone)
        other_drone = DroneFactory()
        RepairOrderFactory(drone=other_drone)

        response = self.client.get(self.url, {"drone": self.drone.id})
        self.assertEqual(response.data["count"], 1)

    def test_filter_by_status(self):
        """Verify that repair orders can be filtered by current status."""
        RepairOrderFactory(drone=self.drone, status=RepairOrderStatus.PENDING)
        RepairOrderFactory(drone=self.drone, status=RepairOrderStatus.COMPLETED)

        response = self.client.get(self.url, {"status": RepairOrderStatus.PENDING})
        self.assertEqual(response.data["count"], 1)


class RepairOrderDetailTests(APITestCase):
    """Verify detailed retrieval of repair orders."""

    def setUp(self):
        """Prepare an authenticated user and an existing repair order."""
        self.user = AdminUserFactory()
        self.client.force_authenticate(self.user)
        self.order = RepairOrderFactory()
        self.detail_url = reverse(
            "repairs:repair-order-detail", kwargs={"pk": self.order.pk}
        )

    def test_retrieve_returns_order(self):
        """Verify that a specific repair order can be successfully retrieved."""
        response = self.client.get(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_retrieve_unknown_returns_404(self):
        """Verify that retrieving a non-existent repair order yields a 404."""
        url = reverse("repairs:repair-order-detail", kwargs={"pk": 9999999})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class RepairOrderStatusUpdateTests(APITestCase):
    """Verify repair order state machine transitions and RBAC."""

    def setUp(self):
        """Authenticate a user for state machine testing."""
        self.user = AdminUserFactory()
        self.client.force_authenticate(self.user)

    def test_transition_pending_to_in_progress(self):
        """Verify a valid state transition stamps the start time."""
        order = RepairOrderFactory(status=RepairOrderStatus.PENDING)
        url = reverse("repairs:repair-order-detail", kwargs={"pk": order.pk})

        response = self.client.patch(
            url,
            {"status": RepairOrderStatus.IN_PROGRESS},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        order.refresh_from_db()
        self.assertEqual(order.status, RepairOrderStatus.IN_PROGRESS)
        self.assertIsNotNone(order.started_at)

    def test_transition_in_progress_to_completed(self):
        """
        Verify a valid state transition to a terminal state stamps the
        completion time.
        """
        order = RepairOrderFactory(status=RepairOrderStatus.IN_PROGRESS)
        url = reverse("repairs:repair-order-detail", kwargs={"pk": order.pk})

        response = self.client.patch(
            url,
            {"status": RepairOrderStatus.COMPLETED},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        order.refresh_from_db()
        self.assertEqual(order.status, RepairOrderStatus.COMPLETED)
        self.assertIsNotNone(order.completed_at)

    def test_invalid_transition_rejected(self):
        """
        Verify that skipping states or invalid transitions are blocked by the
        state machine.
        """
        order = RepairOrderFactory(status=RepairOrderStatus.COMPLETED)
        url = reverse("repairs:repair-order-detail", kwargs={"pk": order.pk})

        response = self.client.patch(
            url,
            {"status": RepairOrderStatus.PENDING},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_viewer_cannot_update_status(self):
        """
        Verify that users lacking correct permissions cannot transition order
        states.
        """
        viewer = ViewerUserFactory()
        self.client.force_authenticate(viewer)

        order = RepairOrderFactory(status=RepairOrderStatus.PENDING)
        url = reverse("repairs:repair-order-detail", kwargs={"pk": order.pk})

        response = self.client.patch(
            url,
            {"status": RepairOrderStatus.IN_PROGRESS},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class DroneRepairHistoryTests(APITestCase):
    """Verify aggregated timeline generation combining multiple repair models."""

    def setUp(self):
        """Prepare authentication, a drone, and the timeline URL."""
        self.user = AdminUserFactory()
        self.client.force_authenticate(self.user)
        self.drone = DroneFactory()
        self.url = reverse(
            "repairs:drone-repair-history",
            kwargs={"drone_id": self.drone.id},
        )

    def test_empty_timeline(self):
        """Verify that a drone with no history returns an empty timeline."""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 0)

    def test_timeline_includes_defects(self):
        """Verify that defect reports are mapped into the timeline correctly."""
        DefectReportFactory(drone=self.drone)

        response = self.client.get(self.url)
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(response.data["results"][0]["event_type"], "defect")

    def test_timeline_includes_repairs(self):
        """Verify that repair orders are mapped into the timeline correctly."""
        RepairOrderFactory(drone=self.drone)

        response = self.client.get(self.url)
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(response.data["results"][0]["event_type"], "repair")

    def test_timeline_includes_replacements(self):
        """Verify that component replacements are mapped into the timeline correctly."""
        ComponentReplacementFactory(drone=self.drone)

        response = self.client.get(self.url)
        types = [r["event_type"] for r in response.data["results"]]
        self.assertIn("replacement", types)

    def test_timeline_aggregates_all_types(self):
        """Verify that all relevant models are fetched and combined successfully."""
        DefectReportFactory(drone=self.drone)
        RepairOrderFactory(drone=self.drone)
        ComponentReplacementFactory(drone=self.drone)

        response = self.client.get(self.url)
        types = {r["event_type"] for r in response.data["results"]}
        self.assertEqual(types, {"defect", "repair", "replacement"})

    def test_filter_by_event_type(self):
        """Verify that the timeline can be filtered down to specific event types."""
        DefectReportFactory(drone=self.drone)
        RepairOrderFactory(drone=self.drone)

        response = self.client.get(self.url, {"event_type": "defect"})
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(response.data["results"][0]["event_type"], "defect")

    def test_nonexistent_drone_returns_404(self):
        """Verify that requesting a timeline for a nonexistent drone returns a 404."""
        url = reverse(
            "repairs:drone-repair-history",
            kwargs={"drone_id": 9999999},
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_timeline_sorted_by_timestamp_desc(self):
        """Verify that timeline items are globally sorted from newest to oldest."""
        DefectReportFactory(
            drone=self.drone,
            detected_at=datetime.datetime(
                2026,
                6,
                1,
                10,
                0,
                tzinfo=datetime.timezone.utc,
            ),
        )
        DefectReportFactory(
            drone=self.drone,
            detected_at=datetime.datetime(
                2026,
                6,
                10,
                10,
                0,
                tzinfo=datetime.timezone.utc,
            ),
        )

        response = self.client.get(self.url)
        timestamps = [r["timestamp"] for r in response.data["results"]]
        self.assertEqual(timestamps, sorted(timestamps, reverse=True))

    def test_does_not_include_other_drones(self):
        """
        Verify that events belonging to other drones are excluded from the
        timeline.
        """
        other_drone = DroneFactory()
        DefectReportFactory(drone=other_drone)
        DefectReportFactory(drone=self.drone)

        response = self.client.get(self.url)
        self.assertEqual(response.data["count"], 1)


class RepairHistoryExportTests(APITestCase):
    """Verify CSV streaming functionality for timeline history."""

    def setUp(self):
        """Prepare authentication and initial timeline records."""
        self.user = AdminUserFactory()
        self.client.force_authenticate(self.user)
        self.drone = DroneFactory()
        self.url = reverse(
            "repairs:drone-repair-history-export",
            kwargs={"drone_id": self.drone.id},
        )

    def test_export_returns_csv(self):
        """
        Verify that the history export endpoint returns a correctly configured
        CSV response.
        """
        DefectReportFactory(drone=self.drone)

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response["Content-Type"], "text/csv")
        self.assertIn("attachment", response["Content-Disposition"])

    def test_export_contains_header_row(self):
        """Verify that the CSV output includes standard headers."""
        response = self.client.get(self.url)
        content = b"".join(response.streaming_content).decode("utf-8")
        self.assertIn("Date", content)
        self.assertIn("Event Type", content)
        self.assertIn("Summary", content)

    def test_export_contains_data(self):
        """Verify that CSV export yields the correct number of data rows."""
        DefectReportFactory(drone=self.drone)

        response = self.client.get(self.url)
        content = b"".join(response.streaming_content).decode("utf-8")
        lines = content.strip().split("\n")
        self.assertEqual(len(lines), 2)

    def test_export_nonexistent_drone_returns_404(self):
        """Verify that attempting to export history for a nonexistent drone fails."""
        url = reverse(
            "repairs:drone-repair-history-export",
            kwargs={"drone_id": 9999999},
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_viewer_cannot_export(self):
        """Verify that unauthorized roles cannot download the history CSV."""
        viewer = ViewerUserFactory()
        self.client.force_authenticate(viewer)

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_staff_without_export_permission_cannot_export(self):
        """Verify that Django staff status alone does not grant repair exports."""
        staff_viewer = ViewerUserFactory()
        staff_viewer.is_staff = True
        staff_viewer.save(update_fields=["is_staff"])
        self.client.force_authenticate(staff_viewer)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class RepairOrderServiceTests(APITestCase):
    """Verify the business logic and state transitions in the repair order service."""

    def setUp(self):
        """Prepare dependencies for the repair order service tests."""
        self.drone = DroneFactory()
        self.user = AdminUserFactory()

    def test_create_repair_order(self):
        """
        Verify that the service creates a repair order perfectly assigned to
        a user.
        """
        order = create_repair_order(
            drone=self.drone,
            description="Replace damaged propeller after collision.",
            created_by=self.user,
        )

        self.assertEqual(RepairOrder.objects.count(), 1)
        self.assertEqual(order.drone, self.drone)
        self.assertEqual(order.status, RepairOrderStatus.PENDING)
        self.assertEqual(order.created_by, self.user)

    def test_update_status_valid_transition(self):
        """Verify that the service applies a valid state machine transition."""
        order = RepairOrderFactory(drone=self.drone, status=RepairOrderStatus.PENDING)

        updated = update_repair_order_status(
            repair_order=order,
            new_status=RepairOrderStatus.IN_PROGRESS,
            user=self.user,
        )

        self.assertEqual(updated.status, RepairOrderStatus.IN_PROGRESS)
        self.assertIsNotNone(updated.started_at)

    def test_update_status_invalid_transition_raises(self):
        """Verify that the service blocks invalid transitions using ValueError."""
        order = RepairOrderFactory(drone=self.drone, status=RepairOrderStatus.COMPLETED)

        with self.assertRaises(ValueError):
            update_repair_order_status(
                repair_order=order,
                new_status=RepairOrderStatus.PENDING,
            )


class RepairHistoryServiceTests(APITestCase):
    """Verify the aggregation and filtering logic of the timeline generation service."""

    def setUp(self):
        """Prepare the base drone for aggregation testing."""
        self.drone = DroneFactory()

    def test_empty_history(self):
        """Verify that fetching history for a pristine drone returns an empty list."""
        result = get_drone_repair_history(self.drone.id)
        self.assertEqual(result, [])

    def test_aggregation_includes_all_types(self):
        """
        Verify that the service perfectly groups multiple distinct event
        models.
        """
        DefectReportFactory(drone=self.drone)
        RepairOrderFactory(drone=self.drone)
        ComponentReplacementFactory(drone=self.drone)

        result = get_drone_repair_history(self.drone.id)
        types = {event["event_type"] for event in result}
        self.assertEqual(types, {"defect", "repair", "replacement"})

    def test_filter_by_event_type(self):
        """
        Verify that passing an event filter successfully narrows the result
        list.
        """
        DefectReportFactory(drone=self.drone)
        RepairOrderFactory(drone=self.drone)

        result = get_drone_repair_history(self.drone.id, event_types=["repair"])
        self.assertTrue(all(e["event_type"] == "repair" for e in result))

    def test_sorted_by_timestamp_descending(self):
        """
        Verify that the final merged list guarantees descending chronological
        order.
        """
        DefectReportFactory(
            drone=self.drone,
            detected_at=datetime.datetime(2026, 6, 1, tzinfo=datetime.timezone.utc),
        )
        DefectReportFactory(
            drone=self.drone,
            detected_at=datetime.datetime(2026, 6, 10, tzinfo=datetime.timezone.utc),
        )

        result = get_drone_repair_history(self.drone.id)
        timestamps = [e["timestamp"] for e in result]
        self.assertEqual(timestamps, sorted(timestamps, reverse=True))


class RepairOrderFactoryTests(APITestCase):
    """Verify the integrity of the repair order test factory."""

    def test_factory_produces_valid_row(self):
        """
        Verify that generating a repair order from the factory passes DB
        constraints.
        """
        order = RepairOrderFactory()
        self.assertIsNotNone(order.pk)
        self.assertEqual(RepairOrder.objects.count(), 1)


class RepairOrderProtectTests(APITestCase):
    """Verify database-level deletion protection for drones with repair orders."""

    def test_drone_with_repair_orders_cannot_be_deleted(self):
        """
        Verify that trying to hard delete a drone linked to an order fails
        safely.
        """
        order = RepairOrderFactory()

        with self.assertRaises(ProtectedError):
            order.drone.delete()


class DefectStatusUpdateTests(APITestCase):
    """Verify status transitions, audit logs, and side effects for defects."""

    def setUp(self):
        """Prepare authentication, defect data, and URLs."""
        self.drone = DroneFactory()
        self.reporter = AdminUserFactory(email="reporter@example.com")
        self.defect = DefectReportFactory(
            drone=self.drone, reporter=self.reporter, status=RepairStatus.REPORTED
        )
        self.url = reverse(
            "repairs:defect-update-status", kwargs={"pk": self.defect.pk}
        )

        self.role, _ = Role.objects.get_or_create(
            code=TECHNICIAN_CODE, name="Technician"
        )
        self.user = AdminUserFactory()
        self.user.role = self.role
        self.user.save()
        self.client.force_authenticate(self.user)

    def test_successful_status_update_creates_history(self):
        """
        Verify that a valid status transition generates the correct audit
        history record.
        """
        payload = {
            "status": RepairStatus.IN_PROGRESS,
            "action_taken": "Starting diagnostics.",
        }
        response = self.client.post(self.url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.defect.refresh_from_db()
        self.assertEqual(self.defect.status, RepairStatus.IN_PROGRESS)

        events = RepairEvent.objects.filter(defect_report=self.defect)
        self.assertEqual(events.count(), 1)

        event = events.first()
        self.assertEqual(event.from_status, RepairStatus.REPORTED)
        self.assertEqual(event.to_status, RepairStatus.IN_PROGRESS)
        self.assertEqual(event.action_taken, "Starting diagnostics.")
        self.assertEqual(event.technician, self.user)

    def test_status_update_sends_email(self):
        """
        Verify that updating a defect dispatches an email notification to the
        reporter.
        """
        payload = {
            "status": RepairStatus.FIXED,
            "action_taken": "Replaced the broken part.",
        }
        self.client.post(self.url, payload, format="json")

        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, [self.reporter.email])
        self.assertIn("Status Update", mail.outbox[0].subject)
        self.assertIn(RepairStatus.FIXED, mail.outbox[0].body)
        self.assertIn("Replaced the broken part.", mail.outbox[0].body)

    def test_same_status_update_is_rejected(self):
        """Verify that transitioning to the identical current status is blocked."""
        payload = {"status": RepairStatus.REPORTED, "action_taken": "Doing nothing."}
        response = self.client.post(self.url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_verified_must_come_from_fixed(self):
        """Verify that VERIFIED status can exclusively follow the FIXED state."""
        payload = {
            "status": RepairStatus.VERIFIED,
            "action_taken": "Skipping to verified.",
        }
        response = self.client.post(self.url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class DefectStatusUpdateRBACTests(APITestCase):
    """Verify role-based access control restrictions for defect transitions."""

    def setUp(self):
        """Setup user roles and existing defect data."""
        self.drone = DroneFactory()
        self.defect = DefectReportFactory(
            drone=self.drone, status=RepairStatus.REPORTED
        )
        self.url = reverse(
            "repairs:defect-update-status", kwargs={"pk": self.defect.pk}
        )

        self.tech_role, _ = Role.objects.get_or_create(
            code=TECHNICIAN_CODE, name="Technician"
        )
        self.cmd_role, _ = Role.objects.get_or_create(
            code=COMMANDER_CODE, name="Commander"
        )
        self.viewer_role, _ = Role.objects.get_or_create(
            code=VIEWER_CODE, name="Viewer"
        )

    def test_viewer_cannot_update_status(self):
        """Verify that viewers are restricted from mutating defect statuses."""
        user = AdminUserFactory()
        user.role = self.viewer_role
        user.save()
        self.client.force_authenticate(user)

        payload = {"status": RepairStatus.IN_PROGRESS, "action_taken": "Try to update"}
        response = self.client.post(self.url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_technician_can_update_to_in_progress_but_not_verified(self):
        """
        Verify that technicians can progress a defect but cannot sign off as
        verified.
        """
        tech = AdminUserFactory()
        tech.role = self.tech_role
        tech.save()
        self.client.force_authenticate(tech)

        payload_progress = {
            "status": RepairStatus.IN_PROGRESS,
            "action_taken": "Work started",
        }
        response_progress = self.client.post(self.url, payload_progress, format="json")
        self.assertEqual(response_progress.status_code, status.HTTP_200_OK)

        self.defect.status = RepairStatus.FIXED
        self.defect.save()

        payload_verified = {
            "status": RepairStatus.VERIFIED,
            "action_taken": "Looks good",
        }
        response_verified = self.client.post(self.url, payload_verified, format="json")
        self.assertEqual(response_verified.status_code, status.HTTP_403_FORBIDDEN)

    @patch("repairs.permissions.user_has_permission", return_value=True)
    def test_commander_can_verify(self, mock_has_perm):
        """Verify that commanders hold the required authority to verify defects."""
        cmd = AdminUserFactory()
        cmd.role = self.cmd_role
        cmd.save()
        self.client.force_authenticate(cmd)

        self.defect.status = RepairStatus.FIXED
        self.defect.save()

        payload = {
            "status": RepairStatus.VERIFIED,
            "action_taken": "Checked and approved.",
        }
        response = self.client.post(self.url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
