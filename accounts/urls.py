from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    path('users/', views.UserRegistrationView.as_view(), name='user-create'),
]