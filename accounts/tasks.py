"""Asynchronous background tasks for email notifications."""

from celery import shared_task
from django.conf import settings
from django.core.mail import send_mail


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def send_email_task(self, subject, message, recipient_list, from_email=None):
    """Send an email asynchronously with automatic retries on failure.

    This task uses Django's built-in mail framework. If an SMTP or network
    error occurs, the task will automatically retry up to 3 times with a
    60-second delay between attempts.

    Args:
        self: The bound Celery task instance (used for retries).
        subject (str): The subject line of the email.
        message (str): The plain text body of the email.
        recipient_list (list): A list of recipient email addresses.
        from_email (str): The sender's email address. Defaults to
            settings.DEFAULT_FROM_EMAIL if not provided.

    Raises:
        Exception: Catches any email sending errors and triggers a task retry.
    """
    try:
        send_mail(
            subject=subject,
            message=message,
            from_email=from_email or settings.DEFAULT_FROM_EMAIL,
            recipient_list=recipient_list,
            fail_silently=False,
        )
    except Exception as exc:
        self.retry(exc=exc)
