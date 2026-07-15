"""Custom model and form validators for file uploads.

Provides reusable validation logic to ensure that uploaded images
meet system requirements for maximum size and allowed formats.
"""

import os

from django.core.exceptions import ValidationError


def validate_image_size(image):
    """Validate that an uploaded image does not exceed the maximum allowed size.

    Raises:
        ValidationError: If the file size is greater than 5MB.
    """
    max_size_mb = 5
    if image.size > max_size_mb * 1024 * 1024:
        raise ValidationError(f"Image size cannot exceed {max_size_mb}MB.")


def validate_image_extension(image):
    """Validate that an uploaded image has an allowed file extension.

    Checks the file extension against a predefined list of acceptable
    formats (.jpg, .jpeg, .png, .webp), ignoring case.

    Raises:
        ValidationError: If the file extension is not supported.
    """
    ext = os.path.splitext(image.name)[1]
    valid_extensions = [".jpg", ".jpeg", ".png", ".webp"]
    if not ext.lower() in valid_extensions:
        allowed_formats = ", ".join(valid_extensions)
        raise ValidationError(
            f"Unsupported file format. Allowed are: {allowed_formats}."
        )
