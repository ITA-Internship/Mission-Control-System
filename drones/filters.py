import django_filters

from .models import Drone


class DroneFilter(django_filters.FilterSet):
    class Meta:
        model = Drone
        fields = {
            "serial_number": ["icontains"],
            "inventory_number": ["icontains"],
            "status": ["exact"],
            "drone_model": ["exact"],
            "drone_model__name": ["exact"],
            "classification": ["exact"],
            "military_unit": ["exact"],
            "military_unit__name": ["icontains"],
        }

    @property
    def qs(self):
        parent_qs = super().qs
        has_status_filter = self.data and self.data.get("status")

        if not has_status_filter:
            return parent_qs.exclude(status__in=Drone.INACTIVE_STATUSES)

        return parent_qs
