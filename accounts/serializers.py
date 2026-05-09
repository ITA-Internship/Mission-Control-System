from rest_framework import serializers
from .models import User, UserProfile
from .services import generate_initial_password, send_activation_email

class UserRegistrationSerializer(serializers.ModelSerializer):
    rank = serializers.CharField(required=False, allow_blank=True)
    contact = serializers.CharField(required=False, allow_blank=True)
    profile_picture = serializers.URLField(required=False, allow_blank=True)

    class Meta:
        model = User
        fields = (
            'id',
            'username',
            'email',
            'first_name',
            'last_name',
            'role',
            'unit',
            'rank',
            'contact',
            'profile_picture',
        )
        read_only_fields = ('id',)

    @staticmethod
    def validate_username(self, value):
        if User.objects.filter(username__iexact=value).exists():
            raise serializers.ValidationError("A user with that username already exists.")
        return value

    @staticmethod
    def validate_email(self, value):
        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError("A user with that email already exists.")
        return value

    def create(self, validated_data):
        rank = validated_data.pop("rank", "")
        contact = validated_data.pop("contact", "")
        profile_picture = validated_data.pop("profile_picture", "")

        user = User(**validated_data)

        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            user.created_by = request.user

        password = generate_initial_password()
        user.set_password(password)
        user.save()

        if rank or contact or profile_picture:
            UserProfile.objects.create(
                user=user,
                rank=rank,
                contact=contact,
                profile_picture=profile_picture,
            )

        send_activation_email(user, password)

        return user