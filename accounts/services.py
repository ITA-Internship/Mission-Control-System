from django.conf import settings
from django.contrib.auth.tokens import default_token_generator
from django.core.exceptions import ValidationError
from django.core.mail import send_mail
from django.db import transaction

from roles.models import ADMIN_CODE, Role

from .models import AuditLog, User, UserProfile, UserRoleAuditLog


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

    create_audit_log(
        actor=created_by,
        action_type=AuditLog.ActionType.USER_CREATED,
        result=AuditLog.ResultStatus.SUCCESS,
        target_user=user,
        description=f"User {user.username} created.",
    )

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


def is_admin_role(role: Role | None) -> bool:
    return bool(role and role.code == ADMIN_CODE)


def count_admin_users() -> int:
    return User.objects.filter(role__code=ADMIN_CODE).count()


def count_admin_users_locked() -> int:
    return User.objects.select_for_update().filter(role__code=ADMIN_CODE).count()


@transaction.atomic
def update_user_role(*, target_user: User, new_role_id: int, changed_by: User) -> User:
    if not new_role_id:
        raise ValidationError({"role_id": ["This field is required."]})

    try:
        new_role = Role.objects.get(pk=new_role_id)
    except Role.DoesNotExist as exc:
        raise ValidationError({"role_id": ["Invalid role_id."]}) from exc

  
    locked_user = User.objects.select_for_update().get(pk=target_user.pk)
    previous_role = locked_user.role

    if not locked_user.is_active:
        raise ValidationError(
            {"role_id": ["Cannot change the role of an inactive user."]}
        )

    if previous_role_id := getattr(previous_role, "id", None):
        if previous_role_id == new_role.id:
            UserRoleAuditLog.objects.create(
                changed_by=changed_by,
                target_user=locked_user,
                previous_role=previous_role,
                new_role=new_role,
            )
            return locked_user

    was_admin = is_admin_role(previous_role)
    will_be_admin = is_admin_role(new_role)

    if changed_by.pk == locked_user.pk and was_admin and not will_be_admin:
        raise ValidationError(
            {"role_id": ["Admins cannot remove their own admin role."]}
        )

    if locked_user.is_superuser and was_admin and not will_be_admin:
        raise ValidationError(
            {"role_id": ["Cannot remove the admin role from the root account."]}
        )

    if was_admin and not will_be_admin and count_admin_users_locked() <= 1:
        raise ValidationError(
            {"role_id": ["Cannot change the last admin to a non-admin role."]}
        )

    locked_user.role = new_role
    locked_user.save(update_fields=["role", "updated_at"])

    UserRoleAuditLog.objects.create(
        changed_by=changed_by,
        target_user=locked_user,
        previous_role=previous_role,
        new_role=new_role,
    )

    create_audit_log(
        actor=changed_by,
        action_type=AuditLog.ActionType.ROLE_CHANGED,
        result=AuditLog.ResultStatus.SUCCESS,
        target_user=locked_user,
        description=f"Role changed from "
        f"{previous_role.name if previous_role else 'None'} to {new_role.name}.",
    )

    return locked_user


def create_audit_log(
    actor, action_type, result, target_user=None, description="", request=None
):
    ip_address = None
    user_agent = ""

    if request:
        user_agent = request.META.get("HTTP_USER_AGENT", "")

        x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
        if x_forwarded_for:
            ip_address = x_forwarded_for.split(",")[-1].strip()
        else:
            ip_address = request.META.get("REMOTE_ADDR")

    return AuditLog.objects.create(
        actor=actor if actor and actor.is_authenticated else None,
        target_user=target_user,
        action_type=action_type,
        result=result,
        description=description,
        ip_address=ip_address,
        user_agent=user_agent,
    )
