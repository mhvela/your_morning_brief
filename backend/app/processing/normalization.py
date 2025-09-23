"""Content normalization functionality."""

import re
from datetime import UTC, datetime
from typing import Any
from urllib.parse import parse_qs, urlencode, urlparse, urlunparse

import bleach
from dateutil import parser as date_parser

from app.core.config import settings
from app.core.logging import get_logger
from app.processing.encoding import normalize_unicode

logger = get_logger(__name__)


def normalize_title(title: str | None) -> str:
    """
    Normalize article title with deterministic rules.

    Args:
        title: Raw title text

    Returns:
        Normalized title for display
    """
    if not title:
        return "Untitled Article"

    # Apply Unicode normalization first
    normalized = normalize_unicode(title)

    # Strip ALL HTML tags first
    cleaned = bleach.clean(normalized, tags=[], strip=True)

    # Decode HTML entities after tag removal
    import html

    cleaned = html.unescape(cleaned)

    # Remove any angle brackets that might remain from entity decoding
    cleaned = re.sub(r"<[^>]*>", "", cleaned)

    # Collapse whitespace
    cleaned = re.sub(r"\s+", " ", cleaned).strip()

    # Remove SQL injection patterns (defense in depth)
    sql_patterns = [
        r"DELETE\s+FROM",
        r"INSERT\s+INTO",
        r"UPDATE\s+SET",
        r"DROP\s+TABLE",
        r";\s*--",
        r"--\s*$",
    ]
    for pattern in sql_patterns:
        cleaned = re.sub(pattern, "", cleaned, flags=re.IGNORECASE)

    return cleaned if cleaned else "Untitled Article"


def normalize_title_for_hash(title: str | None) -> str:
    """
    Normalize title for hash computation (lowercase).

    Args:
        title: Raw title text

    Returns:
        Lowercase normalized title for hashing
    """
    normalized = normalize_title(title)
    return normalized.lower()


def canonicalize_url(url: str | None) -> str:
    """
    Canonicalize URL with deterministic normalization.

    Args:
        url: Raw URL

    Returns:
        Canonicalized URL
    """
    if not url or not url.strip():
        return ""

    try:
        parsed = urlparse(url.strip())

        # Lowercase scheme and host
        scheme = parsed.scheme.lower() if parsed.scheme else "https"
        netloc = parsed.netloc.lower() if parsed.netloc else ""

        # Remove default ports
        if netloc.endswith(":80") and scheme == "http":
            netloc = netloc[:-3]
        elif netloc.endswith(":443") and scheme == "https":
            netloc = netloc[:-4]

        # Process query parameters
        query_params = parse_qs(parsed.query) if parsed.query else {}

        # Remove tracking parameters
        filtered_params = {
            k: v
            for k, v in query_params.items()
            if k.lower()
            not in [param.lower() for param in settings.link_tracking_params]
        }

        # Sort parameters for stability
        new_query = ""
        if filtered_params:
            # Sort by key and ensure consistent ordering
            sorted_params = sorted(filtered_params.items())
            new_query = urlencode(sorted_params, doseq=True)

        # Remove trailing slash unless it's the root path
        path = parsed.path
        if path.endswith("/") and len(path) > 1:
            path = path[:-1]

        # Rebuild URL without fragment
        canonicalized = urlunparse(
            (scheme, netloc, path, parsed.params, new_query, "")  # Remove fragment
        )

        return canonicalized

    except Exception as e:
        logger.warning(
            "URL canonicalization failed", extra={"url": url, "error": str(e)}
        )
        return url


def normalize_summary(summary: str | None) -> str | None:
    """
    Normalize article summary with comprehensive sanitization.

    Args:
        summary: Raw summary HTML/text

    Returns:
        Normalized plain text summary or None
    """
    if not summary or not summary.strip():
        return None

    # Apply Unicode normalization first
    normalized = normalize_unicode(summary)

    # Strip ALL HTML tags using bleach with empty allowlist
    cleaned = bleach.clean(normalized, tags=[], strip=True)

    # Remove JavaScript patterns (defense in depth)
    js_patterns = [
        r"<script[^>]*>.*?</script>",
        r"javascript:",
        r"alert\s*\(",
        r"eval\s*\(",
        r"document\.",
        r"window\.",
        r"location\.",
        r"on\w+\s*=",
    ]
    for pattern in js_patterns:
        cleaned = re.sub(pattern, "", cleaned, flags=re.IGNORECASE | re.DOTALL)

    # Remove SQL injection patterns
    sql_patterns = [
        r"DELETE\s+FROM",
        r"INSERT\s+INTO",
        r"UPDATE\s+SET",
        r"DROP\s+TABLE",
        r";\s*--",
    ]
    for pattern in sql_patterns:
        cleaned = re.sub(pattern, "", cleaned, flags=re.IGNORECASE)

    # Decode HTML entities
    import html

    cleaned = html.unescape(cleaned)

    # Collapse whitespace
    cleaned = re.sub(r"\s+", " ", cleaned).strip()

    # Apply length limit
    if len(cleaned) > settings.summary_max_len:
        cleaned = cleaned[: settings.summary_max_len]

    # Log suspicious patterns for security monitoring
    suspicious_patterns = ["script", "javascript", "eval", "alert"]
    if any(pattern.lower() in cleaned.lower() for pattern in suspicious_patterns):
        logger.warning(
            "Suspicious content detected in summary",
            extra={"summary_preview": cleaned[:200]},
        )

    return cleaned if cleaned else None


