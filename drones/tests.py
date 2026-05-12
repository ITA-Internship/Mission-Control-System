from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from django.contrib.auth import get_user_model
import copy
from drones.models import Drone, DroneSpec

User = get_user_model()

class DroneCreateTests(APITestCase):
    def setUp(self):
        self.create_url = reverse("drones:drone-create")
        self.base_payload = {
            "serial_number": "Test Serial Number",
            "inventory_number": "Test Inventory Number",
            "name": "Test Name",
            "drone_model": "Test Model",
            "status": "ACTIVE",
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
                "payload_capacity_g": "100"
            }
        }
        self.user = User.objects.create_user(
            username="admin",
            password="12345",
            is_staff=True,
        )

        self.client.force_authenticate(self.user)


    def test_create_drone_with_spec(self):
        response = self.client.post(self.create_url, self.base_payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Drone.objects.count(),1)
        self.assertEqual(DroneSpec.objects.count(),1)

        drone = Drone.objects.first()

        self.assertEqual(drone.drone_model, "Test Model")
        self.assertEqual(drone.spec.frame_type,"Test Frame")


    def test_create_drone_missing_required_field(self):
        payload = copy.deepcopy(self.base_payload)
        payload.pop("serial_number")

        response = self.client.post(self.create_url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('serial_number', response.data)
        self.assertEqual(response.data['serial_number'][0].code, 'required')


    def test_create_drone_duplicate_serial_number(self):
        Drone.objects.create(
            serial_number=self.base_payload["serial_number"],
            inventory_number="Inventory Number",
            name="Drone",
            drone_model="Test Model",
            status="ACTIVE",
            acquired_at="2026-05-09",
        )

        response = self.client.post(self.create_url, self.base_payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('serial_number', response.data)
        self.assertEqual(response.data['serial_number'][0].code, 'unique')


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