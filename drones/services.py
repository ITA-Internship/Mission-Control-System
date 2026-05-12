from django.db import transaction

from .models import Drone, DroneSpec


@transaction.atomic
def create_drone_with_spec(drone_data, spec_data):
    drone = Drone.objects.create(**drone_data)
    DroneSpec.objects.create(drone=drone, **spec_data)

    return drone
