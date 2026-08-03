from django.test import override_settings
from rest_framework.test import APITestCase, APIRequestFactory, force_authenticate
from django.core.cache import cache
from drones.factories import AdminUserFactory
from accounts.views import AuditLogViewSet

@override_settings(REST_FRAMEWORK={
    "DEFAULT_AUTHENTICATION_CLASSES": ["rest_framework.authentication.SessionAuthentication"],
    "DEFAULT_THROTTLE_CLASSES": ["rest_framework.throttling.ScopedRateThrottle"],
    "DEFAULT_THROTTLE_RATES": {"audit_view": "2/min", "audit_export": "1/min"},
})
class DiagTest(APITestCase):
    def setUp(self):
        cache.clear()
        self.u = AdminUserFactory()
    def test_introspect(self):
        factory = APIRequestFactory()
        # Build the export view instance the way the router does
        export_view = AuditLogViewSet.as_view({"get": "export"},
            **{"throttle_classes": AuditLogViewSet.__dict__.get("throttle_classes"), "throttle_scope": "audit_export", "detail": False})
        req = factory.get("/api/accounts/audit-log/export/")
        force_authenticate(req, user=self.u)
        # Manually instantiate to inspect
        v = AuditLogViewSet(**{"throttle_scope": "audit_export"})
        v.action = "export"
        print("instance throttle_scope:", getattr(v, "throttle_scope", "MISSING"))
        from rest_framework.throttling import ScopedRateThrottle
        t = ScopedRateThrottle()
        t.scope = getattr(v, "throttle_scope", None)
        print("resolved scope:", t.scope)
        t.rate = t.get_rate()
        print("resolved rate:", t.rate)
    def test_list_rate(self):
        from django.urls import reverse
        url = reverse("accounts:audit-log-list")
        codes = [self.client.get(url, **{}) or 0 for _ in range(1)]
        self.client.force_authenticate(self.u)
        codes = [self.client.get(url).status_code for _ in range(4)]
        print("LIST @2/min statuses:", codes)
    def test_export_rate(self):
        from django.urls import reverse
        self.client.force_authenticate(self.u)
        url = reverse("accounts:audit-log-export")
        codes = [self.client.get(url).status_code for _ in range(3)]
        print("EXPORT @1/min statuses:", codes)
