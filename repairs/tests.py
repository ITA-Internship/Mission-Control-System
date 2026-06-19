import datetime

from django.contrib.auth.models import AnonymousUser
from django.core.exceptions import ValidationError
from django.db.models import ProtectedError
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from common.pagination import StandardResultsSetPagination

from .factories import (
    AdminUserFactory,
    ComponentReplacementFactory,
    DefectReportFactory,
    DroneFactory,
    ViewerUserFactory,
)
from .models import (
    ComponentReplacement,
    ComponentType,
    DefectReport,
    DefectType,
    Severity,
)
from .services import create_component_replacement, create_defect_report


def _base_payload(drone):
    return {
        "drone": drone.id,
        "defect_type": DefectType.MOTOR,
        "severity": Severity.HIGH,
        "description": "Rear-left motor stutters under load and overheats.",
        "detected_at": "2026-06-03T14:30:00Z",
    }


class DefectReportCreateTests(APITestCase):
    def setUp(self):
        self.url = reverse("repairs:defect-create")
        self.drone = DroneFactory()
        self.user = AdminUserFactory()
        self.client.force_authenticate(self.user)

    def test_create_defect_report(self):
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
        response = self.client.post(self.url, _base_payload(self.drone), format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn("id", response.data)
        self.assertEqual(response.data["reporter"], self.user.id)
        self.assertIn("created_at", response.data)
        self.assertIn("updated_at", response.data)

    def test_description_is_trimmed(self):
        payload = _base_payload(self.drone)
        payload["description"] = "   Camera feed drops out intermittently.   "

        response = self.client.post(self.url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        defect = DefectReport.objects.get()
        self.assertEqual(defect.description, "Camera feed drops out intermittently.")

    def test_reporter_is_server_set_and_cannot_be_spoofed(self):
        other_user = ViewerUserFactory()
        payload = _base_payload(self.drone)
        payload["reporter"] = other_user.id

        response = self.client.post(self.url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        defect = DefectReport.objects.get()
        self.assertEqual(defect.reporter, self.user)
        self.assertNotEqual(defect.reporter, other_user)

    def test_create_accepts_recent_detected_at(self):
        payload = _base_payload(self.drone)
        payload["detected_at"] = timezone.now().isoformat()

        response = self.client.post(self.url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)


class DefectReportValidationTests(APITestCase):
    def setUp(self):
        self.url = reverse("repairs:defect-create")
        self.drone = DroneFactory()
        self.user = AdminUserFactory()
        self.client.force_authenticate(self.user)

    def test_missing_required_fields(self):
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
        payload = _base_payload(self.drone)
        payload["defect_type"] = "NOT_A_REAL_TYPE"

        response = self.client.post(self.url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("defect_type", response.data)

    def test_invalid_severity(self):
        payload = _base_payload(self.drone)
        payload["severity"] = "SUPER_CRITICAL"

        response = self.client.post(self.url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("severity", response.data)

    def test_blank_description(self):
        payload = _base_payload(self.drone)
        payload["description"] = ""

        response = self.client.post(self.url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("description", response.data)

    def test_whitespace_only_description(self):
        payload = _base_payload(self.drone)
        payload["description"] = "          "

        response = self.client.post(self.url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("description", response.data)

    def test_too_short_description(self):
        payload = _base_payload(self.drone)
        payload["description"] = "broken"

        response = self.client.post(self.url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("description", response.data)

    def test_detected_at_in_the_future_is_rejected(self):
        payload = _base_payload(self.drone)
        payload["detected_at"] = (
            timezone.now() + datetime.timedelta(hours=1)
        ).isoformat()

        response = self.client.post(self.url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("detected_at", response.data)

    def test_nonexistent_drone_is_rejected(self):
        payload = _base_payload(self.drone)
        payload["drone"] = 9999999

        response = self.client.post(self.url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("drone", response.data)


class DefectReportAuthTests(APITestCase):
    def setUp(self):
        self.url = reverse("repairs:defect-create")
        self.drone = DroneFactory()
        self.defect = DefectReportFactory(drone=self.drone)
        self.detail_url = reverse(
            "repairs:defect-detail", kwargs={"pk": self.defect.pk}
        )

    def test_unauthenticated_cannot_list(self):
        response = self.client.get(self.url)

        self.assertIn(
            response.status_code,
            (status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN),
        )

    def test_unauthenticated_cannot_create(self):
        response = self.client.post(self.url, _base_payload(self.drone), format="json")

        self.assertIn(
            response.status_code,
            (status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN),
        )

    def test_role_without_create_permission_cannot_post(self):
        # Viewer has repairs.view but not repairs.create.
        viewer = ViewerUserFactory()
        self.client.force_authenticate(viewer)

        response = self.client.post(self.url, _base_payload(self.drone), format="json")

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_role_without_create_permission_can_still_view(self):
        viewer = ViewerUserFactory()
        self.client.force_authenticate(viewer)

        list_response = self.client.get(self.url)
        detail_response = self.client.get(self.detail_url)

        self.assertEqual(list_response.status_code, status.HTTP_200_OK)
        self.assertEqual(detail_response.status_code, status.HTTP_200_OK)

    def test_role_without_view_permission_is_forbidden(self):
        # A user with no role has neither repairs.view nor repairs.create.
        roleless_user = AdminUserFactory(role=None)
        self.client.force_authenticate(roleless_user)

        list_response = self.client.get(self.url)
        detail_response = self.client.get(self.detail_url)

        self.assertEqual(list_response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(detail_response.status_code, status.HTTP_403_FORBIDDEN)


class DefectReportListTests(APITestCase):
    def setUp(self):
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
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("count", response.data)
        self.assertIn("results", response.data)
        self.assertEqual(response.data["count"], 2)

    def test_filter_by_drone(self):
        response = self.client.get(self.url, {"drone": self.drone_a.id})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        ids = [item["id"] for item in response.data["results"]]
        self.assertEqual(ids, [self.defect_a.id])

    def test_filter_by_severity(self):
        response = self.client.get(self.url, {"severity": Severity.LOW})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        ids = [item["id"] for item in response.data["results"]]
        self.assertEqual(ids, [self.defect_b.id])

    def test_filter_by_defect_type(self):
        response = self.client.get(self.url, {"defect_type": DefectType.CAMERA})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        ids = [item["id"] for item in response.data["results"]]
        self.assertEqual(ids, [self.defect_b.id])

    def test_filter_by_reporter(self):
        response = self.client.get(self.url, {"reporter": self.defect_a.reporter_id})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        ids = [item["id"] for item in response.data["results"]]
        self.assertIn(self.defect_a.id, ids)

    def test_ordering_by_detected_at(self):
        response = self.client.get(self.url, {"ordering": "detected_at"})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        ids = [item["id"] for item in response.data["results"]]
        self.assertEqual(ids, [self.defect_a.id, self.defect_b.id])

    def test_default_ordering_is_most_recent_first(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        ids = [item["id"] for item in response.data["results"]]
        self.assertEqual(ids, [self.defect_b.id, self.defect_a.id])

    def test_list_uses_slim_serializer(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # The slim list serializer omits description / updated_at.
        first = response.data["results"][0]
        self.assertNotIn("description", first)
        self.assertNotIn("updated_at", first)

    def test_list_pagination(self):
        page_size = StandardResultsSetPagination.page_size
        DefectReportFactory.create_batch(page_size, drone=self.drone_a)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], page_size + 2)
        self.assertEqual(len(response.data["results"]), page_size)
        self.assertIsNotNone(response.data["next"])


class DefectReportDetailTests(APITestCase):
    def setUp(self):
        self.user = AdminUserFactory()
        self.client.force_authenticate(self.user)
        self.defect = DefectReportFactory()
        self.detail_url = reverse(
            "repairs:defect-detail", kwargs={"pk": self.defect.pk}
        )

    def test_retrieve_existing_defect(self):
        response = self.client.get(self.detail_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["id"], self.defect.id)
        self.assertEqual(response.data["description"], self.defect.description)

    def test_retrieve_unknown_defect_returns_404(self):
        url = reverse("repairs:defect-detail", kwargs={"pk": 9999999})

        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_update_is_not_allowed(self):
        # The detail view exposes no write verbs. RepairPermission denies any
        # non-SAFE, non-POST method, so the request is rejected at the
        # permission layer (403) before the 405 routing check is ever reached.
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
    def test_drone_with_defects_cannot_be_deleted(self):
        defect = DefectReportFactory()

        with self.assertRaises(ProtectedError):
            defect.drone.delete()


class CreateDefectReportServiceTests(APITestCase):
    def setUp(self):
        self.drone = DroneFactory()
        self.user = AdminUserFactory()

    def test_create_defect_report_happy_path(self):
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
    def test_factory_produces_valid_row(self):
        defect = DefectReportFactory()

        self.assertIsNotNone(defect.pk)
        self.assertEqual(DefectReport.objects.count(), 1)

        defect.full_clean()


def _replacement_payload(drone):
    return {
        "drone": drone.id,
        "component_type": ComponentType.MOTOR,
        "old_serial_number": "MOTOR-OLD-001",
        "new_serial_number": "MOTOR-NEW-001",
        "reason": "Motor replaced after vibration and overheating.",
        "replaced_at": "2026-06-10T11:00:00Z",
    }


class ComponentReplacementCreateTests(APITestCase):
    def setUp(self):
        self.url = reverse("repairs:replacement-list-create")
        self.drone = DroneFactory()
        self.user = AdminUserFactory()
        self.client.force_authenticate(self.user)

    def test_create_component_replacement(self):
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
        other_user = ViewerUserFactory()
        payload = _replacement_payload(self.drone)
        payload["replaced_by"] = other_user.id

        response = self.client.post(self.url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        replacement = ComponentReplacement.objects.get()
        self.assertEqual(replacement.replaced_by, self.user)
        self.assertNotEqual(replacement.replaced_by, other_user)

    def test_other_component_requires_name(self):
        payload = _replacement_payload(self.drone)
        payload["component_type"] = ComponentType.OTHER

        response = self.client.post(self.url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("component_name", response.data)

    def test_other_component_accepts_custom_name(self):
        payload = _replacement_payload(self.drone)
        payload["component_type"] = ComponentType.OTHER
        payload["component_name"] = "GPS antenna"

        response = self.client.post(self.url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        replacement = ComponentReplacement.objects.get()
        self.assertEqual(replacement.component_name, "GPS antenna")


class ComponentReplacementValidationTests(APITestCase):
    def setUp(self):
        self.url = reverse("repairs:replacement-list-create")
        self.drone = DroneFactory()
        self.user = AdminUserFactory()
        self.client.force_authenticate(self.user)

    def test_missing_required_fields(self):
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
        payload = _replacement_payload(self.drone)
        payload["component_type"] = "NOT_A_REAL_COMPONENT"

        response = self.client.post(self.url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("component_type", response.data)

    def test_blank_new_serial_number(self):
        payload = _replacement_payload(self.drone)
        payload["new_serial_number"] = "    "

        response = self.client.post(self.url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("new_serial_number", response.data)

    def test_blank_reason(self):
        payload = _replacement_payload(self.drone)
        payload["reason"] = "   "

        response = self.client.post(self.url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("reason", response.data)

    def test_replaced_at_in_the_future_is_rejected(self):
        payload = _replacement_payload(self.drone)
        payload["replaced_at"] = (
            timezone.now() + datetime.timedelta(minutes=5)
        ).isoformat()

        response = self.client.post(self.url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("replaced_at", response.data)

    def test_nonexistent_drone_is_rejected(self):
        payload = _replacement_payload(self.drone)
        payload["drone"] = 9999999

        response = self.client.post(self.url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("drone", response.data)

    def test_model_validation_with_missing_replaced_at_does_not_crash(self):
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
    def setUp(self):
        self.url = reverse("repairs:replacement-list-create")
        self.drone = DroneFactory()
        self.replacement = ComponentReplacementFactory(drone=self.drone)
        self.detail_url = reverse(
            "repairs:replacement-detail",
            kwargs={"pk": self.replacement.pk},
        )

    def test_unauthenticated_cannot_list(self):
        response = self.client.get(self.url)

        self.assertIn(
            response.status_code,
            (status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN),
        )

    def test_unauthenticated_cannot_create(self):
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
        viewer = ViewerUserFactory()
        self.client.force_authenticate(viewer)

        response = self.client.post(
            self.url,
            _replacement_payload(self.drone),
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_role_without_create_permission_can_still_view(self):
        viewer = ViewerUserFactory()
        self.client.force_authenticate(viewer)

        list_response = self.client.get(self.url)
        detail_response = self.client.get(self.detail_url)

        self.assertEqual(list_response.status_code, status.HTTP_200_OK)
        self.assertEqual(detail_response.status_code, status.HTTP_200_OK)


class ComponentReplacementListTests(APITestCase):
    def setUp(self):
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
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("count", response.data)
        self.assertIn("results", response.data)
        self.assertEqual(response.data["count"], 2)

    def test_filter_by_drone(self):
        response = self.client.get(self.url, {"drone": self.drone_a.id})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        ids = [item["id"] for item in response.data["results"]]
        self.assertEqual(ids, [self.replacement_a.id])

    def test_filter_by_component_type(self):
        response = self.client.get(
            self.url,
            {"component_type": ComponentType.BATTERY},
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        ids = [item["id"] for item in response.data["results"]]
        self.assertEqual(ids, [self.replacement_b.id])

    def test_filter_by_replaced_by(self):
        response = self.client.get(
            self.url,
            {"replaced_by": self.reporter_a.id},
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        ids = [item["id"] for item in response.data["results"]]
        self.assertEqual(ids, [self.replacement_a.id])

    def test_filter_by_date_range(self):
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
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        ids = [item["id"] for item in response.data["results"]]
        self.assertEqual(ids, [self.replacement_b.id, self.replacement_a.id])

    def test_list_uses_slim_serializer(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        first = response.data["results"][0]
        self.assertNotIn("old_serial_number", first)
        self.assertNotIn("reason", first)
        self.assertNotIn("updated_at", first)

    def test_list_pagination(self):
        page_size = StandardResultsSetPagination.page_size
        ComponentReplacementFactory.create_batch(page_size, drone=self.drone_a)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], page_size + 2)
        self.assertEqual(len(response.data["results"]), page_size)
        self.assertIsNotNone(response.data["next"])


class ComponentReplacementDetailTests(APITestCase):
    def setUp(self):
        self.user = AdminUserFactory()
        self.client.force_authenticate(self.user)
        self.replacement = ComponentReplacementFactory()
        self.detail_url = reverse(
            "repairs:replacement-detail",
            kwargs={"pk": self.replacement.pk},
        )

    def test_retrieve_existing_replacement(self):
        response = self.client.get(self.detail_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["id"], self.replacement.id)
        self.assertEqual(
            response.data["old_serial_number"],
            self.replacement.old_serial_number,
        )
        self.assertEqual(response.data["reason"], self.replacement.reason)

    def test_retrieve_unknown_replacement_returns_404(self):
        url = reverse("repairs:replacement-detail", kwargs={"pk": 9999999})

        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_update_is_not_allowed(self):
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
    def setUp(self):
        self.drone = DroneFactory()
        self.user = AdminUserFactory()

    def test_create_component_replacement_happy_path(self):
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
    def test_drone_with_replacements_cannot_be_deleted(self):
        replacement = ComponentReplacementFactory()

        with self.assertRaises(ProtectedError):
            replacement.drone.delete()


class ComponentReplacementFactoryIntegrityTests(APITestCase):
    def test_factory_produces_valid_row(self):
        replacement = ComponentReplacementFactory()

        self.assertIsNotNone(replacement.pk)
        self.assertEqual(ComponentReplacement.objects.count(), 1)

        replacement.full_clean()


class ComponentReplacementReportTests(APITestCase):
    def setUp(self):
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
        content = b"".join(response.streaming_content).decode("utf-8")
        return [row for row in content.strip().splitlines() if row]

    def test_report_returns_csv_response(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response["Content-Type"], "text/csv")
        self.assertIn("component_replacements.csv", response["Content-Disposition"])

    def test_report_returns_correct_replacement_records(self):
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
        response = self.client.get(self.url, {"drone": self.drone_a.id})
        rows = self._decode_rows(response)

        self.assertEqual(len(rows), 2)
        self.assertIn("DRONE-A-001", rows[1])
        self.assertNotIn("DRONE-B-001", "\n".join(rows))

    def test_report_filters_by_component_type(self):
        response = self.client.get(
            self.url,
            {"component_type": ComponentType.BATTERY},
        )
        rows = self._decode_rows(response)

        self.assertEqual(len(rows), 2)
        self.assertIn("BATTERY", rows[1])
        self.assertNotIn("MOTOR", "\n".join(rows[1:]))

    def test_report_filters_by_user(self):
        response = self.client.get(
            self.url,
            {"replaced_by": self.reporter_a.id},
        )
        rows = self._decode_rows(response)

        self.assertEqual(len(rows), 2)
        self.assertIn("tech.alpha", rows[1])
        self.assertNotIn("tech.bravo", "\n".join(rows))

    def test_report_filters_by_date_range(self):
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
        self.client.force_authenticate(None)

        response = self.client.get(self.url)

        self.assertIn(
            response.status_code,
            (status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN),
        )
