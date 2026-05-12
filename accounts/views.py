from rest_framework import generics

from .models import User
from .serializers import UserRegistrationSerializer
from .permissions import IsSystemAdmin
from django.shortcuts import get_object_or_404
from django.contrib.auth.tokens import default_token_generator
from django.http import HttpResponse
from django.middleware.csrf import get_token

from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny

class UserRegistrationView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserRegistrationSerializer
    permission_classes = [IsSystemAdmin]


class ActivateAccountAPIView(APIView):
    permission_classes = [AllowAny]

    def post(self, request, user_id, token):
        user = get_object_or_404(User, pk=user_id)

        if not default_token_generator.check_token(user, token):
            return Response(
                {"detail": "Invalid or expired activation link."},
                status=status.HTTP_400_BAD_REQUEST
            )

        new_password = request.data.get("password")
        if not new_password:
            return Response(
                {"password": ["This field is required."]},
                status=status.HTTP_400_BAD_REQUEST
            )

        user.set_password(new_password)
        user.save()

        return Response(
            {"detail": "Your account has been activated. You can now log in."},
            status=status.HTTP_200_OK
        )
