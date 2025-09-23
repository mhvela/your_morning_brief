"""Unit tests for RSS ingestion functionality."""

from datetime import datetime
from pathlib import Path
from unittest.mock import Mock, patch

import pytest
from sqlalchemy.orm import Session

# Load fixtures from test_database without importing names into module scope
pytest_plugins = ["tests.test_database"]

# These tests will initially fail - that's the point of TDD!


class TestSourceSeeding:
    """Test source seeding functionality."""

    def test_seed_sources_from_json_file(self, db_session: Session):
        """Test seeding sources from JSON file."""
        from app.ingestion.seeder import seed_sources_from_file

        # Use our test fixture
        test_file = Path(__file__).parent / "fixtures" / "sources.test.json"

        # Mock SessionLocal to return our test session
        with patch("app.ingestion.seeder.SessionLocal") as mock_session_local:
            mock_session_local.return_value.__enter__.return_value = db_session
            mock_session_local.return_value.__exit__.return_value = None
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

    def test_seed_sources_validates_optional_fields(self, db_session: Session):
        """Test that optional fields have proper defaults."""
        from app.ingestion.seeder import seed_sources

        minimal_source = [
            {
                "name": "Minimal Source",
                "url": "http://minimal.example.com",
                "feed_url": "http://minimal.example.com/feed.xml",
            }
        ]

        # Mock SessionLocal to return our test session
        with patch("app.ingestion.seeder.SessionLocal") as mock_session_local:
            mock_session_local.return_value.__enter__.return_value = db_session
            mock_session_local.return_value.__exit__.return_value = None
            result = seed_sources(minimal_source)

        # Should succeed and apply defaults
        assert result["created"] == 1 or result["updated"] == 1

    def test_seed_sources_upserts_by_feed_url(self, db_session: Session):
        """Test that sources are upserted by feed_url."""
        from app.ingestion.seeder import seed_sources

        # First insertion
        sources = [
            {
                "name": "Test Source v1",
                "url": "http://test.example.com",
                "feed_url": "http://test.example.com/feed.xml",
                "credibility_score": 0.5,
            }
        ]

        # Mock SessionLocal to return our test session
        with patch("app.ingestion.seeder.SessionLocal") as mock_session_local:
            mock_session_local.return_value.__enter__.return_value = db_session
            mock_session_local.return_value.__exit__.return_value = None
            seed_sources(sources)

            # Update with same feed_url but different name
            sources[0]["name"] = "Test Source v2"
            sources[0]["credibility_score"] = 0.8
            result2 = seed_sources(sources)

        # Should update existing record
        assert result2["created"] == 0
        assert result2["updated"] == 1

    def test_seed_sources_handles_database_errors(self, db_session: Session):
        """Test graceful handling of database errors."""
        from app.ingestion.seeder import seed_sources

        # Mock the database session to raise an error on add
        with patch("app.ingestion.seeder.SessionLocal") as mock_session_local:
            mock_session_local.return_value.__enter__.return_value = db_session
            mock_session_local.return_value.__exit__.return_value = None

            # Mock db.add to raise an error before logging
            db_session.add = Mock(side_effect=Exception("Database error"))

            with pytest.raises(Exception, match="Database error"):
                seed_sources(
                    [
                        {
                            "name": "Test",
                            "url": "http://test.com",
                            "feed_url": "http://test.com/feed",
                        }
                    ]
                )


