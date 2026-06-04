import copy

from django.core.exceptions import ValidationError
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from common.pagination import StandardResultsSetPagination
from drones.factories import (
    AdminUserFactory,
    DroneFactory,
    DroneSpecFactory,
    MilitaryUnitFactory,
    ViewerUserFactory,
)
from drones.models import (
    Drone,
    DroneSpec,
    DroneSpecChangeLog,
    DroneStatusHistory,
    WriteOffRecord,
)


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
                "battery_model": "Test Battery Model",
                "camera_model": "Test Camera Model",
                "camera_specs": {
                    "sensor": '1/2.8"',
                    "resolution": "1080p",
                    "fov": "120",
                    "stabilization": "none",
                    "night_mode": True,
                },
                "vtx_model": "Test VTX Model",
                "flight_controller": "Test Controller",
                "firmware_version": "Test Firmware Version",
                "typical_range_km": "95.50",
                "max_speed_kmh": "12.5",
                "max_range_km": "130",
                "typical_flight_time_min": "17.50",
                "max_flight_time_min": "20",
                "frequency_mhz": "1000",
                "payload_capacity_g": "100",
                "additional_modules": [
                    {
                        "type": "GPS",
                        "model": "Matek M10Q",
                        "notes": "External module",
                    },
                    {
                        "type": "Receiver",
                        "model": "ELRS 2.4GHz",
                        "notes": "",
                    },
                ],
                "technical_documentation_url": "https://example.com/drone-spec.pdf",
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

    def test_create_drone_with_detailed_spec_fields(self):
        response = self.client.post(self.create_url, self.base_payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        spec = DroneSpec.objects.get()
        self.assertEqual(spec.battery_model, "Test Battery Model")
        self.assertEqual(spec.camera_specs["resolution"], "1080p")
        self.assertEqual(str(spec.typical_range_km), "95.50")
        self.assertEqual(str(spec.typical_flight_time_min), "17.50")
        self.assertEqual(spec.additional_modules[0]["type"], "GPS")
        self.assertEqual(
            spec.technical_documentation_url,
            "https://example.com/drone-spec.pdf",
        )

    def test_create_drone_with_typical_performance_metrics(self):
        response = self.client.post(self.create_url, self.base_payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        drone = Drone.objects.get()
        spec = drone.spec

        self.assertEqual(str(spec.typical_range_km), "95.50")
        self.assertEqual(str(spec.typical_flight_time_min), "17.50")

    def test_create_drone_spec_change_log_created(self):
        response = self.client.post(self.create_url, self.base_payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(DroneSpecChangeLog.objects.count(), 0)

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
        payload["spec"].pop("battery_model", None)
        payload["spec"].pop("camera_specs", None)
        payload["spec"].pop("additional_modules", None)
        payload["spec"].pop("technical_documentation_url", None)

        response = self.client.post(self.create_url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        drone = Drone.objects.first()
        spec = DroneSpec.objects.get(drone=drone)

        self.assertEqual(spec.vtx_model, "")
        self.assertEqual(spec.firmware_version, "")
        self.assertIsNone(spec.payload_capacity_g)
        self.assertEqual(spec.battery_model, "")
        self.assertEqual(spec.camera_specs, {})
        self.assertEqual(spec.additional_modules, [])
        self.assertEqual(spec.technical_documentation_url, "")

    def test_create_drone_rejects_invalid_camera_specs(self):
        payload = copy.deepcopy(self.base_payload)
        payload["spec"]["camera_specs"] = ["invalid"]

        response = self.client.post(self.create_url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("camera_specs", response.data["spec"])

    def test_create_drone_rejects_invalid_additional_modules(self):
        payload = copy.deepcopy(self.base_payload)
        payload["spec"]["additional_modules"] = {"type": "GPS"}

        response = self.client.post(self.create_url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("additional_modules", response.data["spec"])


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

    def test_drone_detail_returns_typical_performance_metrics(self):
        self.client.force_authenticate(self.admin_user)

        self.drone.spec.typical_range_km = "95.50"
        self.drone.spec.typical_flight_time_min = "17.50"
        self.drone.spec.save(
            update_fields=[
                "typical_range_km",
                "typical_flight_time_min",
                "updated_at",
            ]
        )

        response = self.client.get(self.detail_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["spec"]["typical_range_km"], "95.50")
        self.assertEqual(response.data["spec"]["typical_flight_time_min"], "17.50")

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

    def test_patch_drone_spec_detailed_fields(self):
        self.client.force_authenticate(self.admin_user)

        response = self.client.patch(
            self.detail_url,
            {
                "spec": {
                    "battery_model": "Updated Battery Model",
                    "camera_specs": {
                        "sensor": '1/2.8"',
                        "resolution": "4K",
                        "fov": "120",
                        "night_mode": True,
                    },
                    "additional_modules": [
                        {
                            "type": "GPS",
                            "model": "Matek M10Q",
                            "notes": "External module",
                        }
                    ],
                    "technical_documentation_url": (
                        "https://example.com/updated-spec.pdf"
                    ),
                }
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.drone.spec.refresh_from_db()
        self.assertEqual(self.drone.spec.battery_model, "Updated Battery Model")
        self.assertEqual(self.drone.spec.camera_specs["resolution"], "4K")
        self.assertEqual(self.drone.spec.additional_modules[0]["type"], "GPS")
        self.assertEqual(
            self.drone.spec.technical_documentation_url,
            "https://example.com/updated-spec.pdf",
        )

    def test_patch_drone_typical_performance_metrics(self):
        self.client.force_authenticate(self.admin_user)

        response = self.client.patch(
            self.detail_url,
            {
                "spec": {
                    "typical_range_km": "110.50",
                    "typical_flight_time_min": "19.00",
                }
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.drone.spec.refresh_from_db()

        self.assertEqual(str(self.drone.spec.typical_range_km), "110.50")
        self.assertEqual(str(self.drone.spec.typical_flight_time_min), "19.00")

    def test_patch_drone_spec_creates_change_log(self):
        self.client.force_authenticate(self.admin_user)

        old_battery_model = self.drone.spec.battery_model
        old_camera_specs = self.drone.spec.camera_specs

        response = self.client.patch(
            self.detail_url,
            {
                "spec": {
                    "battery_model": "Updated Battery Model",
                    "camera_specs": {
                        "resolution": "4K",
                    },
                }
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(DroneSpecChangeLog.objects.count(), 1)

        change_log = DroneSpecChangeLog.objects.first()

        self.assertEqual(change_log.drone_spec, self.drone.spec)
        self.assertEqual(change_log.changed_by, self.admin_user)
        self.assertIn("battery_model", change_log.changed_fields)
        self.assertIn("camera_specs", change_log.changed_fields)

        self.assertEqual(
            change_log.old_values["battery_model"],
            old_battery_model,
        )
        self.assertEqual(
            change_log.old_values["camera_specs"],
            old_camera_specs,
        )

        self.assertEqual(
            change_log.new_values["battery_model"],
            "Updated Battery Model",
        )
        self.assertEqual(
            change_log.new_values["camera_specs"],
            {"resolution": "4K"},
        )

    def test_patch_typical_performance_metrics_creates_change_log(self):
        self.client.force_authenticate(self.admin_user)

        response = self.client.patch(
            self.detail_url,
            {
                "spec": {
                    "typical_range_km": "110.50",
                    "typical_flight_time_min": "19.00",
                }
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(DroneSpecChangeLog.objects.count(), 1)

        change_log = DroneSpecChangeLog.objects.first()

        self.assertIsNotNone(change_log)
        self.assertIn("typical_range_km", change_log.changed_fields)
        self.assertIn("typical_flight_time_min", change_log.changed_fields)
        self.assertEqual(change_log.new_values["typical_range_km"], "110.50")
        self.assertEqual(
            change_log.new_values["typical_flight_time_min"],
            "19.00",
        )

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

    def test_drone_spec_change_log_rejects_invalid_changed_fields(self):
        change_log = DroneSpecChangeLog(
            drone_spec=self.drone.spec,
            changed_fields={"battery_model": "Updated Battery Model"},
            old_values={},
            new_values={},
        )

        with self.assertRaises(ValidationError):
            change_log.full_clean()

    def test_drone_spec_change_log_rejects_invalid_old_values(self):
        change_log = DroneSpecChangeLog(
            drone_spec=self.drone.spec,
            changed_fields=["battery_model"],
            old_values=[],
            new_values={},
        )

        with self.assertRaises(ValidationError):
            change_log.full_clean()

    def test_drone_spec_change_log_rejects_invalid_new_values(self):
        change_log = DroneSpecChangeLog(
            drone_spec=self.drone.spec,
            changed_fields=["battery_model"],
            old_values={},
            new_values=[],
        )

        with self.assertRaises(ValidationError):
            change_log.full_clean()


class DroneSearchTests(APITestCase):
    def setUp(self):
        self.create_url = reverse("drones:drone-create")
        self.military_unit = MilitaryUnitFactory()
        self.page_size = StandardResultsSetPagination.page_size
        self.drones = DroneFactory.create_batch(
            self.page_size + 1, military_unit=self.military_unit
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

    def test_filtering_exact_field(self):
        response = self.client.get(self.create_url, {"status": self.drones[0].status})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        for item in response.data["results"]:
            self.assertEqual(item["status"], self.drones[0].status)

    def test_filtering_icontains_field(self):
        serial = self.drones[0].serial_number[:3]
        response = self.client.get(
            self.create_url, {"serial_number__icontains": serial}
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        for item in response.data["results"]:
            self.assertIn(serial.lower(), item["serial_number"].lower())

    def test_ordering(self):
        response = self.client.get(self.create_url, {"ordering": "name"})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.data["results"]
        names = [d["name"] for d in results]
        self.assertEqual(names, sorted(names))

    def test_filtering_inactive_drones(self):
        inactive_drone = DroneFactory(status="WRITTEN_OFF")

        response = self.client.get(self.create_url, {"status": "WRITTEN_OFF"})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results_ids = [item["id"] for item in response.data["results"]]
        self.assertIn(inactive_drone.id, results_ids)

    def test_filter_by_typical_range_km_gte(self):
        matching_drone = DroneFactory(military_unit=self.military_unit)
        DroneSpecFactory(drone=matching_drone, typical_range_km="120.00")

        non_matching_drone = DroneFactory(military_unit=self.military_unit)
        DroneSpecFactory(drone=non_matching_drone, typical_range_km="80.00")

        response = self.client.get(
            self.create_url,
            {"spec__typical_range_km__gte": "100.00"},
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        results_ids = [item["id"] for item in response.data["results"]]

        self.assertIn(matching_drone.id, results_ids)
        self.assertNotIn(non_matching_drone.id, results_ids)
