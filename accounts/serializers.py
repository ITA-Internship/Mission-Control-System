from rest_framework import serializers

from .models import User
from .services import create_user_account


class UserRegistrationSerializer(serializers.ModelSerializer):
    rank = serializers.CharField(required=False, allow_blank=True)
    contact = serializers.CharField(required=False, allow_blank=True)
    profile_picture = serializers.URLField(required=False, allow_blank=True)

    class Meta:
        model = User
        fields = (
            "id",
            "username",
            "email",
            "first_name",
            "last_name",
            "role",
            "unit",
            "rank",
            "contact",
            "profile_picture",
        )
        read_only_fields = ("id",)

    def validate_username(self, value):
        if User.objects.filter(username__iexact=value).exists():
            raise serializers.ValidationError(
                "A user with that username already exists."
            )
        return value

    def validate_email(self, value):
        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError("A user with that email already exists.")
        return value

    def create(self, validated_data):
        request = self.context.get("request")
        created_by = request.user if request and hasattr(request, "user") else None

        return create_user_account(validated_data, created_by)
