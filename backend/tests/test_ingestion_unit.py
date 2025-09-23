"""Unit tests for RSS ingestion functionality."""

import pytest
from unittest.mock import Mock, patch
from datetime import datetime
import json
from pathlib import Path

# These tests will initially fail - that's the point of TDD!


class TestSourceSeeding:
    """Test source seeding functionality."""

    def test_seed_sources_from_json_file(self):
        """Test seeding sources from JSON file."""
        from app.ingestion.seeder import seed_sources_from_file

        # Use our test fixture
        test_file = Path(__file__).parent / "fixtures" / "sources.test.json"
        result = seed_sources_from_file(str(test_file))

        assert "created" in result
        assert "updated" in result
        assert "skipped" in result
        assert result["created"] >= 0
        assert result["updated"] >= 0
        assert result["skipped"] >= 0

    def test_seed_sources_validates_json_schema(self):
        """Test that source seeding validates required fields."""
        from app.ingestion.seeder import seed_sources

        # Missing required fields
        invalid_sources = [
            {"name": "Test", "url": "http://example.com"},  # Missing feed_url
            {"feed_url": "http://example.com/feed"},  # Missing name and url
            {},  # Missing all required fields
        ]

        with pytest.raises(ValueError, match="Invalid source data"):
            seed_sources(invalid_sources)

    def test_seed_sources_validates_optional_fields(self):
        """Test that optional fields have proper defaults."""
        from app.ingestion.seeder import seed_sources

        minimal_source = [
            {
                "name": "Minimal Source",
                "url": "http://minimal.example.com",
                "feed_url": "http://minimal.example.com/feed.xml"
            }
        ]

        result = seed_sources(minimal_source)
        # Should succeed and apply defaults
        assert result["created"] == 1 or result["updated"] == 1

    def test_seed_sources_upserts_by_feed_url(self):
        """Test that sources are upserted by feed_url."""
        from app.ingestion.seeder import seed_sources

        # First insertion
        sources = [
            {
                "name": "Test Source v1",
                "url": "http://test.example.com",
                "feed_url": "http://test.example.com/feed.xml",
                "credibility_score": 0.5
            }
        ]
        result1 = seed_sources(sources)

        # Update with same feed_url but different name
        sources[0]["name"] = "Test Source v2"
        sources[0]["credibility_score"] = 0.8
        result2 = seed_sources(sources)

        # Should update existing record
        assert result2["created"] == 0
        assert result2["updated"] == 1

    def test_seed_sources_handles_database_errors(self):
        """Test graceful handling of database errors."""
        from app.ingestion.seeder import seed_sources

        with patch('app.models.source.Source') as mock_source:
            mock_source.side_effect = Exception("Database error")

            with pytest.raises(Exception, match="Database error"):
                seed_sources([{"name": "Test", "url": "http://test.com", "feed_url": "http://test.com/feed"}])


