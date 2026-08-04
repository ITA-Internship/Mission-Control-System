from django.urls import path

from .views import RoleListView

app_name = "roles"

urlpatterns = [
    path("", RoleListView.as_view(), name="role-list"),
]
