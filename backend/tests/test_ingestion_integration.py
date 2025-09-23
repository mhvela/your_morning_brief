"""Integration tests for RSS ingestion functionality."""

import json
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

# These tests will initially fail - that's the point of TDD!


class TestSourceSeedingIntegration:
    """Test source seeding integration with database."""

    @pytest.fixture
    def temp_sources_file(self):
        """Create temporary sources file for testing."""
        sources_data = [
            {
                "name": "Integration Test Source",
                "url": "https://integration.example.com",
                "feed_url": "https://integration.example.com/feed.xml",
                "credibility_score": 0.9,
                "is_active": True,
            }
        ]

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(sources_data, f)
            temp_file = f.name

        yield temp_file

        # Cleanup
        Path(temp_file).unlink(missing_ok=True)

    def test_seed_sources_creates_database_records(self, temp_sources_file):
        """Test that seeding creates actual database records."""
        from app.db.session import SessionLocal
        from app.ingestion.seeder import seed_sources_from_file
        from app.models.source import Source

        # Run seeding
        result = seed_sources_from_file(temp_sources_file)
        assert result["created"] == 1

        # Verify in database
        with SessionLocal() as db:
            source = (
                db.query(Source)
                .filter_by(feed_url="https://integration.example.com/feed.xml")
                .first()
            )

            assert source is not None
            assert source.name == "Integration Test Source"
            assert source.credibility_score == 0.9
            assert source.is_active is True

    def test_seed_sources_idempotent_operation(self, temp_sources_file):
        """Test that re-seeding same sources is idempotent."""
        from app.ingestion.seeder import seed_sources_from_file

        # First run
        result1 = seed_sources_from_file(temp_sources_file)
        assert result1["created"] == 1

        # Second run should update, not create
        result2 = seed_sources_from_file(temp_sources_file)
        assert result2["created"] == 0
        assert result2["updated"] == 1


class TestFeedIngestionIntegration:
    """Test feed ingestion integration with real feed parsing."""

    def test_ingest_from_local_feed_file(self):
        """Test ingestion from local RSS feed file."""
        from app.db.session import SessionLocal
        from app.ingestion.ingest_one import ingest_feed_from_file
        from app.models.article import Article

        # Use our test fixture
        feed_file = Path(__file__).parent / "fixtures" / "feeds" / "sample_feed.xml"

        # Mock source exists
        with patch("app.ingestion.ingest_one.get_or_create_source") as mock_source:
            mock_source.return_value = Mock(id=1, name="Test Source")

            result = ingest_feed_from_file(str(feed_file))

            assert result["parsed"] >= 10  # Our fixture has 12 articles
            assert result["inserted"] >= 10
            assert result["errors"] == 0

        # Verify articles in database
        with SessionLocal() as db:
            articles = db.query(Article).filter_by(source_id=1).all()
            assert len(articles) >= 10

            # Check specific article
            ai_article = next(
                (a for a in articles if "AI Breakthrough" in a.title), None
            )
            assert ai_article is not None
            assert ai_article.link == "https://example.com/article1"
            assert "language processing" in ai_article.summary_raw.lower()

    def test_ingest_handles_duplicate_articles(self):
        """Test that re-ingesting same feed doesn't create duplicates."""
        from app.ingestion.ingest_one import ingest_feed_from_file

        feed_file = Path(__file__).parent / "fixtures" / "feeds" / "sample_feed.xml"

        # Mock source exists
        with patch("app.ingestion.ingest_one.get_or_create_source") as mock_source:
            mock_source.return_value = Mock(id=1, name="Test Source")

            # First ingestion
            result1 = ingest_feed_from_file(str(feed_file))
            assert result1["inserted"] >= 10

            # Second ingestion should skip duplicates
            result2 = ingest_feed_from_file(str(feed_file))
            assert result2["inserted"] == 0
            assert result2["skipped"] >= 10

    def test_ingest_with_malicious_content(self):
        """Test ingestion sanitizes malicious content."""
        from app.db.session import SessionLocal
        from app.ingestion.ingest_one import ingest_feed_from_file
        from app.models.article import Article

        # Use malicious feed fixture
        feed_file = (
            Path(__file__).parent / "fixtures" / "malicious_feeds" / "xss_feed.xml"
        )

        with patch("app.ingestion.ingest_one.get_or_create_source") as mock_source:
            mock_source.return_value = Mock(id=999, name="Malicious Source")

            result = ingest_feed_from_file(str(feed_file))
            assert result["parsed"] >= 3
            assert result["inserted"] >= 3

        # Verify content was sanitized
        with SessionLocal() as db:
            articles = db.query(Article).filter_by(source_id=999).all()

            for article in articles:
                # Should not contain any script tags or event handlers
                assert "<script>" not in article.title
                assert (
                    "<script>" not in article.summary_raw or article.summary_raw is None
                )
                assert "onerror" not in (article.summary_raw or "")
                assert "javascript:" not in (article.summary_raw or "")

    def test_ingest_updates_source_metadata(self):
        """Test that ingestion updates source last_fetched_at and error counts."""
        from app.db.session import SessionLocal
        from app.ingestion.ingest_one import ingest_feed_from_file
        from app.models.source import Source

        feed_file = Path(__file__).parent / "fixtures" / "feeds" / "sample_feed.xml"

        with patch("app.ingestion.ingest_one.get_or_create_source") as mock_source:
            mock_source.return_value = Mock(id=1, name="Test Source")

            result = ingest_feed_from_file(str(feed_file))
            assert result["inserted"] >= 0

        # Verify source metadata was updated
        with SessionLocal() as db:
            source = db.query(Source).filter_by(id=1).first()
            assert source.last_fetched_at is not None
            assert source.error_count == 0  # No errors expected


