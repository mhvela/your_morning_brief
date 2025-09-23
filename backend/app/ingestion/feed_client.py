"""Feed client with security controls for RSS ingestion."""

import ipaddress
import random
import time
from typing import Any
from urllib.parse import urlparse

import feedparser
import httpx

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class FeedClient:
    """HTTP client for fetching RSS feeds with security controls."""

    def __init__(self):
        """Initialize feed client with security settings."""
        self.user_agent = settings.ingestion_user_agent
        self.timeout = settings.ingestion_timeout_sec
        self.max_retries = settings.ingestion_max_retries
        self.max_response_size = (
            settings.max_response_size_mb * 1024 * 1024
        )  # Convert MB to bytes

    def validate_url(self, url: str) -> None:
        """
        Validate URL for security compliance.

        Args:
            url: URL to validate

        Raises:
            ValueError: If URL fails security validation
        """
        if not url or not isinstance(url, str):
            raise ValueError("URL must be a non-empty string")

        try:
            parsed = urlparse(url)
        except Exception as e:
            raise ValueError(f"Invalid URL format: {e}") from e

        # Check URL scheme
        if parsed.scheme.lower() not in settings.allowed_url_schemes:
            raise ValueError(
                f"Invalid URL scheme '{parsed.scheme}'. "
                f"Allowed schemes: {', '.join(settings.allowed_url_schemes)}"
            )

        # Check for hostname
        if not parsed.hostname:
            raise ValueError("URL must include a hostname")

        # SSRF Protection: Check for private/internal IP addresses
        try:
            # Try to parse hostname as IP address
            ip_address = ipaddress.ip_address(parsed.hostname)
            self._check_ip_address(ip_address)
        except ValueError as e:
            # Check if this is our SSRF protection error
            if "SSRF protection" in str(e):
                raise  # Re-raise our SSRF protection error

            # Not a direct IP address, check if it's a blocked hostname
            if parsed.hostname.lower() in ["localhost", "127.0.0.1", "::1"]:
                raise ValueError("SSRF protection: localhost access blocked") from None
            # For domain names, we would need deeper inspection at request time
            # For now, we allow domain names to proceed (real implementation would
            # need to check resolved IPs at connection time)

    def _check_ip_address(
        self, ip: ipaddress.IPv4Address | ipaddress.IPv6Address
    ) -> None:
        """
        Check if IP address is in blocked networks.

        Args:
            ip: IP address to check

        Raises:
            ValueError: If IP is in blocked network range
        """
        for network_str in settings.blocked_networks:
            try:
                network = ipaddress.ip_network(network_str, strict=False)
                if ip in network:
                    raise ValueError(
                        f"SSRF protection: IP {ip} is in blocked network {network}"
                    )
            except ValueError as e:
                if "SSRF protection" in str(e):
                    raise
                # Invalid network config - log warning but continue
                logger.warning(f"Invalid network configuration: {network_str}")

    def _make_http_request(self, url: str) -> Any:
        """Make HTTP request and parse feed content."""
        with httpx.Client(
            timeout=self.timeout,
            verify=True,  # Always verify SSL certificates
            follow_redirects=True,
            max_redirects=3,  # Limit redirects
        ) as client:
            response = client.get(
                url,
                headers={
                    "User-Agent": self.user_agent,
                    "Accept": ("application/rss+xml, application/xml, text/xml, */*"),
                },
            )

            # Check response size
            self._validate_response_size(response)

            # Raise for HTTP errors
            response.raise_for_status()

            # Parse feed content
            feed = feedparser.parse(response.content)

            # Check for parsing errors
            if hasattr(feed, "bozo") and feed.bozo and hasattr(feed, "bozo_exception"):
                logger.warning(
                    "Feed parsing warning",
                    extra={"url": url, "warning": str(feed.bozo_exception)},
                )

            return feed

    def _validate_response_size(self, response: httpx.Response) -> None:
        """Validate response size against limits."""
        content_length = response.headers.get("content-length")
        if content_length and int(content_length) > self.max_response_size:
            raise ValueError(
                f"Response too large: {content_length} bytes "
                f"(max: {self.max_response_size} bytes)"
            )

        # Check actual content size
        if len(response.content) > self.max_response_size:
            raise ValueError(
                f"Response too large: {len(response.content)} bytes "
                f"(max: {self.max_response_size} bytes)"
            )

    def _handle_retry_logic(
        self, attempt: int, url: str, total_wait_time: float
    ) -> float:
        """Handle retry delay logic and return new total wait time."""
        if attempt >= self.max_retries:
            return total_wait_time

        delay = calculate_backoff_delay(
            attempt,
            settings.retry_backoff_base_sec,
            settings.retry_backoff_jitter_sec,
            settings.ingestion_total_retry_cap_sec - total_wait_time,
        )

        new_total_wait_time = total_wait_time + delay
        if new_total_wait_time >= settings.ingestion_total_retry_cap_sec:
            logger.warning(
                "Retry time limit exceeded",
                extra={"url": url, "total_wait_time": new_total_wait_time},
            )
            return settings.ingestion_total_retry_cap_sec

        logger.debug(f"Retrying in {delay:.2f}s", extra={"url": url, "delay": delay})
        time.sleep(delay)
        return new_total_wait_time

    def fetch_feed(self, url: str) -> Any:
        """
        Fetch and parse RSS feed with security controls and retry logic.

        Args:
            url: Feed URL to fetch

        Returns:
            Parsed feedparser result

        Raises:
            ValueError: If URL fails security validation
            TimeoutError: If request times out
            Exception: If request fails after retries
        """
        # Validate URL first
        self.validate_url(url)

        # Attempt fetch with retries
        last_exception = None
        total_wait_time = 0

        for attempt in range(self.max_retries + 1):  # +1 for initial attempt
            try:
                logger.debug(
                    "Fetching feed",
                    extra={
                        "url": url,
                        "attempt": attempt + 1,
                        "max_retries": self.max_retries + 1,
                    },
                )

                feed = self._make_http_request(url)

                logger.info(
                    "Successfully fetched feed",
                    extra={
                        "url": url,
                        "entries_count": (
                            len(feed.entries) if hasattr(feed, "entries") else 0
                        ),
                        "attempt": attempt + 1,
                    },
                )

                return feed

            except httpx.TimeoutException:
                last_exception = TimeoutError(
                    f"Request timed out after {self.timeout}s"
                )
                logger.warning(
                    "Feed fetch timeout",
                    extra={"url": url, "attempt": attempt + 1, "timeout": self.timeout},
                )

            except httpx.HTTPStatusError as e:
                last_exception = Exception(
                    f"HTTP error {e.response.status_code}: {e.response.text}"
                )
                logger.warning(
                    "Feed fetch HTTP error",
                    extra={
                        "url": url,
                        "attempt": attempt + 1,
                        "status_code": e.response.status_code,
                    },
                )

            except Exception as e:
                last_exception = e
                logger.warning(
                    "Feed fetch error",
                    extra={"url": url, "attempt": attempt + 1, "error": str(e)},
                )

            # Handle retry logic
            total_wait_time = self._handle_retry_logic(attempt, url, total_wait_time)
            if total_wait_time >= settings.ingestion_total_retry_cap_sec:
                break

        # All retries failed
        logger.error(
            "Feed fetch failed after all retries",
            extra={
                "url": url,
                "attempts": self.max_retries + 1,
                "last_error": str(last_exception),
            },
        )

        if last_exception:
            raise last_exception
        else:
            raise Exception("Failed to fetch feed after all retries")


