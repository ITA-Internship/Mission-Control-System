import os

from django.core.exceptions import ValidationError


def validate_image_size(image):
    max_size_mb = 5
    if image.size > max_size_mb * 1024 * 1024:
        raise ValidationError(f"Image size cannot exceed {max_size_mb}MB.")


def validate_image_extension(image):
    ext = os.path.splitext(image.name)[1]
    valid_extensions = [".jpg", ".jpeg", ".png", ".webp"]
    if not ext.lower() in valid_extensions:
        allowed_formats = ", ".join(valid_extensions)
        raise ValidationError(
            f"Unsupported file format. Allowed are: {allowed_formats}."
        )