class TestFeedClient:
    """Test feed client functionality (will be implemented after security tests pass)."""

    def test_fetch_feed_returns_parsed_content(self):
        """Test that fetch_feed returns feedparser-compatible content."""
        from app.ingestion.feed_client import FeedClient

        client = FeedClient()

        with patch('httpx.get') as mock_get:
            # Mock RSS content
            mock_response = Mock()
            mock_response.content = b"""<?xml version="1.0"?>
            <rss version="2.0">
                <channel>
                    <title>Test Feed</title>
                    <item>
                        <title>Test Article</title>
                        <link>http://example.com/article1</link>
                        <description>Test description</description>
                    </item>
                </channel>
            </rss>"""
            mock_response.headers = {'content-length': '200'}
            mock_get.return_value = mock_response

            feed = client.fetch_feed("https://example.com/feed.xml")

            assert hasattr(feed, 'entries')
            assert len(feed.entries) > 0
            assert feed.entries[0].title == "Test Article"

    def test_fetch_feed_includes_user_agent(self):
        """Test that requests include proper User-Agent."""
        from app.ingestion.feed_client import FeedClient

        client = FeedClient()

        with patch('httpx.get') as mock_get:
            mock_response = Mock()
            mock_response.content = b"<rss></rss>"
            mock_response.headers = {'content-length': '20'}
            mock_get.return_value = mock_response

            client.fetch_feed("https://example.com/feed.xml")

            # Verify httpx.get was called with proper headers
            mock_get.assert_called_once()
            call_kwargs = mock_get.call_args[1]
            assert 'headers' in call_kwargs
            assert 'User-Agent' in call_kwargs['headers']
            assert 'YourMorningBriefBot' in call_kwargs['headers']['User-Agent']

    def test_fetch_feed_respects_timeout(self):
        """Test that requests respect configured timeout."""
        from app.ingestion.feed_client import FeedClient

        client = FeedClient()

        with patch('httpx.get') as mock_get:
            mock_response = Mock()
            mock_response.content = b"<rss></rss>"
            mock_response.headers = {'content-length': '20'}
            mock_get.return_value = mock_response

            client.fetch_feed("https://example.com/feed.xml")

            # Verify timeout was set
            mock_get.assert_called_once()
            call_kwargs = mock_get.call_args[1]
            assert 'timeout' in call_kwargs
            assert call_kwargs['timeout'] > 0


class TestMapper:
    """Test article mapping functionality."""

    def test_map_entry_to_article_fields(self):
        """Test mapping feed entry to article fields."""
        from app.ingestion.mapper import ArticleMapper

        # Mock feedparser entry
        mock_entry = Mock()
        mock_entry.title = "Test Article Title"
        mock_entry.link = "https://example.com/article1"
        mock_entry.summary = "This is a test article description."
        mock_entry.published = "Mon, 23 Sep 2024 09:00:00 GMT"
        mock_entry.author = "Test Author"
        mock_entry.tags = [Mock(term="tech"), Mock(term="news")]

        mapper = ArticleMapper()
        article_data = mapper.map_entry_to_article(mock_entry, source_id=1)

        assert article_data["title"] == "Test Article Title"
        assert article_data["link"] == "https://example.com/article1"
        assert article_data["summary_raw"] == "This is a test article description."
        assert article_data["source_id"] == 1
        assert article_data["author"] == "Test Author"
        assert article_data["tags"] == ["tech", "news"]
        assert "content_hash" in article_data
        assert "published_at" in article_data

    def test_map_entry_handles_missing_fields(self):
        """Test mapping handles missing optional fields gracefully."""
        from app.ingestion.mapper import ArticleMapper

        # Minimal mock entry (only required fields)
        mock_entry = Mock()
        mock_entry.title = "Minimal Article"
        mock_entry.link = "https://example.com/minimal"
        # Missing: summary, published, author, tags
        del mock_entry.summary
        del mock_entry.published
        del mock_entry.author
        del mock_entry.tags

        mapper = ArticleMapper()
        article_data = mapper.map_entry_to_article(mock_entry, source_id=1)

        assert article_data["title"] == "Minimal Article"
        assert article_data["link"] == "https://example.com/minimal"
        assert article_data["summary_raw"] is None or article_data["summary_raw"] == ""
        assert article_data["author"] is None
        assert article_data["tags"] == []
        assert "content_hash" in article_data
        assert "published_at" in article_data  # Should have fallback

    def test_published_at_parsing(self):
        """Test various published date formats are parsed correctly."""
        from app.ingestion.mapper import parse_published_date

        test_dates = [
            "Mon, 23 Sep 2024 09:00:00 GMT",
            "2024-09-23T09:00:00Z",
            "2024-09-23T09:00:00+00:00",
            "September 23, 2024",
        ]

        for date_str in test_dates:
            parsed = parse_published_date(date_str)
            assert isinstance(parsed, datetime)
            assert parsed.tzinfo is not None  # Should be timezone-aware

    def test_published_at_fallback(self):
        """Test fallback behavior when published date is missing."""
        from app.ingestion.mapper import parse_published_date

        # None or invalid dates should return fallback
        fallback1 = parse_published_date(None)
        fallback2 = parse_published_date("invalid date string")
        fallback3 = parse_published_date("")

        assert isinstance(fallback1, datetime)
        assert isinstance(fallback2, datetime)
        assert isinstance(fallback3, datetime)

    def test_content_hash_generation(self):
        """Test content hash generation follows specification."""
        from app.ingestion.mapper import generate_content_hash

        title = "Test Article"
        link = "https://example.com/article1"
        published_at = "2024-09-23T09:00:00Z"

        content_hash = generate_content_hash(title, link, published_at)

        # Should be SHA256 hex (64 characters)
        assert len(content_hash) == 64
        assert all(c in '0123456789abcdef' for c in content_hash.lower())

    def test_content_hash_normalization(self):
        """Test content hash normalization for stability."""
        from app.ingestion.mapper import generate_content_hash

        # Different cases/whitespace should produce same hash
        hash1 = generate_content_hash("Test Article", "https://example.com/article", "2024-09-23T09:00:00Z")
        hash2 = generate_content_hash("  test article  ", "https://example.com/article", "2024-09-23T09:00:00Z")
        hash3 = generate_content_hash("TEST ARTICLE", "https://example.com/article", "2024-09-23T09:00:00Z")

        assert hash1 == hash2 == hash3


