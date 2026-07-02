from django.db import transaction
from django.db.models.signals import post_delete, post_init, pre_save
from django.dispatch import receiver

from .models import VideoMetadata


def _safe_delete_file(storage, file_name):
    try:
        if storage.exists(file_name):
            storage.delete(file_name)
    except Exception:
        pass


@receiver(post_init, sender=VideoMetadata)
def store_initial_file(sender, instance, **kwargs):
    instance._initial_file_name = instance.file.name if instance.file else None


@receiver(post_delete, sender=VideoMetadata)
def delete_file_on_metadata_delete(sender, instance, **kwargs):
    if instance.file:
        storage = instance.file.storage
        file_name = instance.file.name
        transaction.on_commit(lambda: _safe_delete_file(storage, file_name))


@receiver(pre_save, sender=VideoMetadata)
def delete_old_file_on_replace(sender, instance, **kwargs):
    if not instance.pk:
        return

    initial_file_name = getattr(instance, "_initial_file_name", None)

    if initial_file_name and instance.file and initial_file_name != instance.file.name:
        storage = instance.file.storage
        transaction.on_commit(lambda: _safe_delete_file(storage, initial_file_name))
