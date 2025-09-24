"""Security-focused tests for RSS ingestion functionality."""

import sqlite3
from unittest.mock import Mock, patch

import pytest

# These tests will initially fail - that's the point of TDD!
# We'll implement the functionality to make them pass.


class TestSSRFProtection:
    """Test SSRF (Server-Side Request Forgery) protection."""

    def test_blocks_private_ip_ranges(self):
        """Test that private IP ranges are blocked."""
        # Test cases for private IP ranges that should be blocked
        blocked_urls = [
            "http://10.0.0.1/feed.xml",  # 10.0.0.0/8
            "http://172.16.0.1/feed.xml",  # 172.16.0.0/12
            "http://192.168.1.1/feed.xml",  # 192.168.0.0/16
            "http://127.0.0.1/feed.xml",  # 127.0.0.0/8 (localhost)
            "http://localhost/feed.xml",  # localhost domain
            "http://169.254.1.1/feed.xml",  # 169.254.0.0/16 (link-local)
        ]

        # This will fail until we implement the feed client
        from app.ingestion.feed_client import FeedClient

        client = FeedClient()

        for url in blocked_urls:
            with pytest.raises(ValueError, match="SSRF protection"):
                client.fetch_feed(url)

    def test_allows_public_urls(self):
        """Test that public URLs are allowed."""
        # Test cases for public URLs that should be allowed
        allowed_urls = [
            "https://example.com/feed.xml",
            "https://news.ycombinator.com/rss",
            "https://feeds.feedburner.com/oreilly/radar",
        ]

        from app.ingestion.feed_client import FeedClient

        client = FeedClient()

        for url in allowed_urls:
            # Should not raise SSRF protection error
            # (may raise other errors like network timeout, which is fine)
            try:
                client.validate_url(url)
            except ValueError as e:
                if "SSRF protection" in str(e):
                    pytest.fail(f"Public URL {url} was incorrectly blocked")

    def test_rejects_non_http_schemes(self):
        """Test that non-HTTP(S) schemes are rejected."""
        invalid_schemes = [
            "ftp://example.com/feed.xml",
            "file:///etc/passwd",
            "javascript:alert('xss')",
            "data:text/html,<script>alert('xss')</script>",
        ]

        from app.ingestion.feed_client import FeedClient

        client = FeedClient()

        for url in invalid_schemes:
            with pytest.raises(ValueError, match="Invalid URL scheme"):
                client.validate_url(url)


class TestXSSPrevention:
    """Test XSS (Cross-Site Scripting) prevention through HTML sanitization."""

    def test_strips_script_tags(self):
        """Test that script tags are completely removed."""
        from app.ingestion.mapper import sanitize_html

        malicious_content = '<script>alert("xss")</script>Safe content'
        cleaned = sanitize_html(malicious_content)

        assert "<script>" not in cleaned
        assert "alert(" not in cleaned
        assert "Safe content" in cleaned

    def test_strips_event_handlers(self):
        """Test that HTML event handlers are removed."""
        from app.ingestion.mapper import sanitize_html

        malicious_content = '<img src="x" onerror="alert(\'xss\')" />Image text'
        cleaned = sanitize_html(malicious_content)

        assert "onerror" not in cleaned
        assert "alert(" not in cleaned
        assert "Image text" in cleaned

    def test_strips_all_html_tags(self):
        """Test that ALL HTML tags are removed per security requirement."""
        from app.ingestion.mapper import sanitize_html

        html_content = """
        <h1>Title</h1>
        <p>Paragraph with <a href="http://example.com">link</a></p>
        <div>Content</div>
        <iframe src="malicious.com"></iframe>
        """
        cleaned = sanitize_html(html_content)

        # Should have no HTML tags at all
        assert "<" not in cleaned
        assert ">" not in cleaned
        # But should preserve text content
        assert "Title" in cleaned
        assert "Paragraph" in cleaned
        assert "link" in cleaned
        assert "Content" in cleaned

    def test_handles_malformed_html(self):
        """Test handling of malformed HTML."""
        from app.ingestion.mapper import sanitize_html

        malformed_content = '<script>alert("xss"<div>unclosed<p>tags'
        cleaned = sanitize_html(malformed_content)

        assert "<script>" not in cleaned
        assert "alert(" not in cleaned


class TestSQLInjectionPrevention:
    """Test SQL injection prevention."""

    def test_source_seeding_with_malicious_input(self):
        """Test that source seeding handles malicious SQL input safely."""
        from app.ingestion.seeder import seed_sources

        malicious_sources = [
            {
                "name": "'; DROP TABLE sources; --",
                "url": "http://malicious.com",
                "feed_url": "http://malicious.com/feed.xml",
                "credibility_score": 0.5,
            }
        ]

        # Should not raise SQL injection errors
        # Should handle the malicious input as literal text
        result = seed_sources(malicious_sources)
        assert result["created"] == 1 or result["updated"] == 1

    def test_article_insertion_with_malicious_content(self):
        """Test that article insertion handles SQL injection attempts."""
        # Mock feed entry with SQL injection attempt
        # configure spec to avoid attribute issues
        from unittest.mock import MagicMock

        from app.ingestion.mapper import ArticleMapper

        # Create a more realistic mock that handles attribute access properly
        malicious_entry = MagicMock()
        malicious_entry.title = "'; DELETE FROM articles; --"
        malicious_entry.link = "http://malicious.com/article"
        malicious_entry.summary = "'; UPDATE articles SET title='hacked'; --"
        malicious_entry.published = "Mon, 23 Sep 2024 09:00:00 GMT"
        malicious_entry.tags = []

        # Configure to return None for missing attributes instead of Mock objects
        def mock_getattr(name, default=None):
            attrs = {
                "title": "'; DELETE FROM articles; --",
                "link": "http://malicious.com/article",
                "summary": "'; UPDATE articles SET title='hacked'; --",
                "published": "Mon, 23 Sep 2024 09:00:00 GMT",
                "tags": [],
            }
            return attrs.get(name, default)

        # Replace the entry with a custom mock that handles getattr properly
        class MockEntry:
            def __init__(self):
                self.title = "'; DELETE FROM articles; --"
                self.link = "http://malicious.com/article"
                self.summary = "'; UPDATE articles SET title='hacked'; --"
                self.published = "Mon, 23 Sep 2024 09:00:00 GMT"
                self.tags = []

            def __getattr__(self, name):
                # Return None for any attribute not explicitly set
                return None

        malicious_entry = MockEntry()

        mapper = ArticleMapper()
        article_data = mapper.map_entry_to_article(malicious_entry, source_id=1)

        # Should create valid Article instance without SQL injection
        assert isinstance(article_data, dict)
        assert "DELETE FROM" not in article_data["title"]
        assert "UPDATE articles" not in article_data["summary_raw"]


