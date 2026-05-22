import copy

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from drones.factories import (
    AdminUserFactory,
    DroneFactory,
    DroneSpecFactory,
    MilitaryUnitFactory,
    ViewerUserFactory,
)
from drones.models import Drone, DroneSpec, DroneStatusHistory, WriteOffRecord
from drones.pagination import StandardResultsSetPagination


class DroneCreateTests(APITestCase):
    def setUp(self):
        self.create_url = reverse("drones:drone-create")
        self.military_unit = MilitaryUnitFactory()
        self.base_payload = {
            "serial_number": "Test Serial Number",
            "inventory_number": "Test Inventory Number",
            "name": "Test Name",
            "drone_model": "Test Model",
            "status": "ACTIVE",
            "military_unit": self.military_unit.id,
            "acquired_at": "2026-05-09",
            "spec": {
                "frame_type": "Test Frame",
                "motor_model": "Test Motor Model",
                "battery_type": "Test Battery Type",
                "battery_capacity_mah": 1500,
                "camera_model": "Test Camera Model",
                "vtx_model": "Test VTX Model",
                "flight_controller": "Test Controller",
                "firmware_version": "Test Firmware Version",
                "max_speed_kmh": "12.5",
                "max_range_km": "130",
                "max_flight_time_min": "20",
                "frequency_mhz": "1000",
                "payload_capacity_g": "100",
            },
        }
        self.user = AdminUserFactory()
        self.client.force_authenticate(self.user)

    def test_create_drone_with_spec(self):
        response = self.client.post(self.create_url, self.base_payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Drone.objects.count(), 1)
        self.assertEqual(DroneSpec.objects.count(), 1)

        drone = Drone.objects.first()

        self.assertEqual(drone.drone_model, "Test Model")
        self.assertEqual(drone.spec.frame_type, "Test Frame")

    def test_create_drone_missing_required_field(self):
        payload = copy.deepcopy(self.base_payload)
        payload.pop("serial_number")

        response = self.client.post(self.create_url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("serial_number", response.data)
        self.assertEqual(response.data["serial_number"][0].code, "required")

    def test_create_drone_duplicate_serial_number(self):
        Drone.objects.create(
            serial_number=self.base_payload["serial_number"],
            inventory_number="Inventory Number",
            name="Drone",
            drone_model="Test Model",
            status="ACTIVE",
            military_unit=self.military_unit,
            acquired_at="2026-05-09",
        )

        response = self.client.post(self.create_url, self.base_payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("serial_number", response.data)
        self.assertEqual(response.data["serial_number"][0].code, "unique")

    def test_create_spec_with_optional_fields_omitted(self):
        payload = copy.deepcopy(self.base_payload)
        payload["spec"].pop("vtx_model", None)
        payload["spec"].pop("firmware_version", None)
        payload["spec"].pop("payload_capacity_g", None)

        response = self.client.post(self.create_url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        drone = Drone.objects.first()
        spec = DroneSpec.objects.get(drone=drone)

        self.assertEqual(spec.vtx_model, "")
        self.assertEqual(spec.firmware_version, "")
        self.assertIsNone(spec.payload_capacity_g)


class DroneUpdateAndDecommissionTests(APITestCase):
    def setUp(self):
        self.admin_user = AdminUserFactory()
        self.viewer_user = ViewerUserFactory()

        self.drone = DroneFactory(status="ACTIVE")
        DroneSpecFactory(drone=self.drone)

        self.list_url = reverse("drones:drone-create")
        self.detail_url = reverse("drones:drone-detail", kwargs={"pk": self.drone.pk})

    def test_get_drone_detail_as_admin(self):
        self.client.force_authenticate(self.admin_user)

        response = self.client.get(self.detail_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["id"], self.drone.id)
        self.assertEqual(response.data["status"], "ACTIVE")

    def test_patch_drone_notes(self):
        self.client.force_authenticate(self.admin_user)

        response = self.client.patch(
            self.detail_url,
            {"notes": "Updated notes"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.drone.refresh_from_db()

        self.assertEqual(self.drone.notes, "Updated notes")

    def test_patch_drone_spec(self):
        self.client.force_authenticate(self.admin_user)

        response = self.client.patch(
            self.detail_url,
            {
                "spec": {
                    "frame_type": "Updated frame",
                    "max_speed_kmh": "155.50",
                }
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.drone.spec.refresh_from_db()

        self.assertEqual(self.drone.spec.frame_type, "Updated frame")
        self.assertEqual(str(self.drone.spec.max_speed_kmh), "155.50")

    def test_decommission_requires_reason(self):
        self.client.force_authenticate(self.admin_user)

        response = self.client.patch(
            self.detail_url,
            {"status": "WRITTEN_OFF"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("writeoff_reason", response.data)

    def test_decommission_creates_writeoff_record_and_status_history(self):
        self.client.force_authenticate(self.admin_user)

        response = self.client.patch(
            self.detail_url,
            {
                "status": "WRITTEN_OFF",
                "writeoff_reason": "Destroyed during mission",
                "writeoff_reason_description": "The drone cannot be repaired.",
                "document_number": "WO-2026-001",
                "written_off_at": "2026-05-17",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.drone.refresh_from_db()

        self.assertEqual(self.drone.status, "WRITTEN_OFF")
        self.assertTrue(Drone.objects.filter(id=self.drone.id).exists())
        self.assertEqual(WriteOffRecord.objects.count(), 1)
        self.assertEqual(DroneStatusHistory.objects.count(), 1)

        writeoff_record = WriteOffRecord.objects.get(drone=self.drone)
        status_history = DroneStatusHistory.objects.get(drone=self.drone)

        self.assertEqual(writeoff_record.reason, "Destroyed during mission")
        self.assertEqual(writeoff_record.document_number, "WO-2026-001")
        self.assertEqual(status_history.from_status, "ACTIVE")
        self.assertEqual(status_history.to_status, "WRITTEN_OFF")
        self.assertEqual(status_history.related_writeoff, writeoff_record)

    def test_decommissioned_drone_is_not_returned_in_active_list(self):
        self.client.force_authenticate(self.admin_user)

        inactive_drone = DroneFactory(status="WRITTEN_OFF")
        DroneSpecFactory(drone=inactive_drone)

        response = self.client.get(self.list_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        returned_ids = [drone["id"] for drone in response.data["results"]]

        self.assertIn(self.drone.id, returned_ids)
        self.assertNotIn(inactive_drone.id, returned_ids)

    def test_viewer_can_get_drone_detail(self):
        self.client.force_authenticate(self.viewer_user)

        response = self.client.get(self.detail_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_viewer_cannot_patch_drone(self):
        self.client.force_authenticate(self.viewer_user)

        response = self.client.patch(
            self.detail_url,
            {"notes": "Viewer update attempt"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_status_change_creates_status_history(self):
        self.client.force_authenticate(self.admin_user)

        response = self.client.patch(
            self.detail_url,
            {"status": "DAMAGED"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.drone.refresh_from_db()

        self.assertEqual(self.drone.status, "DAMAGED")
        self.assertEqual(DroneStatusHistory.objects.count(), 1)

        history = DroneStatusHistory.objects.get()

        self.assertEqual(history.from_status, "ACTIVE")
        self.assertEqual(history.to_status, "DAMAGED")

    def test_decommission_requires_written_off_at(self):
        self.client.force_authenticate(self.admin_user)

        response = self.client.patch(
            self.detail_url,
            {
                "status": "WRITTEN_OFF",
                "writeoff_reason": "Destroyed during mission",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("written_off_at", response.data)

    def test_existing_writeoff_record_is_not_overwritten(self):
        self.client.force_authenticate(self.admin_user)

        self.client.patch(
            self.detail_url,
            {
                "status": "WRITTEN_OFF",
                "writeoff_reason": "Original reason",
                "document_number": "WO-2026-001",
                "written_off_at": "2026-05-17",
            },
            format="json",
        )

        response = self.client.patch(
            self.detail_url,
            {
                "status": "WRITTEN_OFF",
                "writeoff_reason": "Changed reason",
                "document_number": "WO-2026-999",
                "written_off_at": "2026-05-18",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        writeoff_record = WriteOffRecord.objects.get(drone=self.drone)
        self.assertEqual(writeoff_record.reason, "Original reason")
        self.assertEqual(writeoff_record.document_number, "WO-2026-001")
        self.assertEqual(str(writeoff_record.written_off_at), "2026-05-17")


class DroneSearchTests(APITestCase):
    def setUp(self):
        self.create_url = reverse("drones:drone-create")
        self.military_unit = MilitaryUnitFactory()
        self.page_size = StandardResultsSetPagination.page_size
        self.drones = []
        for i in range(self.page_size + 1):
            if i % 2 == 0:
                self.drones.append(DroneFactory(military_unit=self.military_unit))
            else:
                self.drones.append(
                    DroneFactory(military_unit=self.military_unit, status="LOST")
                )

        self.user = ViewerUserFactory()
        self.client.force_authenticate(self.user)

    def test_get_drone_list(self):
        response = self.client.get(self.create_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_pagination_get_first_page(self):
        response = self.client.get(self.create_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], self.page_size + 1)
        self.assertEqual(
            len(response.data["results"]),
            self.page_size,
        )
        self.assertIsNotNone(response.data["next"])
        self.assertIsNone(response.data["previous"])

    def test_pagination_get_second_page(self):
        response = self.client.get(self.create_url, {"page": 2})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            len(response.data["results"]),
            1,
        )
        self.assertIsNotNone(response.data["previous"])

    def test_pagination_get_non_existing_page(self):
        response = self.client.get(self.create_url, {"page": 10})

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_search_valid_query(self):
        target_drone = self.drones[1]
        response = self.client.get(
            self.create_url, {"search": target_drone.serial_number}
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response.data["results"][0]["serial_number"], target_drone.serial_number
        )

    def test_search_no_results(self):
        response = self.client.get(self.create_url, {"search": "NON_EXISTENT_QUERY"})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 0)

    def test_filtering_exact_field(self):
        response = self.client.get(self.create_url, {"status": "LOST"})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        for item in response.data["results"]:
            self.assertEqual(item["status"], "LOST")

    def test_filtering_icontains_field(self):
        response = self.client.get(
            self.create_url, {"drone_model__icontains": "model_4"}
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        for item in response.data["results"]:
            self.assertIn("model_4", item["drone_model"])

    def test_ordering(self):
        response = self.client.get(self.create_url, {"ordering": "name"})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.data["results"]
        names = [d["name"] for d in results]
        self.assertEqual(names, sorted(names))
