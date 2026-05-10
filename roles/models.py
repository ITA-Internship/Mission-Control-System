from django.db import models

ADMIN_CODE = "ADMIN"
COMMANDER_CODE = "COMMANDER"
OPERATOR_CODE = "OPERATOR"
TECHNICIAN_CODE = "TECHNICIAN"
VIEWER_CODE = "VIEWER"

ROLE_CODES = (
    (ADMIN_CODE, "Admin"),
    (COMMANDER_CODE, "Commander"),
    (OPERATOR_CODE, "Operator"),
    (TECHNICIAN_CODE, "Technician"),
    (VIEWER_CODE, "Viewer"),
)

class Role(models.Model):
    code = models.CharField(max_length=50, unique=True, choices=ROLE_CODES)
    name = models.CharField(max_length=150)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


    def __str__(self) -> str:
        return f"{self.name} ({self.code})"
