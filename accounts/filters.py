"""Define filters for user and military unit list endpoints.

Classes:
    UserFilter: Filter users by role, unit, and active status.
    MilitaryUnitFilter: Filter military units by active status.
"""

import django_filters

from .models import MilitaryUnit, User


class UserFilter(django_filters.FilterSet):
    """Filter users by role, unit, and active status.

    Role and unit can be filtered either by primary key (``role``, ``unit``) or
    by their catalog code (``role_code``, ``unit_code``) for convenience.
    """

    role_code = django_filters.CharFilter(
        field_name="role__code",
        lookup_expr="iexact",
    )
    unit_code = django_filters.CharFilter(
        field_name="unit__code",
        lookup_expr="iexact",
    )

    class Meta:
        """Configure User fields supported by the filter."""

        model = User
        fields = ("role", "role_code", "unit", "unit_code", "is_active")


class MilitaryUnitFilter(django_filters.FilterSet):
    """Filter military units by active status."""

    class Meta:
        """Configure MilitaryUnit fields supported by the filter."""

        model = MilitaryUnit
        fields = ("is_active",)
