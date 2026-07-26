"""Define filters for drone inventory and write-off audit endpoints.

Classes:
    DroneFilter: Filter drone inventory and hide inactive drones by default.
    WriteOffRecordFilter: Filter write-off audit records by drone, user, mission,
        dates, document number, and reason.
"""

import django_filters

from .models import Drone, WriteOffRecord


class DroneFilter(django_filters.FilterSet):
    """Filter drone inventory by identity, status, model, unit, and spec fields.

    Inactive drones are excluded from default inventory results unless the
    request explicitly includes a status filter. This keeps standard inventory
    views focused on active assets while still allowing targeted inactive-status
    queries.
    """

    serial_number = django_filters.CharFilter(lookup_expr="icontains", max_length=100)
    inventory_number = django_filters.CharFilter(
        lookup_expr="icontains", max_length=100
    )
    military_unit = django_filters.CharFilter(lookup_expr="icontains", max_length=100)

    is_firmware_outdated = django_filters.BooleanFilter(
        field_name="spec__is_firmware_outdated"
    )

    class Meta:
        """Configure Drone fields and lookup expressions supported by the filter."""

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
        """Return filtered drones while hiding inactive inventory by default."""
        parent_qs = super().qs
        has_status_filter = self.data and self.data.get("status")

        if not has_status_filter:
            return parent_qs.filter(status__in=Drone.ACTIVE_STATUSES)

        return parent_qs


class WriteOffRecordFilter(django_filters.FilterSet):
    """Filter write-off audit records by drone, author, mission, dates, and reason."""

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
        """Configure fields supported by the write-off audit filter."""

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