def normalize_author(author: str | None) -> str | None:
    """
    Normalize author field.

    Args:
        author: Raw author text

    Returns:
        Normalized author or None
    """
    if not author or not author.strip():
        return None

    # Apply Unicode normalization
    normalized = normalize_unicode(author)

    # Strip HTML tags
    cleaned = bleach.clean(normalized, tags=[], strip=True)

    # Decode HTML entities
    import html

    cleaned = html.unescape(cleaned)

    # Trim whitespace
    cleaned = cleaned.strip()

    return cleaned if cleaned else None


def normalize_tags(tags: list[str] | None) -> list[str]:
    """
    Normalize tags with deduplication and sorting.

    Args:
        tags: List of raw tag strings

    Returns:
        Normalized, deduplicated, and sorted tags
    """
    if not tags:
        return []

    normalized_tags = []
    seen_lower = set()

    for tag in tags:
        if not tag or not isinstance(tag, str):
            continue

        # Apply Unicode normalization
        normalized = normalize_unicode(tag)

        # Strip HTML tags
        cleaned = bleach.clean(normalized, tags=[], strip=True)

        # Decode HTML entities
        import html

        cleaned = html.unescape(cleaned)

        # Trim whitespace
        cleaned = cleaned.strip()

        if cleaned and cleaned.lower() not in seen_lower:
            normalized_tags.append(cleaned)
            seen_lower.add(cleaned.lower())

    # Sort for stable ordering
    return sorted(normalized_tags)


def normalize_published_date(date_str: str | None) -> datetime:
    """
    Normalize published date to timezone-aware UTC datetime.

    Args:
        date_str: Raw date string

    Returns:
        Timezone-aware datetime in UTC
    """
    if not date_str or not date_str.strip():
        # Use current date at midnight UTC as fallback
        fallback = datetime.now(UTC).replace(hour=0, minute=0, second=0, microsecond=0)
        logger.debug("Using fallback date for missing published_at")
        return fallback

    try:
        # Parse with dateutil which handles many formats
        parsed_date = date_parser.parse(date_str.strip())

        # Ensure timezone awareness
        if parsed_date.tzinfo is None:
            # Assume UTC if no timezone info
            parsed_date = parsed_date.replace(tzinfo=UTC)
        else:
            # Convert to UTC
            parsed_date = parsed_date.astimezone(UTC)

        return parsed_date

    except (ValueError, TypeError) as e:
        logger.warning(
            "Failed to parse published date, using fallback",
            extra={"date_str": date_str, "error": str(e)},
        )
        # Fallback to current date at midnight UTC
        return datetime.now(UTC).replace(hour=0, minute=0, second=0, microsecond=0)


def normalize_entry(entry: Any) -> dict[str, Any]:
    """
    Normalize a complete RSS entry with all fields.

    Args:
        entry: RSS feed entry object

    Returns:
        Dictionary with normalized fields
    """
    # Extract and normalize basic fields
    title = getattr(entry, "title", "")
    link = getattr(entry, "link", "")
    summary = getattr(entry, "summary", None) or getattr(entry, "description", None)
    author = getattr(entry, "author", None)

    # Extract tags
    raw_tags = []
    entry_tags = getattr(entry, "tags", [])
    for tag in entry_tags:
        tag_term = getattr(tag, "term", "")
        if tag_term:
            raw_tags.append(tag_term)

    # Extract published date
    published_str = getattr(entry, "published", None) or getattr(entry, "updated", None)

    # Normalize all fields
    normalized = {
        "title": normalize_title(title),
        "title_for_hash": normalize_title_for_hash(title),
        "link": canonicalize_url(link),
        "summary": normalize_summary(summary),
        "author": normalize_author(author),
        "tags": normalize_tags(raw_tags),
        "published_at": normalize_published_date(published_str),
    }

    logger.debug(
        "Normalized entry",
        extra={
            "original_title": title[:50] + "..." if len(title) > 50 else title,
            "normalized_title": (
                str(normalized["title"])[:50] + "..."
                if len(str(normalized["title"])) > 50
                else str(normalized["title"])
            ),
            "original_link": link,
            "canonical_link": normalized["link"],
        },
    )

    return normalized
