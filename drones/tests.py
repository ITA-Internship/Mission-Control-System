from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from drones.models import Drone, DroneSpec


class DroneCreateTests(APITestCase):

    def test_create_drone_with_spec(self):
        payload = {
            "serial_number": "Test Serial Number",
            "inventory_number": "Test Inventory Number",
            "name": "Test Name",
            "model": "Test Model",
            "status": "ACTIVE",
            "acquired_at": "2026-05-09",

            "spec": {
                "frame_type": "Test Frame",
                "motor_model": "Test Motor Model",
                "battery_type": "Test Battery Type",
                "battery_capacity_mah": 1500,
                "camera_model": "Test Camera Model",
                "flight_controller": "Test Controller",
                "max_speed_kmh": "12.5",
                "max_range_km": "130",
                "max_flight_time": "20",
                "frequency_mhz": "1000",
                "payload_capacity_g": "100"
            }
        }

        response = self.client.post(reverse("drones:drone-create"), payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Drone.objects.count(),1)
        self.assertEqual(DroneSpec.objects.count(),1)

        drone = Drone.objects.first()

        self.assertEqual(drone.model, "Test Model")
        self.assertEqual(drone.spec.frame_type,"Test Frame")


    def test_create_drone_missing_required_field(self):
        payload = {
            "inventory_number": "Test Inventory Number",
            "name": "Test Name",
            "model": "Test Model",
            "status": "ACTIVE",
            "acquired_at": "2026-05-09",
            "spec": {
                "frame_type": "Test Frame",
                "motor_model": "Test Motor Model",
                "battery_type": "Test Battery Type",
                "battery_capacity_mah": 1500,
                "camera_model": "Test Camera Model"
            }
        }

        response = self.client.post(reverse("drones:drone-create"), payload, format="json")

        self.assertEqual(response.status_code, 400)


    def test_create_drone_duplicate_serial_number(self):
        Drone.objects.create(
            serial_number="Test Serial Number",
            inventory_number="Test Inventory Number",
            name="Drone",
            status="ACTIVE",
            acquired_at="2026-05-09",
        )

        payload = {
            "serial_number": "Test Serial Number",
            "inventory_number": "Test Inventory Number 2",
            "name": "Drone 2",
            "status": "ACTIVE",
            "acquired_at": "2026-05-09",
            "spec": {
                "frame_type": "Test Frame",
                "motor_model": "Test Motor Model",
                "battery_type": "Test Battery Type",
                "battery_capacity_mah": 1500,
                "camera_model": "Test Camera Model",
                "flight_controller": "Test Controller",
                "max_speed_kmh": "12.5",
                "max_range_km": "130",
                "max_flight_time": "20",
                "frequency_mhz": "1000",
                "payload_capacity_g": "100"
            }
        }

        response = self.client.post(reverse("drones:drone-create"), payload, format="json")

        self.assertEqual(response.status_code, 400)