class TestConfiguration:
    """Test ingestion configuration."""

    def test_config_has_required_settings(self):
        """Test that config includes all required ingestion settings."""
        from app.core.config import settings

        required_settings = [
            'INGESTION_USER_AGENT',
            'INGESTION_TIMEOUT_SEC',
            'INGESTION_MAX_RETRIES',
            'RETRY_BACKOFF_BASE_SEC',
            'RETRY_BACKOFF_JITTER_SEC',
            'INGESTION_TOTAL_RETRY_CAP_SEC',
            'SUMMARY_MAX_LEN',
            'MAX_RESPONSE_SIZE_MB',
            'BLOCKED_NETWORKS',
            'ALLOWED_URL_SCHEMES',
        ]

        for setting in required_settings:
            assert hasattr(settings, setting), f"Missing required setting: {setting}"

    def test_config_defaults(self):
        """Test that config has sensible defaults."""
        from app.core.config import settings

        assert 'YourMorningBriefBot' in settings.INGESTION_USER_AGENT
        assert settings.INGESTION_TIMEOUT_SEC > 0
        assert settings.MAX_RESPONSE_SIZE_MB > 0
        assert len(settings.BLOCKED_NETWORKS) > 0
        assert 'http' in settings.ALLOWED_URL_SCHEMES
        assert 'https' in settings.ALLOWED_URL_SCHEMES


class TestRetryLogic:
    """Test retry logic and error handling."""

    def test_exponential_backoff_calculation(self):
        """Test exponential backoff with jitter calculation."""
        from app.ingestion.feed_client import calculate_backoff_delay

        base = 0.5
        jitter = 0.3
        max_delay = 8.0

        # Test increasing delays
        delay1 = calculate_backoff_delay(0, base, jitter, max_delay)
        delay2 = calculate_backoff_delay(1, base, jitter, max_delay)
        delay3 = calculate_backoff_delay(2, base, jitter, max_delay)

        assert 0 <= delay1 <= base + jitter
        assert base <= delay2 <= 2 * base + jitter
        assert 2 * base <= delay3 <= 4 * base + jitter

    def test_retry_cap_enforcement(self):
        """Test that total retry time is capped."""
        from app.ingestion.feed_client import calculate_backoff_delay

        base = 0.5
        jitter = 0.3
        max_delay = 2.0  # Low cap for testing

        # High retry count should be capped
        delay = calculate_backoff_delay(10, base, jitter, max_delay)
        assert delay <= max_delay