class TestCLIIntegration:
    """Test CLI command integration."""

    def test_cli_seed_sources_command(self):
        """Test CLI source seeding command."""
        import sys

        from app.ingestion.ingest_one import main

        # Test file path
        test_file = Path(__file__).parent / "fixtures" / "sources.test.json"

        # Mock command line arguments
        test_args = ["ingest_one.py", "--seed-sources", str(test_file)]

        with patch.object(sys, "argv", test_args):
            # Should run without exceptions
            try:
                result = main()
                # main() should return 0 for success
                assert result == 0 or result is None
            except SystemExit as e:
                # sys.exit(0) is also acceptable
                assert e.code == 0

    def test_cli_ingest_feed_by_url_command(self):
        """Test CLI feed ingestion by URL command."""
        import sys

        from app.ingestion.ingest_one import main

        test_args = ["ingest_one.py", "--feed-url", "https://example.com/feed.xml"]

        with (
            patch.object(sys, "argv", test_args),
            patch("app.ingestion.feed_client.FeedClient.fetch_feed") as mock_fetch,
        ):
            # Mock successful feed fetch
            mock_feed = Mock()
            mock_feed.entries = []
            mock_fetch.return_value = mock_feed

            try:
                result = main()
                assert result == 0 or result is None
            except SystemExit as e:
                assert e.code == 0

    def test_cli_ingest_feed_by_source_id_command(self):
        """Test CLI feed ingestion by source ID command."""
        import sys

        from app.ingestion.ingest_one import main

        test_args = ["ingest_one.py", "--source-id", "1"]

        with (
            patch.object(sys, "argv", test_args),
            patch("app.ingestion.ingest_one.get_source_by_id") as mock_get_source,
            patch("app.ingestion.feed_client.FeedClient.fetch_feed") as mock_fetch,
        ):
            # Mock source exists
            mock_source = Mock()
            mock_source.feed_url = "https://example.com/feed.xml"
            mock_get_source.return_value = mock_source

            # Mock successful feed fetch
            mock_feed = Mock()
            mock_feed.entries = []
            mock_fetch.return_value = mock_feed

            try:
                result = main()
                assert result == 0 or result is None
            except SystemExit as e:
                assert e.code == 0

    def test_cli_argument_validation(self):
        """Test CLI argument validation."""
        import sys

        from app.ingestion.ingest_one import main

        # No arguments should fail
        test_args = ["ingest_one.py"]

        with patch.object(sys, "argv", test_args):
            with pytest.raises(SystemExit) as exc_info:
                main()
            # Should exit with non-zero code
            assert exc_info.value.code != 0

    def test_cli_mutually_exclusive_arguments(self):
        """Test that mutually exclusive arguments are handled."""
        import sys

        from app.ingestion.ingest_one import main

        # Both --feed-url and --source-id should be invalid
        test_args = [
            "ingest_one.py",
            "--feed-url",
            "https://example.com/feed.xml",
            "--source-id",
            "1",
        ]

        with patch.object(sys, "argv", test_args):
            with pytest.raises(SystemExit) as exc_info:
                main()
            # Should exit with non-zero code
            assert exc_info.value.code != 0


