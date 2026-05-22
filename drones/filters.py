import django_filters
from .models import Drone


class DroneFilter(django_filters.FilterSet):
    class Meta:
        model = Drone
        fields = {
            "serial_number" : ["icontains"],
            "inventory_number" : ["icontains"],
            "status" : ["exact"],
            "drone_model" : ["icontains"],
            "classification" : ["exact"],
            "military_unit" : ["exact"]
        }
