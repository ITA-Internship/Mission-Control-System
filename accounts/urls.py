from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    ActivateAccountAPIView,
    AuditLogViewSet,
    UserRegistrationView,
    UserRoleUpdateAPIView,
    UserStatusUpdateView,
)

app_name = "accounts"

router = DefaultRouter()
router.register(r"audit-log", AuditLogViewSet, basename="audit-log")

urlpatterns = [
    path("users/", UserRegistrationView.as_view(), name="user-create"),
    path(
        "users/<int:user_id>/role/",
        UserRoleUpdateAPIView.as_view(),
        name="user-role-update",
    ),
    path(
        "activate/<int:user_id>/<str:token>/",
        ActivateAccountAPIView.as_view(),
        name="account-activate",
    ),
    path("", include(router.urls)),
    path(
        "users/<int:pk>/status/",
        UserStatusUpdateView.as_view(),
        name="user-status-update",
    ),
]