class TestErrorHandlingIntegration:
    """Test error handling in integration scenarios."""

    def test_ingest_handles_network_errors(self):
        """Test ingestion handles network errors gracefully."""
        from app.ingestion.ingest_one import ingest_feed_from_url

        with patch("app.ingestion.feed_client.FeedClient.fetch_feed") as mock_fetch:
            mock_fetch.side_effect = Exception("Network error")

            result = ingest_feed_from_url("https://unreachable.example.com/feed.xml")

            assert result["errors"] == 1
            assert result["inserted"] == 0

    def test_ingest_handles_malformed_xml(self):
        """Test ingestion handles malformed XML gracefully."""
        from app.ingestion.ingest_one import ingest_feed_from_file

        # Create temporary malformed XML file
        with tempfile.NamedTemporaryFile(mode="w", suffix=".xml", delete=False) as f:
            f.write(
                "<?xml version='1.0'?><rss><channel><item><title>Unclosed"
            )  # Malformed
            malformed_file = f.name

        try:
            with patch("app.ingestion.ingest_one.get_or_create_source") as mock_source:
                mock_source.return_value = Mock(id=1, name="Test Source")

                result = ingest_feed_from_file(malformed_file)

                # Should handle gracefully, not crash
                assert "errors" in result
        finally:
            Path(malformed_file).unlink(missing_ok=True)

    def test_ingest_handles_database_errors(self):
        """Test ingestion handles database errors gracefully."""
        from app.ingestion.ingest_one import ingest_feed_from_file

        feed_file = Path(__file__).parent / "fixtures" / "feeds" / "sample_feed.xml"

        with (
            patch("app.ingestion.ingest_one.get_or_create_source") as mock_source,
            patch("app.db.session.SessionLocal") as mock_session,
        ):
            mock_source.return_value = Mock(id=1, name="Test Source")
            mock_session.side_effect = Exception("Database connection error")

            result = ingest_feed_from_file(str(feed_file))

            # Should handle gracefully
            assert result["errors"] >= 1


class TestPerformanceIntegration:
    """Test performance characteristics of ingestion."""

    def test_ingestion_completes_within_time_limit(self):
        """Test that single feed ingestion completes within 5 seconds."""
        import time

        from app.ingestion.ingest_one import ingest_feed_from_file

        feed_file = Path(__file__).parent / "fixtures" / "feeds" / "sample_feed.xml"

        with patch("app.ingestion.ingest_one.get_or_create_source") as mock_source:
            mock_source.return_value = Mock(id=1, name="Test Source")

            start_time = time.time()
            ingest_feed_from_file(str(feed_file))
            end_time = time.time()

            duration = end_time - start_time
            assert duration < 5.0  # Should complete within 5 seconds

    def test_ingestion_handles_large_feed(self):
        """Test ingestion can handle feeds with many items."""
        from app.ingestion.ingest_one import ingest_feed_from_file

        # Mock a large feed with 100 items
        large_feed_content = """<?xml version="1.0"?>
        <rss version="2.0">
            <channel>
                <title>Large Feed</title>
        """

        for i in range(100):
            large_feed_content += f"""
                <item>
                    <title>Article {i}</title>
                    <link>https://example.com/article{i}</link>
                    <description>Description for article {i}</description>
                    <pubDate>Mon, 23 Sep 2024 09:00:00 GMT</pubDate>
                </item>
            """

        large_feed_content += """
            </channel>
        </rss>
        """

        with tempfile.NamedTemporaryFile(mode="w", suffix=".xml", delete=False) as f:
            f.write(large_feed_content)
            large_feed_file = f.name

        try:
            with patch("app.ingestion.ingest_one.get_or_create_source") as mock_source:
                mock_source.return_value = Mock(id=1, name="Test Source")

                result = ingest_feed_from_file(large_feed_file)

                assert result["parsed"] == 100
                assert result["inserted"] == 100
                assert result["errors"] == 0
        finally:
            Path(large_feed_file).unlink(missing_ok=True)
