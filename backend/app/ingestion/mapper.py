"""Article mapping and content processing functionality."""

import hashlib
import re
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse

import bleach
from dateutil import parser as date_parser

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


def sanitize_html(content: str) -> str:
    """
    Sanitize HTML content by removing ALL tags and JavaScript.

    This implements a strict security policy - no HTML tags are allowed.
    All content is converted to plain text.

    Args:
        content: HTML content to sanitize

    Returns:
        Plain text with all HTML removed
    """
    if not content:
        return ""

    # First pass: Use bleach with empty allowlist to remove ALL HTML tags
    # strip=True removes tags and keeps text content
    cleaned = bleach.clean(content, tags=[], strip=True)

    # Second pass: Remove any script content and suspicious patterns
    # Remove anything that looks like JavaScript
    cleaned = re.sub(r'<script[^>]*>.*?</script>', '', cleaned, flags=re.IGNORECASE | re.DOTALL)
    cleaned = re.sub(r'javascript:', '', cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r'alert\s*\(', '', cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r'eval\s*\(', '', cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r'document\.|window\.|location\.', '', cleaned, flags=re.IGNORECASE)

    # Remove any remaining HTML entities
    cleaned = re.sub(r'&[a-zA-Z0-9#]+;', '', cleaned)

    # Remove event handlers that might have been preserved
    cleaned = re.sub(r'on\w+\s*=', '', cleaned, flags=re.IGNORECASE)

    # Remove any remaining angle brackets (shouldn't be any, but extra safety)
    cleaned = re.sub(r'<[^>]*>', '', cleaned)

    # Trim to configured max length
    if len(cleaned) > settings.summary_max_len:
        cleaned = cleaned[:settings.summary_max_len]

    return cleaned.strip()


def canonicalize_url(url: str) -> str:
    """
    Canonicalize URL by removing tracking parameters and normalizing format.

    Args:
        url: URL to canonicalize

    Returns:
        Canonicalized URL
    """
    if not url:
        return ""

    try:
        parsed = urlparse(url)

        # Remove common tracking parameters
        tracking_params = {
            'utm_source', 'utm_medium', 'utm_campaign', 'utm_term', 'utm_content',
            'fbclid', 'gclid', 'msclkid', 'ref', 'source', 'medium'
        }

        # Filter out tracking parameters
        query_params = parse_qs(parsed.query)
        filtered_params = {
            k: v for k, v in query_params.items()
            if k.lower() not in tracking_params
        }

        # Rebuild query string
        new_query = urlencode(filtered_params, doseq=True) if filtered_params else ""

        # Rebuild URL
        canonicalized = urlunparse((
            parsed.scheme.lower(),
            parsed.netloc.lower(),
            parsed.path,
            parsed.params,
            new_query,
            ""  # Remove fragment
        ))

        return canonicalized

    except Exception as e:
        logger.warning("Failed to canonicalize URL", extra={"url": url, "error": str(e)})
        return url


def parse_published_date(date_str: Optional[str]) -> datetime:
    """
    Parse published date with fallback handling.

    Args:
        date_str: Date string to parse

    Returns:
        Timezone-aware datetime in UTC
    """
    if not date_str or not date_str.strip():
        # Use current date at midnight UTC as fallback
        return datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)

    try:
        # Parse with dateutil which handles many formats
        parsed_date = date_parser.parse(date_str)

        # Ensure timezone awareness
        if parsed_date.tzinfo is None:
            # Assume UTC if no timezone info
            parsed_date = parsed_date.replace(tzinfo=timezone.utc)
        else:
            # Convert to UTC
            parsed_date = parsed_date.astimezone(timezone.utc)

        return parsed_date

    except (ValueError, TypeError) as e:
        logger.warning(
            "Failed to parse published date, using fallback",
            extra={"date_str": date_str, "error": str(e)}
        )
        # Fallback to current date at midnight UTC
        return datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)


def generate_content_hash(title: str, link: str, published_at: str) -> str:
    """
    Generate stable content hash for deduplication.

    Follows the specification:
    sha256(lowercase(strip(title)) + "|" + canonical_link + "|" + (iso8601(published_at_utc) OR "fallback:" + first_8_chars_of_sha256(link)))

    Args:
        title: Article title
        link: Article link
        published_at: Published date (ISO format or fallback indicator)

    Returns:
        SHA256 hash as hex string
    """
    # Normalize title: lowercase and strip whitespace
    normalized_title = title.strip().lower() if title else ""

    # Canonicalize link
    canonical_link = canonicalize_url(link)

    # Handle published_at - could be ISO datetime or fallback indicator
    if published_at and not published_at.startswith("fallback:"):
        # Use the provided timestamp
        timestamp_part = published_at
    else:
        # Generate fallback hash from link
        link_hash = hashlib.sha256(canonical_link.encode('utf-8')).hexdigest()[:8]
        timestamp_part = f"fallback:{link_hash}"

    # Combine parts
    hash_input = f"{normalized_title}|{canonical_link}|{timestamp_part}"

    # Generate SHA256 hash
    content_hash = hashlib.sha256(hash_input.encode('utf-8')).hexdigest()

    logger.debug(
        "Generated content hash",
        extra={
            "title": normalized_title[:50] + "..." if len(normalized_title) > 50 else normalized_title,
            "link": canonical_link,
            "timestamp_part": timestamp_part,
            "hash": content_hash[:16] + "..."
        }
    )

    return content_hash


