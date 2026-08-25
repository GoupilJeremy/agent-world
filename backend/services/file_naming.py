"""Generate portable filenames for agent outputs.

The naming algorithm deliberately uses only ASCII letters, digits, and
underscores.  Generated names therefore behave consistently on Windows,
macOS, and Linux and cannot introduce path separators into an output path.
"""

from __future__ import annotations

import re
import unicodedata
from datetime import date, datetime, timezone

SUPPORTED_OUTPUT_EXTENSIONS = frozenset({"json", "md", "txt"})

_MAX_COMPONENT_LENGTH = 64
_MAX_CUSTOM_COMPONENT_LENGTH = 32
_MAX_STEM_LENGTH = 120
_NON_ALPHANUMERIC = re.compile(r"[^a-z0-9]+")
_WINDOWS_RESERVED_NAMES = frozenset(
    {"con", "prn", "aux", "nul"}
    | {f"com{number}" for number in range(1, 10)}
    | {f"lpt{number}" for number in range(1, 10)}
)


def generate_filename(
    content: str,
    extension: str = "json",
    prefix: str | None = None,
    suffix: str | None = None,
    now: datetime | date | None = None,
) -> str:
    """Return a content-based, dated filename.

    Args:
        content: Text used to derive the meaningful part of the filename.
        extension: One of ``json``, ``md``, or ``txt``. A leading dot is
            accepted for convenience.
        prefix: Optional portable component placed before the content slug.
        suffix: Optional portable component placed after the content slug.
        now: Date used in the filename. It is injectable for deterministic
            tests and defaults to the current UTC date.

    The result follows ``[prefix_]content[_suffix]_YYYYMMDD.extension``.
    Empty or non-transliterable content falls back to ``agent_output``.
    """

    if not isinstance(content, str):
        raise TypeError("Filename content must be a string")

    normalized_extension = normalize_extension(extension)
    timestamp = _normalize_date(now)
    content_slug = slugify_component(
        content,
        fallback="agent_output",
        max_length=_MAX_COMPONENT_LENGTH,
    )

    components = []
    prefix_slug = _optional_component(prefix, "prefix")
    suffix_slug = _optional_component(suffix, "suffix")
    if prefix_slug:
        components.append(prefix_slug)
    components.append(content_slug)
    if suffix_slug:
        components.append(suffix_slug)

    semantic_stem = "_".join(components)[:_MAX_STEM_LENGTH].rstrip("_")
    if not semantic_stem:
        semantic_stem = "agent_output"
    return f"{semantic_stem}_{timestamp:%Y%m%d}.{normalized_extension}"


def normalize_extension(extension: str) -> str:
    """Normalize and validate a generated-file extension."""

    if not isinstance(extension, str):
        raise TypeError("Output extension must be a string")
    normalized = extension.strip().lower().removeprefix(".")
    if normalized not in SUPPORTED_OUTPUT_EXTENSIONS:
        supported = ", ".join(sorted(SUPPORTED_OUTPUT_EXTENSIONS))
        raise ValueError(f"Unsupported output extension '{extension}'; use {supported}")
    return normalized


def slugify_component(
    value: str,
    *,
    fallback: str = "output",
    max_length: int = _MAX_COMPONENT_LENGTH,
) -> str:
    """Convert untrusted text into one portable filename component."""

    if not isinstance(value, str):
        raise TypeError("Filename components must be strings")
    if not isinstance(fallback, str):
        raise TypeError("Filename component fallback must be a string")
    if max_length < 1:
        raise ValueError("Filename component length must be positive")

    slug = _slug_text(value, max_length)
    if not slug:
        slug = _slug_text(fallback, max_length)
    if not slug:
        slug = "output"[:max_length]
    if slug.lower() in _WINDOWS_RESERVED_NAMES:
        slug = f"_{slug}"[:max_length].rstrip("_")
    return slug or "x"[:max_length]


def _slug_text(value: str, max_length: int) -> str:
    """Normalize one slug candidate without trusting fallback text."""

    decomposed = unicodedata.normalize("NFKD", value)
    ascii_value = decomposed.encode("ascii", "ignore").decode("ascii").lower()
    return _NON_ALPHANUMERIC.sub("_", ascii_value).strip("_")[:max_length].rstrip("_")


def _optional_component(value: str | None, label: str) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str):
        raise TypeError(f"Filename {label} must be a string")
    if not value.strip():
        return None
    return slugify_component(
        value,
        fallback=label,
        max_length=_MAX_CUSTOM_COMPONENT_LENGTH,
    )


def _normalize_date(value: datetime | date | None) -> date:
    if value is None:
        return datetime.now(timezone.utc).date()
    if isinstance(value, datetime):
        # A naive datetime is treated as an already-local calendar value. An
        # aware datetime is normalized to UTC so two callers describing the
        # same instant cannot generate different dates.
        if value.tzinfo is None:
            return value.date()
        return value.astimezone(timezone.utc).date()
    if isinstance(value, date):
        return value
    raise TypeError("now must be a date or datetime")
