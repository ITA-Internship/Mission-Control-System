from django.db import transaction
from django.db.models.signals import post_delete, pre_save
from django.dispatch import receiver

from .models import VideoMetadata


def _safe_delete_file(storage, file_name):
    try:
        if storage.exists(file_name):
            storage.delete(file_name)
    except Exception:
        pass


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

    try:
        old_instance = VideoMetadata.objects.filter(pk=instance.pk).first()
        if not old_instance:
            return

        old_file = old_instance.file
    except Exception:
        return

    if old_file and old_file.name != instance.file.name:
        storage = old_file.storage
        old_file_name = old_file.name

        transaction.on_commit(lambda: _safe_delete_file(storage, old_file_name))
