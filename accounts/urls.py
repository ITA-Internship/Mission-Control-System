from django.urls import path

from .views import ActivateAccountAPIView, UserRegistrationView, UserRoleUpdateAPIView

app_name = "accounts"

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
]
