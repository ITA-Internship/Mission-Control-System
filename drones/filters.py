import django_filters

from .models import Drone, WriteOffRecord


class DroneFilter(django_filters.FilterSet):
    is_firmware_outdated = django_filters.BooleanFilter(
        field_name="spec__is_firmware_outdated"
    )

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
            "spec__max_speed_kmh": ["exact", "gte", "lte"],
            "spec__typical_range_km": ["exact", "gte", "lte"],
            "spec__max_range_km": ["exact", "gte", "lte"],
            "spec__typical_flight_time_min": ["exact", "gte", "lte"],
            "spec__max_flight_time_min": ["exact", "gte", "lte"],
            "spec__payload_capacity_g": ["exact", "gte", "lte"],
        }

    @property
    def qs(self):
        parent_qs = super().qs
        has_status_filter = self.data and self.data.get("status")

        if not has_status_filter:
            return parent_qs.exclude(status__in=Drone.INACTIVE_STATUSES)

        return parent_qs


class WriteOffRecordFilter(django_filters.FilterSet):
    drone = django_filters.NumberFilter(field_name="drone_id")
    drone_serial_number = django_filters.CharFilter(
        field_name="drone__serial_number",
        lookup_expr="icontains",
    )
    drone_inventory_number = django_filters.CharFilter(
        field_name="drone__inventory_number",
        lookup_expr="icontains",
    )
    authorized_by = django_filters.NumberFilter(field_name="authorized_by_id")
    related_mission = django_filters.NumberFilter(field_name="related_mission_id")

    written_off_at_after = django_filters.DateFilter(
        field_name="written_off_at",
        lookup_expr="gte",
    )
    written_off_at_before = django_filters.DateFilter(
        field_name="written_off_at",
        lookup_expr="lte",
    )

    document_number = django_filters.CharFilter(
        field_name="document_number",
        lookup_expr="icontains",
    )
    reason = django_filters.CharFilter(
        field_name="reason",
        lookup_expr="icontains",
    )

    class Meta:
        model = WriteOffRecord
        fields = (
            "drone",
            "drone_serial_number",
            "drone_inventory_number",
            "authorized_by",
            "related_mission",
            "written_off_at_after",
            "written_off_at_before",
            "document_number",
            "reason",
        )