class ArticleMapper:
    """Maps RSS feed entries to Article model data."""

    def map_entry_to_article(self, entry: Any, source_id: int) -> Dict[str, Any]:
        """
        Map feedparser entry to Article model fields.

        Args:
            entry: feedparser entry object
            source_id: ID of the source this article belongs to

        Returns:
            Dictionary with Article model fields
        """
        # Extract and sanitize title
        title = sanitize_html(getattr(entry, 'title', ''))
        if not title:
            title = "Untitled Article"

        # Extract and validate link
        link = getattr(entry, 'link', '')
        if not link:
            # Fallback to first alternate link if available
            links = getattr(entry, 'links', [])
            for link_obj in links:
                if getattr(link_obj, 'rel', '') == 'alternate':
                    link = getattr(link_obj, 'href', '')
                    break
            if not link:
                raise ValueError("Article missing required link/URL")

        # Extract and sanitize summary/description
        summary_raw = None
        summary_text = getattr(entry, 'summary', None) or getattr(entry, 'description', None)
        if summary_text:
            summary_raw = sanitize_html(summary_text)

        # Parse published date
        published_str = getattr(entry, 'published', None) or getattr(entry, 'updated', None)
        published_at = parse_published_date(published_str)

        # Determine timestamp for hash
        if published_str:
            # Use the parsed datetime in ISO format
            timestamp_for_hash = published_at.isoformat()
        else:
            # Use fallback indicator (will be processed in generate_content_hash)
            timestamp_for_hash = "fallback"

        # Generate content hash
        content_hash = generate_content_hash(title, link, timestamp_for_hash)

        # Extract optional fields
        author = sanitize_html(getattr(entry, 'author', '') or '')
        if not author:
            author = None

        # Extract tags
        tags = []
        entry_tags = getattr(entry, 'tags', [])
        for tag in entry_tags:
            tag_term = getattr(tag, 'term', '')
            if tag_term:
                # Sanitize tag term and add to list
                clean_tag = sanitize_html(tag_term)
                if clean_tag:
                    tags.append(clean_tag)

        article_data = {
            'source_id': source_id,
            'title': title,
            'link': canonicalize_url(link),
            'summary_raw': summary_raw,
            'content_hash': content_hash,
            'published_at': published_at,
            'author': author,
            'tags': tags
        }

        logger.debug(
            "Mapped article",
            extra={
                "title": title[:50] + "..." if len(title) > 50 else title,
                "link": article_data['link'],
                "published_at": published_at.isoformat(),
                "content_hash": content_hash[:16] + "..."
            }
        )

        return article_data


def validate_article_data(article_data: Dict[str, Any]) -> None:
    """
    Validate article data before database insertion.

    Args:
        article_data: Dictionary containing article data

    Raises:
        ValueError: If required fields are missing or invalid
    """
    required_fields = ['source_id', 'title', 'link', 'content_hash', 'published_at']

    for field in required_fields:
        if field not in article_data:
            raise ValueError(f"Missing required field: {field}")

    # Validate field types and constraints
    if not isinstance(article_data['source_id'], int) or article_data['source_id'] <= 0:
        raise ValueError("source_id must be a positive integer")

    if not isinstance(article_data['title'], str) or not article_data['title'].strip():
        raise ValueError("title must be a non-empty string")

    if not isinstance(article_data['link'], str) or not article_data['link'].strip():
        raise ValueError("link must be a non-empty string")

    if not isinstance(article_data['content_hash'], str) or len(article_data['content_hash']) != 64:
        raise ValueError("content_hash must be a 64-character SHA256 hex string")

    if not isinstance(article_data['published_at'], datetime):
        raise ValueError("published_at must be a datetime object")

    # Validate optional fields
    if 'summary_raw' in article_data and article_data['summary_raw'] is not None:
        if not isinstance(article_data['summary_raw'], str):
            raise ValueError("summary_raw must be a string or None")

    if 'author' in article_data and article_data['author'] is not None:
        if not isinstance(article_data['author'], str):
            raise ValueError("author must be a string or None")

    if 'tags' in article_data:
        if not isinstance(article_data['tags'], list):
            raise ValueError("tags must be a list")
        for tag in article_data['tags']:
            if not isinstance(tag, str):
                raise ValueError("all tags must be strings")