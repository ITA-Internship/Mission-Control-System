import copy
import csv
import io
from datetime import date

from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from common.pagination import StandardResultsSetPagination
from drones.factories import (
    AdminUserFactory,
    DroneFactory,
    DroneModelFactory,
    DroneSpecFactory,
    MilitaryUnitFactory,
    ViewerUserFactory,
)
from drones.models import (
    Drone,
    DroneModel,
    DroneSpec,
    DroneSpecChangeLog,
    DroneStatusHistory,
    WriteOffRecord,
)


class DroneCreateTests(APITestCase):
    def setUp(self):
        self.create_url = reverse("drones:drone-create")
        self.military_unit = MilitaryUnitFactory()
        self.drone_model = DroneModelFactory()
        self.base_payload = {
            "serial_number": "Test Serial Number",
            "inventory_number": "Test Inventory Number",
            "name": "Test Name",
            "drone_model": self.drone_model.id,
            "classification": self.drone_model.supported_classifications[0],
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
                "is_firmware_outdated": False,
                "communication_protocol": "ExpressLRS",
                "control_channel": "CH1",
                "telemetry_channel": "CH2",
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
                "firmware_file_url": "https://example.com/firmware.bin",
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

        self.assertEqual(drone.serial_number, "Test Serial Number")
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
        self.assertFalse(spec.is_firmware_outdated)
        self.assertEqual(spec.communication_protocol, "ExpressLRS")
        self.assertEqual(spec.control_channel, "CH1")
        self.assertEqual(spec.telemetry_channel, "CH2")
        self.assertEqual(spec.firmware_file_url, "https://example.com/firmware.bin")

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
        self.assertEqual(DroneSpecChangeLog.objects.count(), 1)

        change_log = DroneSpecChangeLog.objects.first()

        self.assertEqual(change_log.drone_spec, DroneSpec.objects.get())
        self.assertEqual(change_log.changed_by, self.user)
        self.assertEqual(change_log.old_values, {})
        self.assertIn("max_speed_kmh", change_log.changed_fields)
        self.assertIn("typical_range_km", change_log.changed_fields)
        self.assertIn("typical_flight_time_min", change_log.changed_fields)
        self.assertEqual(change_log.new_values["max_speed_kmh"], "12.50")
        self.assertEqual(change_log.new_values["typical_range_km"], "95.50")
        self.assertEqual(
            change_log.new_values["typical_flight_time_min"],
            "17.50",
        )

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
            drone_model=self.drone_model,
            classification=self.drone_model.supported_classifications[0],
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
        payload["spec"].pop("communication_protocol", None)
        payload["spec"].pop("control_channel", None)
        payload["spec"].pop("telemetry_channel", None)
        payload["spec"].pop("firmware_file_url", None)
        payload["spec"].pop("is_firmware_outdated", None)

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
        self.assertEqual(spec.communication_protocol, "")
        self.assertEqual(spec.control_channel, "")
        self.assertEqual(spec.telemetry_channel, "")
        self.assertEqual(spec.firmware_file_url, "")
        self.assertFalse(spec.is_firmware_outdated)

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
                    "is_firmware_outdated": True,
                    "communication_protocol": "Crossfire",
                    "firmware_file_url": "https://example.com/new-firmware.bin",
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
        self.assertTrue(self.drone.spec.is_firmware_outdated)
        self.assertEqual(self.drone.spec.communication_protocol, "Crossfire")
        self.assertEqual(
            self.drone.spec.firmware_file_url, "https://example.com/new-firmware.bin"
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
        old_protocol = self.drone.spec.communication_protocol

        response = self.client.patch(
            self.detail_url,
            {
                "spec": {
                    "battery_model": "Updated Battery Model",
                    "camera_specs": {
                        "resolution": "4K",
                    },
                    "communication_protocol": "Crossfire",
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
        self.assertIn("communication_protocol", change_log.changed_fields)
        self.assertEqual(change_log.old_values["communication_protocol"], old_protocol)
        self.assertEqual(change_log.new_values["communication_protocol"], "Crossfire")

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
                "writeoff_reason": WriteOffRecord.Reason.DESTRUCTION,
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

        self.assertEqual(writeoff_record.reason, WriteOffRecord.Reason.DESTRUCTION)
        self.assertEqual(
            writeoff_record.reason_description, "The drone cannot be repaired."
        )
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

    def test_status_change_uses_custom_reason_in_status_history(self):
        self.client.force_authenticate(self.admin_user)

        response = self.client.patch(
            self.detail_url,
            {
                "status": Drone.STATUS_DAMAGED,
                "status_change_reason": "Battery failure during inspection",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.drone.refresh_from_db()
        self.assertEqual(self.drone.status, Drone.STATUS_DAMAGED)

        history = DroneStatusHistory.objects.get(drone=self.drone)

        self.assertEqual(history.from_status, Drone.STATUS_ACTIVE)
        self.assertEqual(history.to_status, Drone.STATUS_DAMAGED)
        self.assertEqual(history.reason, "Battery failure during inspection")
        self.assertEqual(history.changed_by, self.admin_user)

    def test_drone_detail_returns_status_history_and_visual_indicators(self):
        self.client.force_authenticate(self.admin_user)

        self.client.patch(
            self.detail_url,
            {
                "status": Drone.STATUS_DAMAGED,
                "status_change_reason": "Motor damaged",
            },
            format="json",
        )

        response = self.client.get(self.detail_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(response.data["status"], Drone.STATUS_DAMAGED)
        self.assertEqual(response.data["status_label"], "Damaged")
        self.assertEqual(response.data["status_indicator"], "warning")
        self.assertEqual(response.data["status_category"], "downtime")

        self.assertIn("status_history", response.data)
        self.assertEqual(len(response.data["status_history"]), 1)

        history_item = response.data["status_history"][0]

        self.assertEqual(history_item["from_status"], Drone.STATUS_ACTIVE)
        self.assertEqual(history_item["to_status"], Drone.STATUS_DAMAGED)
        self.assertEqual(history_item["reason"], "Motor damaged")
        self.assertEqual(history_item["event_type"], "status_change")

    def test_decommission_requires_written_off_at(self):
        self.client.force_authenticate(self.admin_user)

        response = self.client.patch(
            self.detail_url,
            {
                "status": "WRITTEN_OFF",
                "writeoff_reason": WriteOffRecord.Reason.DESTRUCTION,
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
                "writeoff_reason": WriteOffRecord.Reason.LOSS,
                "document_number": "WO-2026-001",
                "written_off_at": "2026-05-17",
            },
            format="json",
        )

        response = self.client.patch(
            self.detail_url,
            {
                "status": "WRITTEN_OFF",
                "writeoff_reason": WriteOffRecord.Reason.DAMAGE,
                "document_number": "WO-2026-999",
                "written_off_at": "2026-05-18",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        writeoff_record = WriteOffRecord.objects.get(drone=self.drone)
        self.assertEqual(writeoff_record.reason, WriteOffRecord.Reason.LOSS)
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


class WriteOffHistoryAuditTests(APITestCase):
    def setUp(self):
        self.admin_user = AdminUserFactory()
        self.viewer_user = ViewerUserFactory()

        self.drone = DroneFactory(status=Drone.STATUS_WRITTEN_OFF)
        self.other_drone = DroneFactory(status=Drone.STATUS_WRITTEN_OFF)

        self.list_url = reverse("drones:writeoff-history")
        self.drone_history_url = reverse(
            "drones:drone-writeoff-history",
            kwargs={"drone_pk": self.drone.pk},
        )
        self.report_url = reverse("drones:writeoff-history-report")

    def get_writeoff_reason(self):
        reason_choices = getattr(WriteOffRecord, "Reason", None)
        return getattr(reason_choices, "OTHER", "Destroyed during mission")

    def create_writeoff_record(self, drone=None, document_number="WO-TEST-001"):
        return WriteOffRecord.objects.create(
            drone=drone or self.drone,
            reason=self.get_writeoff_reason(),
            reason_description="Audit test write-off reason.",
            authorized_by=self.admin_user,
            document_number=document_number,
            written_off_at=date(2026, 5, 17),
        )

    def get_results(self, response):
        return response.data.get("results", response.data)

    def test_writeoff_record_cannot_be_updated_after_creation(self):
        writeoff = self.create_writeoff_record()

        writeoff.reason_description = "Changed description."

        with self.assertRaises(ValidationError):
            writeoff.save()

    def test_writeoff_record_cannot_be_deleted_after_creation(self):
        writeoff = self.create_writeoff_record()

        with self.assertRaises(ValidationError):
            writeoff.delete()

    def test_writeoff_record_queryset_delete_is_blocked(self):
        writeoff = self.create_writeoff_record()

        with self.assertRaises(ValidationError):
            WriteOffRecord.objects.filter(pk=writeoff.pk).delete()

    def test_writeoff_record_queryset_update_is_blocked(self):
        writeoff = self.create_writeoff_record()

        with self.assertRaises(ValidationError):
            WriteOffRecord.objects.filter(pk=writeoff.pk).update(
                reason_description="Changed through queryset."
            )

    def test_writeoff_history_api_returns_records_for_authorized_user(self):
        writeoff = self.create_writeoff_record()

        self.client.force_authenticate(self.viewer_user)

        response = self.client.get(self.list_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        results = self.get_results(response)

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["id"], writeoff.id)
        self.assertEqual(results[0]["drone_id"], self.drone.id)
        self.assertEqual(results[0]["document_number"], "WO-TEST-001")

    def test_writeoff_history_api_is_protected_for_unauthenticated_user(self):
        self.create_writeoff_record()

        self.client.force_authenticate(user=None)

        response = self.client.get(self.list_url)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_drone_writeoff_history_returns_only_selected_drone_records(self):
        selected_writeoff = self.create_writeoff_record(
            drone=self.drone,
            document_number="WO-SELECTED",
        )
        self.create_writeoff_record(
            drone=self.other_drone,
            document_number="WO-OTHER",
        )

        self.client.force_authenticate(self.viewer_user)

        response = self.client.get(self.drone_history_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        results = self.get_results(response)

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["id"], selected_writeoff.id)
        self.assertEqual(results[0]["drone_id"], self.drone.id)
        self.assertEqual(results[0]["document_number"], "WO-SELECTED")

    def test_writeoff_history_api_does_not_allow_post(self):
        self.client.force_authenticate(self.admin_user)

        response = self.client.post(self.list_url, {}, format="json")

        self.assertIn(
            response.status_code,
            (
                status.HTTP_403_FORBIDDEN,
                status.HTTP_405_METHOD_NOT_ALLOWED,
            ),
        )

    def test_writeoff_history_report_view_returns_html_for_staff_user(self):
        self.create_writeoff_record(document_number="WO-REPORT-001")

        self.admin_user.is_staff = True
        self.admin_user.save(update_fields=["is_staff"])

        self.client.force_login(self.admin_user)

        response = self.client.get(self.report_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertContains(response, "Write-off event log")
        self.assertContains(response, "WO-REPORT-001")

    def test_writeoff_history_report_view_is_protected_for_unauthenticated_user(self):
        self.create_writeoff_record(document_number="WO-REPORT-001")

        response = self.client.get(self.report_url)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class DroneWriteOffReasonTests(APITestCase):
    def setUp(self):
        self.admin_user = AdminUserFactory()

        self.drone = DroneFactory(status="ACTIVE")
        DroneSpecFactory(drone=self.drone)

        self.detail_url = reverse("drones:drone-detail", kwargs={"pk": self.drone.pk})
        self.client.force_authenticate(self.admin_user)

    def _write_off(self, **overrides):
        payload = {
            "status": "WRITTEN_OFF",
            "writeoff_reason": WriteOffRecord.Reason.LOSS,
            "written_off_at": "2026-05-17",
        }
        payload.update(overrides)

        return self.client.patch(self.detail_url, payload, format="json")

    def test_each_canonical_reason_can_be_selected_and_saved(self):
        canonical_reasons = [
            WriteOffRecord.Reason.LOSS,
            WriteOffRecord.Reason.DESTRUCTION,
            WriteOffRecord.Reason.DAMAGE,
        ]

        for reason in canonical_reasons:
            with self.subTest(reason=reason):
                drone = DroneFactory(status="ACTIVE")
                DroneSpecFactory(drone=drone)
                detail_url = reverse("drones:drone-detail", kwargs={"pk": drone.pk})

                response = self.client.patch(
                    detail_url,
                    {
                        "status": "WRITTEN_OFF",
                        "writeoff_reason": reason,
                        "written_off_at": "2026-05-17",
                    },
                    format="json",
                )

                self.assertEqual(response.status_code, status.HTTP_200_OK)

                writeoff_record = WriteOffRecord.objects.get(drone=drone)
                self.assertEqual(writeoff_record.reason, reason)

    def test_reason_and_notes_are_saved(self):
        response = self._write_off(
            writeoff_reason=WriteOffRecord.Reason.DAMAGE,
            writeoff_reason_description="Severe frame damage beyond repair.",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        writeoff_record = WriteOffRecord.objects.get(drone=self.drone)
        self.assertEqual(writeoff_record.reason, WriteOffRecord.Reason.DAMAGE)
        self.assertEqual(
            writeoff_record.reason_description,
            "Severe frame damage beyond repair.",
        )

    def test_reason_is_visible_from_writeoff_record_in_detail(self):
        self._write_off(
            writeoff_reason=WriteOffRecord.Reason.DESTRUCTION,
            writeoff_reason_description="Destroyed by enemy fire.",
        )

        response = self.client.get(self.detail_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        writeoff_data = response.data["writeoff_record"]
        self.assertEqual(writeoff_data["reason"], WriteOffRecord.Reason.DESTRUCTION)
        self.assertEqual(writeoff_data["reason_label"], "Destruction")
        self.assertEqual(
            writeoff_data["reason_description"],
            "Destroyed by enemy fire.",
        )

    def test_other_reason_with_custom_description_is_accepted(self):
        response = self._write_off(
            writeoff_reason=WriteOffRecord.Reason.OTHER,
            writeoff_reason_description="Repurposed for spare parts.",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        writeoff_record = WriteOffRecord.objects.get(drone=self.drone)
        self.assertEqual(writeoff_record.reason, WriteOffRecord.Reason.OTHER)
        self.assertEqual(
            writeoff_record.reason_description,
            "Repurposed for spare parts.",
        )

    def test_other_reason_requires_custom_description(self):
        response = self._write_off(writeoff_reason=WriteOffRecord.Reason.OTHER)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("writeoff_reason_description", response.data)
        self.assertFalse(WriteOffRecord.objects.filter(drone=self.drone).exists())

    def test_other_reason_with_blank_description_is_rejected(self):
        response = self._write_off(
            writeoff_reason=WriteOffRecord.Reason.OTHER,
            writeoff_reason_description="   ",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("writeoff_reason_description", response.data)

    def test_invalid_reason_code_is_rejected(self):
        response = self._write_off(writeoff_reason="NOT_A_REAL_REASON")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("writeoff_reason", response.data)
        self.assertFalse(WriteOffRecord.objects.filter(drone=self.drone).exists())

    def test_blank_reason_is_rejected(self):
        response = self._write_off(writeoff_reason="")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("writeoff_reason", response.data)
        self.assertIn(
            "required when drone is decommissioned",
            str(response.data["writeoff_reason"][0]),
        )
        self.assertFalse(WriteOffRecord.objects.filter(drone=self.drone).exists())

    def test_status_history_uses_human_readable_reason_label(self):
        self._write_off(writeoff_reason=WriteOffRecord.Reason.DAMAGE)

        history = DroneStatusHistory.objects.get(drone=self.drone)
        self.assertEqual(history.reason, "Critical damage")


class WriteOffRecordModelTests(APITestCase):
    def setUp(self):
        self.drone = DroneFactory(status="ACTIVE")

    def test_model_rejects_invalid_reason_code(self):
        record = WriteOffRecord(drone=self.drone, reason="BOGUS")

        with self.assertRaises(ValidationError) as ctx:
            record.full_clean()

        self.assertIn("reason", ctx.exception.error_dict)

    def test_model_rejects_blank_reason(self):
        record = WriteOffRecord(drone=self.drone, reason="")

        with self.assertRaises(ValidationError) as ctx:
            record.full_clean()

        self.assertIn("reason", ctx.exception.error_dict)

    def test_model_requires_description_for_other_reason(self):
        record = WriteOffRecord(drone=self.drone, reason=WriteOffRecord.Reason.OTHER)

        with self.assertRaises(ValidationError) as ctx:
            record.full_clean()

        self.assertIn("reason_description", ctx.exception.error_dict)

    def test_model_accepts_canonical_reason(self):
        record = WriteOffRecord(drone=self.drone, reason=WriteOffRecord.Reason.LOSS)
        record.save()

        self.assertEqual(record.reason_label, "Loss")
        self.assertTrue(
            WriteOffRecord.objects.filter(pk=record.pk).exists(),
        )


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

    def test_filtering_is_firmware_outdated(self):
        outdated_drone = DroneFactory(military_unit=self.military_unit)
        DroneSpecFactory(drone=outdated_drone, is_firmware_outdated=True)

        response = self.client.get(self.create_url, {"is_firmware_outdated": "true"})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results_ids = [item["id"] for item in response.data["results"]]

        self.assertIn(outdated_drone.id, results_ids)

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


class DroneModelTests(APITestCase):
    def setUp(self):
        self.create_url = reverse("drones:drone-model-create")
        self.base_payload = {
            "name": "Test Model Name",
            "manufacturer": "Test Manufacturer",
            "supported_classifications": [
                Drone.CLASSIFICATION_RECONNAISSANCE,
                Drone.CLASSIFICATION_COMBAT,
            ],
        }
        self.user = AdminUserFactory()
        self.client.force_authenticate(self.user)

    def test_create_drone_model(self):
        response = self.client.post(self.create_url, self.base_payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(DroneModel.objects.count(), 1)

        drone_model = DroneModel.objects.first()
        self.assertEqual(drone_model.name, self.base_payload.get("name"))

    def test_create_drone_model_without_supported_classifications(self):
        payload = copy.deepcopy(self.base_payload)
        payload.pop("supported_classifications")

        response = self.client.post(self.create_url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("supported_classifications", response.data)

    def test_create_drone_model_with_empty_supported_classifications(self):
        payload = copy.deepcopy(self.base_payload)
        payload["supported_classifications"] = []

        response = self.client.post(self.create_url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("supported_classifications", response.data)

    def test_create_drone_model_with_wrong_classification(self):
        payload = copy.deepcopy(self.base_payload)
        payload["supported_classifications"] = ["unknown classification"]

        response = self.client.post(self.create_url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("supported_classifications", response.data)


class DroneClassificationValidationTests(APITestCase):
    def setUp(self):
        self.create_url = reverse("drones:drone-create")
        self.military_unit = MilitaryUnitFactory()
        self.drone_model = DroneModelFactory()
        self.base_payload = {
            "serial_number": "Test Serial Number",
            "inventory_number": "Test Inventory Number",
            "name": "Test Name",
            "drone_model": self.drone_model.id,
            "classification": self.drone_model.supported_classifications[0],
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
        self.drone = DroneFactory(drone_model=self.drone_model)
        self.detail_url = reverse("drones:drone-detail", kwargs={"pk": self.drone.pk})
        self.user = AdminUserFactory()
        self.client.force_authenticate(self.user)

    def test_create_drone_with_allowed_classification(self):
        response = self.client.post(self.create_url, self.base_payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_create_drone_with_not_allowed_classififcation(self):
        payload = copy.deepcopy(self.base_payload)
        payload["classification"] = "unknown"

        response = self.client.post(self.create_url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("classification", response.data)

    def test_update_drone_classification_to_allowed(self):
        response = self.client.patch(
            self.detail_url,
            {"classification": self.drone_model.supported_classifications[1]},
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_update_drone_classification_to_empty(self):
        response = self.client.patch(self.detail_url, {"classification": ""})

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("classification", response.data)

    def test_update_drone_classification_to_not_allowed(self):
        response = self.client.patch(self.detail_url, {"classification": "unknown"})

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("classification", response.data)


class DroneDataExportsTests(APITestCase):
    def setUp(self):
        self.export_url = reverse("drones:drone-export")
        self.admin_user = AdminUserFactory()
        self.military_unit = MilitaryUnitFactory(name="Unit A")

        self.drone1 = DroneFactory(
            serial_number="SN-001", status="ACTIVE", military_unit=self.military_unit
        )
        self.drone2 = DroneFactory(
            serial_number="SN-002", status="DAMAGED", military_unit=self.military_unit
        )

        self.client.force_authenticate(self.admin_user)

    def test_export_csv_success_and_format(self):
        response = self.client.get(self.export_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response["Content-Type"], "text/csv")
        self.assertIn(
            'attachment; filename="drones_export.csv"', response["Content-Disposition"]
        )

        content = b"".join(response.streaming_content).decode("utf-8")
        csv_reader = csv.reader(io.StringIO(content))
        rows = list(csv_reader)

        self.assertEqual(rows[0][0], "ID")
        self.assertEqual(rows[0][1], "Serial Number")
        self.assertEqual(len(rows), 3)

        content_str = content.lower()
        self.assertIn("sn-001", content_str)
        self.assertIn("sn-002", content_str)
        self.assertIn("unit a", content_str)

    def test_export_csv_with_filters(self):
        response = self.client.get(self.export_url, {"status": "ACTIVE"})

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        content = b"".join(response.streaming_content).decode("utf-8")
        content_str = content.lower()

        self.assertIn("sn-001", content_str)
        self.assertNotIn("sn-002", content_str)


class DroneDataImportTests(APITestCase):
    def setUp(self):
        self.import_url = reverse("drones:drone-import")

        self.admin_user = AdminUserFactory()
        self.military_unit = MilitaryUnitFactory(name="Test Unit 123")
        DroneModelFactory(name="DJI", supported_classifications=["RECONNAISSANCE"])
        DroneModelFactory(name="Custom", supported_classifications=["COMBAT"])
        self.client.force_authenticate(self.admin_user)

    def _generate_csv_file(self, data_rows, headers=None, filename="drones.csv"):
        if headers is None:
            headers = [
                "Serial Number",
                "Inventory Number",
                "Name",
                "Model",
                "Military Unit",
                "Acquired At",
            ]
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(headers)
        writer.writerows(data_rows)

        return SimpleUploadedFile(
            filename, output.getvalue().encode("utf-8"), content_type="text/csv"
        )

    def test_import_successful(self):
        csv_file = self._generate_csv_file(
            [
                [
                    "SN-IMP-01",
                    "INV-01",
                    "Mavic 3",
                    "DJI",
                    "Test Unit 123",
                    "2026-05-10",
                ],
                [
                    "SN-IMP-02",
                    "INV-02",
                    "FPV 7",
                    "Custom",
                    "Test Unit 123",
                    "2026-05-11",
                ],
            ]
        )

        response = self.client.post(
            self.import_url, {"file": csv_file}, format="multipart"
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["added_count"], 2)
        self.assertEqual(len(response.data["errors"]), 0)

        self.assertTrue(Drone.objects.filter(serial_number="SN-IMP-01").exists())
        self.assertTrue(Drone.objects.filter(serial_number="SN-IMP-02").exists())

        drone = Drone.objects.get(serial_number="SN-IMP-01")
        self.assertIsNotNone(drone.spec)

    def test_import_rejects_non_extension(self):
        txt_file = self._generate_csv_file(
            [["SN-01", "INV-01", "Name", "Model", "Unit", "2026-01-01"]],
            filename="drones.txt",
        )

        response = self.client.post(
            self.import_url, {"file": txt_file}, format="multipart"
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("file", response.data)

    def test_import_fails_on_missing_required_columns(self):
        bad_headers_file = self._generate_csv_file(
            [["SN-01", "INV-01", "Name", "Model", "2026-01-01"]],
            headers=[
                "Serial Number",
                "Inventory Number",
                "Name",
                "Model",
                "Acquired At",
            ],
        )

        response = self.client.post(
            self.import_url, {"file": bad_headers_file}, format="multipart"
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("error", response.data)
        self.assertIn("Invalid file format", response.data["error"])

    def test_import_skips_duplicate_serial_numbers(self):
        DroneFactory(serial_number="EXISTING-SN")

        csv_file = self._generate_csv_file(
            [
                [
                    "EXISTING-SN",
                    "INV-01",
                    "Mavic 3",
                    "DJI",
                    "Test Unit 123",
                    "2026-05-10",
                ],
                ["NEW-SN", "INV-02", "FPV", "Custom", "Test Unit 123", "2026-05-11"],
            ]
        )

        response = self.client.post(
            self.import_url, {"file": csv_file}, format="multipart"
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["added_count"], 1)
        self.assertEqual(len(response.data["errors"]), 1)
        self.assertIn("already exists", response.data["errors"][0]["error"])
        self.assertEqual(response.data["errors"][0]["row"], 2)

    def test_import_skips_unknown_military_unit(self):
        csv_file = self._generate_csv_file(
            [["SN-001", "INV-01", "Mavic 3", "DJI", "UNKNOWN UNIT", "2026-05-10"]]
        )

        response = self.client.post(
            self.import_url, {"file": csv_file}, format="multipart"
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["added_count"], 0)
        self.assertEqual(len(response.data["errors"]), 1)
        self.assertIn("not found in database", response.data["errors"][0]["error"])

    def test_import_skips_rows_with_empty_required_fields(self):
        csv_file = self._generate_csv_file(
            [["", "INV-01", "Mavic 3", "DJI", "Test Unit 123", "2026-05-10"]]
        )

        response = self.client.post(
            self.import_url, {"file": csv_file}, format="multipart"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["added_count"], 0)
        self.assertEqual(len(response.data["errors"]), 1)
        self.assertIn(
            "Missing one or more required fields", response.data["errors"][0]["error"]
        )
