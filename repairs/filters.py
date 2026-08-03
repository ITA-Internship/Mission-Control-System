"""Filter definitions for the repairs REST API.

Provides Django FilterSet classes for defect reports, repair orders, and
component replacements to allow clients to query and narrow down lists.
"""

import django_filters

from .models import ComponentReplacement, DefectReport, RepairOrder


class CharInFilter(django_filters.BaseInFilter, django_filters.CharFilter):
    """Match a field against a comma-separated list (``?field__in=A,B``)."""


class DefectFilter(django_filters.FilterSet):
    """Filter specifications for the DefectReport list API."""

    # `status__in` lets callers request several lifecycle states at once — the
    # dashboard uses it to count/list only *open* defects (REPORTED,IN_PROGRESS)
    # rather than every defect ever reported.
    status__in = CharInFilter(field_name="status", lookup_expr="in")

    class Meta:
        model = DefectReport
        fields = {
            "drone": ["exact"],
            "severity": ["exact"],
            "defect_type": ["exact"],
            "reporter": ["exact"],
            "status": ["exact"],
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
