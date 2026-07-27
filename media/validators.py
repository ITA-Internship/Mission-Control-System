"""Content-based validation for uploaded files.

Both the file extension and the client-supplied ``Content-Type`` header are
forgeable: a caller can rename arbitrary bytes to ``x.png`` or send an arbitrary
``content_type``. Trusting either permits executables, HTML/SVG (stored XSS), or
other hostile payloads to pass the allow-list. To prevent this, the module
derives the real MIME type from the file's leading bytes with libmagic and
requires it to match the claimed extension.
"""

import os

import magic
from django.core.exceptions import ValidationError

# Leading bytes libmagic needs to identify a file. 2 KiB covers every format we
# accept while keeping us from pulling large uploads into memory to sniff them.
_SNIFF_BYTES = 2048

# Real MIME types accepted per (lower-case, dotted) extension. Binary formats
# are pinned to their exact signature; text formats (CSV, JSON) are reported as
# ``text/plain`` by many libmagic builds, so those extensions also accept the
# generic text type. The map is intentionally broader than any single upload
# allow-list so it can back both artifact and video validation.
EXTENSION_CONTENT_TYPES = {
    ".jpg": {"image/jpeg"},
    ".jpeg": {"image/jpeg"},
    ".png": {"image/png"},
    ".csv": {"text/csv", "application/csv", "text/plain"},
    ".json": {"application/json", "text/json", "text/plain"},
    ".mp4": {"video/mp4", "application/mp4"},
    ".avi": {"video/x-msvideo", "video/avi", "video/vnd.avi"},
    ".mov": {"video/quicktime"},
    ".mkv": {"video/x-matroska", "application/x-matroska"},
}


def detect_content_type(file):
    """Return the MIME type libmagic infers from ``file``'s leading bytes.

    Restores the file's read position before returning so the caller can still
    persist the upload afterwards.
    """
    pos = file.tell() if hasattr(file, "tell") else 0
    try:
        file.seek(0)
        head = file.read(_SNIFF_BYTES)
    finally:
        file.seek(pos)

    if isinstance(head, str):
        head = head.encode("utf-8", "replace")
    return magic.from_buffer(head, mime=True)


def validate_file_content(file, allowed_extensions):
    """Validate ``file``'s real content against its claimed extension.

    ``allowed_extensions`` is an iterable of dotted, lower-case extensions
    acceptable in the calling context (the artifact or video allow-list).
    Returns ``(extension, detected_mime)`` on success and raises
    ``django.core.exceptions.ValidationError`` otherwise. The client-supplied
    ``Content-Type`` is never consulted.
    """
    allowed = {ext.lower() for ext in allowed_extensions}
    ext = os.path.splitext(file.name or "")[1].lower()

    if ext not in allowed:
        shown = ext or "(none)"
        raise ValidationError(
            f"Unsupported file extension '{shown}'. "
            f"Allowed: {', '.join(sorted(allowed))}."
        )

    expected = EXTENSION_CONTENT_TYPES.get(ext)
    if expected is None:
        # An extension is allow-listed but has no known signature to check it
        # against — fail closed rather than trust the extension alone.
        raise ValidationError(f"No content-type signature is configured for '{ext}'.")

    detected = detect_content_type(file)
    if detected not in expected:
        raise ValidationError(
            f"File content ('{detected}') does not match the '{ext}' extension."
        )

    return ext, detected