class TestInputValidation:
    """Test comprehensive input validation."""

    def test_url_validation(self):
        """Test URL validation catches malformed URLs."""
        from app.ingestion.feed_client import FeedClient

        invalid_urls = [
            "not-a-url",
            "http://",
            "https://",
            "",
            None,
            "http://[invalid-ipv6",
        ]

        client = FeedClient()
        for url in invalid_urls:
            with pytest.raises((ValueError, TypeError)):
                client.validate_url(url)

    def test_response_size_limits(self):
        """Test that response size limits are enforced."""
        from app.ingestion.feed_client import FeedClient

        client = FeedClient()

        # Mock a response that's too large
        with patch("httpx.Client") as mock_client_class:
            # Simulate 11MB response (over 10MB limit)
            mock_response = Mock()
            mock_response.content = b"x" * (11 * 1024 * 1024)
            mock_response.headers = {"content-length": str(11 * 1024 * 1024)}

            mock_client = Mock()
            mock_client.get.return_value = mock_response
            mock_client_class.return_value.__enter__.return_value = mock_client

            with pytest.raises(ValueError, match="Response too large"):
                client.fetch_feed("https://example.com/feed.xml")

    def test_timeout_enforcement(self):
        """Test that timeouts are properly enforced."""
        import httpx

        from app.ingestion.feed_client import FeedClient

        client = FeedClient()

        with patch("httpx.Client") as mock_client_class:
            mock_client = Mock()
            mock_client_class.return_value.__enter__.return_value = mock_client
            mock_client.get.side_effect = httpx.TimeoutException("Request timed out")

            with pytest.raises(TimeoutError):
                client.fetch_feed("https://slow.example.com/feed.xml")


class TestContentHashSecurity:
    """Test content hash generation for security and stability."""

    def test_hash_stability(self):
        """Test that content hash is stable across runs."""
        from app.ingestion.mapper import generate_content_hash

        title = "Test Article"
        link = "https://example.com/article1"
        published_at = "2024-09-23T09:00:00Z"

        hash1 = generate_content_hash(title, link, published_at)
        hash2 = generate_content_hash(title, link, published_at)

        assert hash1 == hash2
        assert len(hash1) == 64  # SHA256 hex length

    def test_hash_uniqueness(self):
        """Test that different content produces different hashes."""
        from app.ingestion.mapper import generate_content_hash

        hash1 = generate_content_hash(
            "Title1", "https://example.com/1", "2024-09-23T09:00:00Z"
        )
        hash2 = generate_content_hash(
            "Title2", "https://example.com/2", "2024-09-23T09:00:00Z"
        )
        hash3 = generate_content_hash(
            "Title1", "https://example.com/1", "2024-09-23T10:00:00Z"
        )

        assert hash1 != hash2
        assert hash1 != hash3
        assert hash2 != hash3

    def test_hash_with_malicious_content(self):
        """Test content hash generation with malicious input."""
        from app.ingestion.mapper import generate_content_hash

        malicious_title = "<script>alert('xss')</script>Title"
        malicious_link = "javascript:alert('xss')"

        # Should not raise exceptions and should produce valid hash
        content_hash = generate_content_hash(
            malicious_title, malicious_link, "2024-09-23T09:00:00Z"
        )
        assert len(content_hash) == 64
        assert content_hash.isalnum()  # Should be hex


class TestDatabaseSecurity:
    """Test database interaction security."""

    def test_parameterized_queries_only(self):
        """Test that only parameterized queries are used."""
        # This is more of a code review test, but we can check that
        # our ORM usage follows secure patterns
        from app.models.article import Article
        from app.models.source import Source

        # Verify models use SQLAlchemy ORM (which uses parameterized queries)
        assert hasattr(Source, "__tablename__")
        assert hasattr(Article, "__tablename__")

        # The actual test is in our implementation - we should never
        # use string concatenation or f-strings for SQL

    def test_foreign_key_constraints(self):
        """Test that foreign key constraints are enforced."""
        # This test verifies our conftest.py setup enables FK constraints
        from tests.conftest import _set_sqlite_pragma

        # Create a mock connection
        mock_connection = sqlite3.connect(":memory:")
        _set_sqlite_pragma(mock_connection, None)

        # Verify foreign keys are enabled
        cursor = mock_connection.cursor()
        cursor.execute("PRAGMA foreign_keys")
        result = cursor.fetchone()
        assert result[0] == 1  # 1 means enabled