def calculate_backoff_delay(
    attempt: int, base_delay: float, jitter: float, max_remaining_time: float
) -> float:
    """
    Calculate exponential backoff delay with jitter.

    Args:
        attempt: Current attempt number (0-based)
        base_delay: Base delay in seconds
        jitter: Maximum jitter to add in seconds
        max_remaining_time: Maximum remaining time before hitting total cap

    Returns:
        Delay in seconds
    """
    # Exponential backoff: base * (2^attempt)
    exponential_delay = base_delay * (2**attempt)

    # Add random jitter
    jitter_amount = random.uniform(0, jitter)
    total_delay = exponential_delay + jitter_amount

    # Cap at remaining time
    capped_delay = min(total_delay, max_remaining_time)

    return max(0, capped_delay)


def validate_feed_content(feed: Any) -> dict[str, Any]:
    """
    Validate feed content and extract metadata.

    Args:
        feed: Parsed feedparser result

    Returns:
        Dictionary with feed metadata and validation results
    """
    metadata = {
        "title": getattr(feed.feed, "title", "Unknown Feed"),
        "link": getattr(feed.feed, "link", ""),
        "description": getattr(feed.feed, "description", ""),
        "entry_count": len(feed.entries) if hasattr(feed, "entries") else 0,
        "parsing_errors": [],
    }

    # Check for parsing errors
    if hasattr(feed, "bozo") and feed.bozo and hasattr(feed, "bozo_exception"):
        metadata["parsing_errors"].append(str(feed.bozo_exception))

    # Validate entries structure
    if not hasattr(feed, "entries"):
        metadata["parsing_errors"].append("Feed missing entries")
    elif not isinstance(feed.entries, list):
        metadata["parsing_errors"].append("Feed entries is not a list")

    return metadata
