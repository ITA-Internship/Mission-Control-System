"""URL routing for user accounts, profile management,
password recovery, and audit logs."""

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    ActivateAccountAPIView,
    AuditLogViewSet,
    ChangePasswordView,
    MilitaryUnitListView,
    MilitaryUnitDetailView,
    MilitaryUnitListCreateView,
    PasswordResetConfirmView,
    PasswordResetRequestView,
    ProtectedProfilePictureView,
    UserListCreateView,
    UserMeView,
    UserRoleUpdateAPIView,
    UserStatusUpdateView,
)

app_name = "accounts"

router = DefaultRouter()
router.register(r"audit-log", AuditLogViewSet, basename="audit-log")

urlpatterns = [
    path("users/", UserListCreateView.as_view(), name="user-create"),
    path(
        "military-units/",
        MilitaryUnitListCreateView.as_view(),
        name="military-unit-list",
    ),
    path(
        "military-units/<int:pk>/",
        MilitaryUnitDetailView.as_view(),
        name="military-unit-detail",
    ),
    path(
        "users/me/",
        UserMeView.as_view(),
        name="user-me",
    ),
    path(
        "users/me/change-password/",
        ChangePasswordView.as_view(),
        name="change-password",
    ),
    path(
        "users/password-reset/",
        PasswordResetRequestView.as_view(),
        name="password-reset-request",
    ),
    path(
        "users/password-reset-confirm/<str:uidb64>/<str:token>/",
        PasswordResetConfirmView.as_view(),
        name="password-reset-confirm",
    ),
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
    path(
        "users/<int:user_id>/profile-picture/",
        ProtectedProfilePictureView.as_view(),
        name="user-profile-picture",
    ),
    path(
        "military-units/",
        MilitaryUnitListView.as_view(),
        name="military-unit-list",
    ),
]
