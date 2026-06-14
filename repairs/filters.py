import django_filters

from .models import ComponentReplacement, DefectReport


class DefectFilter(django_filters.FilterSet):
    class Meta:
        model = DefectReport
        fields = {
            "drone": ["exact"],
            "severity": ["exact"],
            "defect_type": ["exact"],
            "reporter": ["exact"],
        }


class ComponentReplacementFilter(django_filters.FilterSet):
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
