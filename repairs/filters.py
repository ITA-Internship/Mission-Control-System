"""Filter definitions for the repairs REST API.

Provides Django FilterSet classes for defect reports, repair orders, and
component replacements to allow clients to query and narrow down lists.
"""

import django_filters

from .models import ComponentReplacement, DefectReport, RepairOrder


class DefectFilter(django_filters.FilterSet):
    """Filter specifications for the DefectReport list API."""

    class Meta:
        model = DefectReport
        fields = {
            "drone": ["exact"],
            "severity": ["exact"],
            "defect_type": ["exact"],
            "reporter": ["exact"],
        }


class ComponentReplacementFilter(django_filters.FilterSet):
    """Filter specifications for the ComponentReplacement APIs.

    Includes custom start_date and end_date fields for temporal querying.
    """

    start_date = django_filters.DateTimeFilter(
        field_name="replaced_at",
        lookup_expr="gte",
    )
    end_date = django_filters.DateTimeFilter(
        field_name="replaced_at",
        lookup_expr="lte",
    )

    class Meta:
        model = ComponentReplacement
        fields = {
            "drone": ["exact"],
            "component_type": ["exact"],
            "replaced_by": ["exact"],
        }


class RepairOrderFilter(django_filters.FilterSet):
    """Filter specifications for the RepairOrder list API."""

    class Meta:
        model = RepairOrder
        fields = {
            "drone": ["exact"],
            "status": ["exact"],
            "defect_report": ["exact"],
            "assigned_to": ["exact"],
            "created_at": ["gte", "lte"],
        }
