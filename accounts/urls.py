from django.urls import path
from .views import UserRegistrationView, ActivateAccountAPIView

app_name = 'accounts'

urlpatterns = [
    path('users/', UserRegistrationView.as_view(), name='user-create'),
    path('activate/<int:user_id>/<str:token>/', ActivateAccountAPIView.as_view(), name='account-activate'),]
