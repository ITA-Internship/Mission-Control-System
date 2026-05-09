from django.utils.crypto import get_random_string
from django.core.mail import send_mail
from django.conf import settings

def generate_initial_password() -> str:
    return get_random_string(length=12)

def send_activation_email(user, password: str) -> None:
    subject = "Your Account Has Been Created"
    message = (
        f"Welcome, {user.first_name}!\n\n"
        f"Your account in the system has been created..\n"
        f"Login: {user.username}\n"
        f"Temporary password: {password}\n\n"
    )

    send_mail(
        subject=subject,
        message=message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
        fail_silently=False,
    )
