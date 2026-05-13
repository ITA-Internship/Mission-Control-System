from django.conf import settings
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from django.db import transaction

from .models import User, UserProfile


@transaction.atomic
def create_user_account(validated_data: dict, created_by: User = None) -> User:
    rank = validated_data.pop("rank", "")
    contact = validated_data.pop("contact", "")
    profile_picture = validated_data.pop("profile_picture", "")

    user = User(**validated_data)
    if created_by:
        user.created_by = created_by

    user.set_unusable_password()
    user.save()

    if rank or contact or profile_picture:
        UserProfile.objects.create(
            user=user,
            rank=rank,
            contact=contact,
            profile_picture=profile_picture,
        )

    send_activation_email(user)

    return user


def send_activation_email(user) -> None:
    token = default_token_generator.make_token(user)

    frontend_url = getattr(settings, "FRONTEND_URL", "http://localhost:3000")

    activation_url = f"{frontend_url}/activate/{user.pk}/{token}/"

    subject = "Your Account Has Been Created"
    message = (
        f"Welcome, {user.first_name}!\n\n"
        f"Your account in the system has been created.\n"
        f"Login: {user.username}\n\n"
        f"Please click the link below to set your password "
        "and activate your account:\n"
        f"{activation_url}\n\n"
        f"For security reasons, this link is for one-time use only."
    )

    send_mail(
        subject=subject,
        message=message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
        fail_silently=False,
    )
