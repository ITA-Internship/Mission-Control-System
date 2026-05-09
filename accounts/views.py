from rest_framework import generics

from .models import User
from .serializers import UserRegistrationSerializer
from .permissions import IsSystemAdmin

class UserRegistrationView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserRegistrationSerializer
    permission_classes = [IsSystemAdmin]