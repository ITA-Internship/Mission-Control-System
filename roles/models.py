from django.db import models

ROLE_CODES = (
    ("ADMIN", "Admin"),
    ("COMMANDER", "Commander"),
    ("OPERATOR", "Operator"),
    ("TECHNICIAN", "Technician"),
    ("VIEWER", "Viewer"),
)

class Role(models.Model):
    code = models.CharField(max_length=50, unique=True, choices=ROLE_CODES)
    name = models.CharField(max_length=150)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


    def __str__(self) -> str:
        return f"{self.name} ({self.code})"
