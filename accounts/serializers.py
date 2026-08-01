"""Serialize users, audit logs, and password reset actions.

Classes:
    UserRegistrationSerializer: Serializes data for the registration of
        new users.
    UserStatusUpdateSerializer: Serializes requests to activate or
        deactivate a user.
    UserRoleUpdateSerializer: Serializes requests to change a user's role.
    UserRoleUpdateResponseSerializer: Serializes the response data after
        a role update.
    AuditLogSerializer: Read-only serializer for audit log entries.
    UserMeSerializer: Serializes the current user's data and profile for
        retrieval and updates.
    ChangePasswordSerializer: Serializes requests to change the current
        user's password.
    AccountActivationSerializer: Serializes and validates the initial
        password submitted during account activation.
    PasswordResetRequestSerializer: Serializes requests to initiate a
        password reset process.
    PasswordResetConfirmSerializer: Serializes the new password to confirm
        a password reset.
"""

from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import transaction
from django.urls import reverse
from rest_framework import serializers

from .models import AuditLog, User, UserProfile
from .services import create_user_account
from .validators import validate_image_extension, validate_image_size


class UserRegistrationSerializer(serializers.ModelSerializer):
    """Provide serialization and validation for user registration requests."""

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
        """Validate that the provided username is unique."""
        if User.objects.filter(username__iexact=value).exists():
            raise serializers.ValidationError(
                "A user with that username already exists."
            )
        return value

    def validate_email(self, value):
        """Validate that the provided email address is unique."""
        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError("A user with that email already exists.")
        return value

    def create(self, validated_data):
        """Create and return a new user account."""
        request = self.context.get("request")
        created_by = request.user if request and hasattr(request, "user") else None

        return create_user_account(validated_data, created_by)


class UserStatusUpdateSerializer(serializers.Serializer):
    """Serialize user status update requests."""

    is_active = serializers.BooleanField(required=True)
    reason = serializers.CharField(required=False, allow_blank=True, max_length=255)


class UserRoleUpdateSerializer(serializers.Serializer):
    """Serialize user role update requests."""

    role_id = serializers.IntegerField(required=True, min_value=1)


class UserRoleUpdateResponseSerializer(serializers.ModelSerializer):
    """Serialize user role update responses."""

    role = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ("id", "username", "email", "role")

    def get_role(self, obj) -> dict | None:
        """Return the role details of the user."""
        if not obj.role:
            return None

        return {
            "id": obj.role.id,
            "code": obj.role.code,
            "name": obj.role.name,
        }


class AuditLogSerializer(serializers.ModelSerializer):
    """Serialize audit log entries for read-only API responses."""

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
    """Serialize the authenticated user's data along with their profile information."""

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
    role_name = serializers.CharField(source="role.name", read_only=True, default=None)
    role_code = serializers.CharField(source="role.code", read_only=True, default=None)
    unit_name = serializers.CharField(source="unit.name", read_only=True, default=None)
    unit_code = serializers.CharField(source="unit.code", read_only=True, default=None)
    created_by_username = serializers.CharField(
        source="created_by.username",
        read_only=True,
        default=None,
    )

    def validate_first_name(self, value):
        """Require a non-empty normalized first name for self-service updates."""
        normalized = value.strip()
        if not normalized:
            raise serializers.ValidationError("First name is required.")
        return normalized

    def validate_last_name(self, value):
        """Require a non-empty normalized last name for self-service updates."""
        normalized = value.strip()
        if not normalized:
            raise serializers.ValidationError("Last name is required.")
        return normalized

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
            "role_name",
            "role_code",
            "unit",
            "unit_name",
            "unit_code",
            "is_active",
            "must_change_password",
            "last_login",
            "created_at",
            "created_by_username",
        )
        read_only_fields = (
            "id",
            "username",
            "email",
            "role",
            "role_name",
            "role_code",
            "unit",
            "unit_name",
            "unit_code",
            "is_active",
            "must_change_password",
            "last_login",
            "created_at",
            "created_by_username",
            "is_staff",
            "is_superuser",
            "created_by",
        )

    @transaction.atomic
    def update(self, instance, validated_data):
        """Update the user instance and their associated profile data."""
        profile_data = validated_data.pop("profile", None)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        if profile_data is not None:
            profile, created = UserProfile.objects.get_or_create(user=instance)
            old_picture = profile.profile_picture
            old_picture_name = old_picture.name if old_picture else ""
            old_picture_storage = old_picture.storage if old_picture else None
            for attr, value in profile_data.items():
                setattr(profile, attr, value)
            profile.save()
            new_picture_name = (
                profile.profile_picture.name if profile.profile_picture else ""
            )
            if (
                old_picture_storage
                and old_picture_name
                and old_picture_name != new_picture_name
            ):
                transaction.on_commit(
                    lambda storage=old_picture_storage, name=old_picture_name: (
                        storage.delete(name)
                    )
                )
            instance.profile = profile

        return instance

    def to_representation(self, instance):
        """Expose profile pictures only through the protected account endpoint."""
        data = super().to_representation(instance)
        profile = getattr(instance, "profile", None)
        if profile and profile.profile_picture:
            data["profile_picture"] = reverse(
                "accounts:user-profile-picture",
                kwargs={"user_id": instance.pk},
            )
        else:
            data["profile_picture"] = None
        return data


class ChangePasswordSerializer(serializers.Serializer):
    """Serialize requests to change the user's password."""

    old_password = serializers.CharField(required=True, write_only=True)
    new_password = serializers.CharField(required=True, write_only=True)

    def validate_old_password(self, value):
        """Validate that the provided old password is correct."""
        user = self.context["request"].user
        if not user.check_password(value):
            raise serializers.ValidationError("Incorrect old password.")
        return value

    def validate_new_password(self, value):
        """Validate the new password against Django's built-in password validators."""
        user = self.context["request"].user
        if user.check_password(value):
            raise serializers.ValidationError(
                "New password must be different from the current password."
            )
        try:
            validate_password(value, user)
        except DjangoValidationError as exc:
            raise serializers.ValidationError(list(exc.messages))
        return value


class AccountActivationSerializer(serializers.Serializer):
    """Serialize account activation requests that set the initial password."""

    password = serializers.CharField(required=True, write_only=True)

    def validate_password(self, value):
        """Validate the initial password against Django's built-in validators."""
        user = self.context.get("user")
        try:
            validate_password(value, user)
        except DjangoValidationError as exc:
            raise serializers.ValidationError(list(exc.messages))
        return value


class PasswordResetRequestSerializer(serializers.Serializer):
    """Serialize requests to initiate a password reset."""

    email = serializers.EmailField(required=True)


class PasswordResetConfirmSerializer(serializers.Serializer):
    """Serialize requests to confirm a password reset with a new password."""

    new_password = serializers.CharField(required=True, write_only=True)

    def validate_new_password(self, value):
        """Validate the new password against Django's built-in password validators."""
        try:
            validate_password(value)
        except DjangoValidationError as exc:
            raise serializers.ValidationError(list(exc.messages))
        return value
