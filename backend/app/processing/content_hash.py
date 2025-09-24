"""Stable content hash generation for deduplication."""

import hashlib
from datetime import datetime
from typing import Any

from app.core.config import settings
from app.core.logging import get_logger
from app.processing.normalization import (
    canonicalize_url,
    normalize_summary,
    normalize_title_for_hash,
)

logger = get_logger(__name__)


def compute_content_hash(
    title: str | None,
    link: str | None,
    published_at: datetime | None,
    summary: str | None = None,
) -> str:
    """
    Generate stable content hash for deduplication.

    Implements the M1.5 specification:
    sha256(
      lowercase(trimmed_title) + "|" +
      canonical_link + "|" +
      iso8601(published_at_utc) + "|" +
      first_100_chars_of(cleaned_summary)
    )

    Args:
        title: Article title
        link: Article URL
        published_at: Published datetime (UTC)
        summary: Article summary (optional)

    Returns:
        SHA256 hash as hex string
    """
    # Normalize title for hashing (lowercase, cleaned)
    normalized_title = normalize_title_for_hash(title)

    # Canonicalize link
    canonical_link = canonicalize_url(link) if link else ""

    # Handle published timestamp
    if published_at:
        try:
            # Ensure UTC and format as ISO8601
            if published_at.tzinfo is None:
                from datetime import UTC

                published_at = published_at.replace(tzinfo=UTC)
            else:
                published_at = published_at.astimezone(
                    UTC if hasattr(datetime, "UTC") else None
                )

            timestamp_part = published_at.isoformat()
        except Exception as e:
            logger.warning(
                "Failed to format published_at for hash, using fallback",
                extra={"published_at": str(published_at), "error": str(e)},
            )
            # Generate fallback hash from link
            link_hash = hashlib.sha256(canonical_link.encode("utf-8")).hexdigest()[:8]
            timestamp_part = f"fallback:{link_hash}"
    else:
        # Generate fallback hash from link
        link_hash = hashlib.sha256(canonical_link.encode("utf-8")).hexdigest()[:8]
        timestamp_part = f"fallback:{link_hash}"

    # Handle summary (first N characters of cleaned summary)
    summary_part = ""
    if summary:
        normalized_summary = normalize_summary(summary)
        if normalized_summary:
            summary_part = normalized_summary[: settings.hash_summary_prefix_len]

    # Combine all parts
    hash_input = f"{normalized_title}|{canonical_link}|{timestamp_part}|{summary_part}"

    # Generate SHA256 hash
    content_hash = hashlib.sha256(hash_input.encode("utf-8")).hexdigest()

    logger.debug(
        "Generated content hash",
        extra={
            "title_preview": (
                normalized_title[:30] + "..."
                if len(normalized_title) > 30
                else normalized_title
            ),
            "link": canonical_link,
            "timestamp_part": timestamp_part,
            "summary_preview": (
                summary_part[:30] + "..." if len(summary_part) > 30 else summary_part
            ),
            "hash_preview": content_hash[:16] + "...",
        },
    )

    return content_hash


def compute_content_hash_from_normalized(normalized_data: dict[str, Any]) -> str:
    """
    Generate content hash from already normalized data.

    Args:
        normalized_data: Dictionary with normalized entry fields

    Returns:
        SHA256 hash as hex string
    """
    return compute_content_hash(
        title=normalized_data.get("title_for_hash"),
        link=normalized_data.get("link"),
        published_at=normalized_data.get("published_at"),
        summary=normalized_data.get("summary"),
    )
