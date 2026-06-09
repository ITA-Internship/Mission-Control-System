from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import transaction
from rest_framework import serializers

from .models import AuditLog, User, UserProfile
from .services import create_user_account
from .validators import validate_image_extension, validate_image_size


class UserRegistrationSerializer(serializers.ModelSerializer):
    rank = serializers.CharField(required=False, allow_blank=True)
    contact = serializers.CharField(required=False, allow_blank=True)
    profile_picture = serializers.ImageField(
        required=False,
        allow_null=True,
        validators=[validate_image_size, validate_image_extension],
    )

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


class UserStatusUpdateSerializer(serializers.Serializer):
    is_active = serializers.BooleanField(required=True)
    reason = serializers.CharField(required=False, allow_blank=True, max_length=255)


class UserRoleUpdateSerializer(serializers.Serializer):
    role_id = serializers.IntegerField(required=True, min_value=1)


class UserRoleUpdateResponseSerializer(serializers.ModelSerializer):
    role = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ("id", "username", "email", "role")

    def get_role(self, obj):
        if not obj.role:
            return None

        return {
            "id": obj.role.id,
            "code": obj.role.code,
            "name": obj.role.name,
        }


class AuditLogSerializer(serializers.ModelSerializer):
    actor_username = serializers.CharField(source="actor.username", read_only=True)
    target_user_username = serializers.CharField(
        source="target_user.username", read_only=True
    )

    class Meta:
        model = AuditLog

        fields = [
            "id",
            "actor",
            "actor_username",
            "target_user",
            "target_user_username",
            "action_type",
            "result",
            "description",
            "ip_address",
            "user_agent",
            "created_at",
        ]


class UserMeSerializer(serializers.ModelSerializer):
    rank = serializers.CharField(
        source="profile.rank", required=False, allow_blank=True
    )
    contact = serializers.CharField(
        source="profile.contact", required=False, allow_blank=True
    )
    profile_picture = serializers.ImageField(
        source="profile.profile_picture",
        required=False,
        allow_null=True,
        validators=[validate_image_size, validate_image_extension],
    )

    class Meta:
        model = User
        fields = (
            "id",
            "username",
            "email",
            "first_name",
            "last_name",
            "rank",
            "contact",
            "profile_picture",
            "role",
            "unit",
            "is_active",
        )
        read_only_fields = (
            "id",
            "username",
            "email",
            "role",
            "unit",
            "is_active",
            "is_staff",
            "is_superuser",
            "created_by",
        )

    @transaction.atomic
    def update(self, instance, validated_data):
        profile_data = validated_data.pop("profile", None)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        if profile_data is not None:
            profile, created = UserProfile.objects.get_or_create(user=instance)
            for attr, value in profile_data.items():
                setattr(profile, attr, value)
            profile.save()

        return instance


class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(required=True, write_only=True)
    new_password = serializers.CharField(required=True, write_only=True)

    def validate_old_password(self, value):
        user = self.context["request"].user
        if not user.check_password(value):
            raise serializers.ValidationError("Incorrect old password.")
        return value

    def validate_new_password(self, value):
        user = self.context["request"].user
        try:
            validate_password(value, user)
        except DjangoValidationError as exc:
            raise serializers.ValidationError(list(exc.messages))
        return value


class PasswordResetRequestSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)


class PasswordResetConfirmSerializer(serializers.Serializer):
    new_password = serializers.CharField(required=True, write_only=True)

    def validate_new_password(self, value):
        try:
            validate_password(value)
        except DjangoValidationError as exc:
            raise serializers.ValidationError(list(exc.messages))
        return value