class TestFeedClient:
    """Test feed client functionality."""

    def test_fetch_feed_returns_parsed_content(self):
        """Test that fetch_feed returns feedparser-compatible content."""
        from app.ingestion.feed_client import FeedClient

        client = FeedClient()

        with patch("httpx.Client") as mock_client:
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
            mock_response.headers = {"content-length": "200"}
            mock_response.status_code = 200
            mock_response.raise_for_status = Mock()  # Don't raise for 200

            # Mock the context manager and the get method
            mock_client_instance = Mock()
            mock_client_instance.get.return_value = mock_response
            mock_client.return_value.__enter__.return_value = mock_client_instance
            mock_client.return_value.__exit__.return_value = None

            feed = client.fetch_feed("https://example.com/feed.xml")

            assert hasattr(feed, "entries")
            assert len(feed.entries) > 0
            assert feed.entries[0].title == "Test Article"

    def test_fetch_feed_includes_user_agent(self):
        """Test that requests include proper User-Agent."""
        from app.ingestion.feed_client import FeedClient

        client = FeedClient()

        with patch("httpx.Client") as mock_client:
            mock_response = Mock()
            mock_response.content = b"<rss></rss>"
            mock_response.headers = {"content-length": "20"}
            mock_response.status_code = 200
            mock_response.raise_for_status = Mock()

            # Mock the context manager and the get method
            mock_client_instance = Mock()
            mock_client_instance.get.return_value = mock_response
            mock_client.return_value.__enter__.return_value = mock_client_instance
            mock_client.return_value.__exit__.return_value = None

            client.fetch_feed("https://example.com/feed.xml")

            # Verify get was called with proper headers
            mock_client_instance.get.assert_called_once()
            call_kwargs = mock_client_instance.get.call_args[1]
            assert "headers" in call_kwargs
            assert "User-Agent" in call_kwargs["headers"]
            assert "YourMorningBriefBot" in call_kwargs["headers"]["User-Agent"]

    def test_fetch_feed_respects_timeout(self):
        """Test that requests respect configured timeout."""
        from app.ingestion.feed_client import FeedClient

        client = FeedClient()

        with patch("httpx.Client") as mock_client:
            mock_response = Mock()
            mock_response.content = b"<rss></rss>"
            mock_response.headers = {"content-length": "20"}
            mock_response.status_code = 200
            mock_response.raise_for_status = Mock()

            # Mock the context manager and the get method
            mock_client_instance = Mock()
            mock_client_instance.get.return_value = mock_response
            mock_client.return_value.__enter__.return_value = mock_client_instance
            mock_client.return_value.__exit__.return_value = None

            client.fetch_feed("https://example.com/feed.xml")

            # Verify timeout was set on the client constructor
            mock_client.assert_called_once()
            call_kwargs = mock_client.call_args[1]
            assert "timeout" in call_kwargs
            assert call_kwargs["timeout"] > 0


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
        # Create a Mock that raises AttributeError for missing attributes
        class MinimalEntry:
            def __init__(self):
                self.title = "Minimal Article"
                self.link = "https://example.com/minimal"

            def __getattr__(self, name):
                # For any attribute not explicitly set, raise AttributeError
                raise AttributeError(
                    f"'{self.__class__.__name__}' object has no attribute '{name}'"
                )

        mock_entry = MinimalEntry()

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
        assert all(c in "0123456789abcdef" for c in content_hash.lower())

    def test_content_hash_normalization(self):
        """Test content hash normalization for stability."""
        from app.ingestion.mapper import generate_content_hash

        # Different cases/whitespace should produce same hash
        hash1 = generate_content_hash(
            "Test Article", "https://example.com/article", "2024-09-23T09:00:00Z"
        )
        hash2 = generate_content_hash(
            "  test article  ", "https://example.com/article", "2024-09-23T09:00:00Z"
        )
        hash3 = generate_content_hash(
            "TEST ARTICLE", "https://example.com/article", "2024-09-23T09:00:00Z"
        )

        assert hash1 == hash2 == hash3


class TestConfiguration:
    """Test ingestion configuration."""

    def test_config_has_required_settings(self):
        """Test that config includes all required ingestion settings."""
        from app.core.config import settings

        required_settings = [
            "ingestion_user_agent",
            "ingestion_timeout_sec",
            "ingestion_max_retries",
            "retry_backoff_base_sec",
            "retry_backoff_jitter_sec",
            "ingestion_total_retry_cap_sec",
            "summary_max_len",
            "max_response_size_mb",
            "blocked_networks",
            "allowed_url_schemes",
        ]

        for setting in required_settings:
            assert hasattr(settings, setting), f"Missing required setting: {setting}"

    def test_config_defaults(self):
        """Test that config has sensible defaults."""
        from app.core.config import settings

        assert "YourMorningBriefBot" in settings.ingestion_user_agent
        assert settings.ingestion_timeout_sec > 0
        assert settings.max_response_size_mb > 0
        assert len(settings.blocked_networks) > 0
        assert "http" in settings.allowed_url_schemes
        assert "https" in settings.allowed_url_schemes


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
