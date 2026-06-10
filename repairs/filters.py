import django_filters

from .models import DefectReport


class DefectFilter(django_filters.FilterSet):
    class Meta:
        model = DefectReport
        fields = {
            "drone": ["exact"],
            "severity": ["exact"],
            "defect_type": ["exact"],
            "reporter": ["exact"],
        }
