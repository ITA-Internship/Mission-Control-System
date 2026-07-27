"""Provide service-layer functions for user account management.

Functions:
    create_user_account: Creates a new user, profile, and triggers activation email.
    send_activation_email: Sends a one-time activation link to a user.
    is_admin_role: Checks if a specific role has admin privileges.
    count_admin_users: Returns the total number of admin users.
    count_admin_users_locked: Returns the total number of admin
        users with a database lock.
    set_user_password: Sets and saves a new password for a user.
    update_user_role: Safely changes a user's role with business logic validation.
    create_audit_log: Records an action in the system's audit log.
"""

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import transaction

from roles.models import ADMIN_CODE, Role

from .models import AuditLog, User, UserProfile, UserRoleAuditLog


@transaction.atomic
def create_user_account(validated_data: dict, created_by: User = None) -> User:
    """Create a new user account and associated profile, then send an activation email.
    Args:
        validated_data (dict): A dictionary containing user data.
        created_by (User): The user who created this account.
    Returns:
        User: The newly created user instance.
    """

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
    """Send a one-time activation link to the new user's email."""
    from .tasks import send_email_task
    from .tokens import account_activation_token_generator

    token = account_activation_token_generator.make_token(user)

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

    send_email_task.delay(
        subject=subject,
        message=message,
        recipient_list=[user.email],
    )


def is_admin_role(role: Role | None) -> bool:
    """Check if the given role is an admin role."""
    return bool(role and role.code == ADMIN_CODE)


def count_admin_users() -> int:
    """Return the count of users with admin role."""
    return User.objects.filter(role__code=ADMIN_CODE).count()


def count_admin_users_locked() -> int:
    """Return the count of users with the admin role and apply a database lock."""
    return User.objects.select_for_update().filter(role__code=ADMIN_CODE).count()


def set_user_password(user: User, raw_password: str) -> None:
    """Set and save a new password for the user.

    Persists the password and clears ``must_change_password`` in a single
    ``UPDATE``. An account is considered "pending activation" while it has no
    usable password, so setting one here is what activates the account.
    """
    user.set_password(raw_password)
    user.must_change_password = False
    user.save(update_fields=["password", "must_change_password"])


@transaction.atomic
def update_user_role(*, target_user: User, new_role_id: int, changed_by: User) -> User:
    """Update the role of a user while enforcing security and business rules.

    Args:
        target_user (User): The user whose role is to be updated.
        new_role_id (int): The ID of the new role to be assigned.
        changed_by (User): The user who is performing the role change.

    Returns:
        User: The updated user object.

    Raises:
        ValidationError: If the role_id is invalid, the user is inactive,
            or if the action violates admin role restrictions (e.g., removing
            the last admin).
    """
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
    """Create a new audit log entry in the database.

    Args:
        actor (User): The user who performed the action.
        action_type (str): The type of action performed (from AuditLog.ActionType).
        result (str): The result of the action (from AuditLog.ResultStatus).
        target_user (User): The user on whom the action was performed.
        description (str): A text description of the action. Defaults to "".
        request (HttpRequest): The HTTP request object, used to extract
            the IP address and User-Agent. Defaults to None.

    Returns:
        AuditLog: The created audit log instance.
    """
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
