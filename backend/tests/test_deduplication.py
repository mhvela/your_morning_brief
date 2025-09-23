"""Tests for content hash and deduplication functionality."""

from datetime import UTC, datetime

from app.processing import content_hash


class TestContentHashGeneration:
    """Test stable content hash generation."""

    def test_stable_hash_generation(self):
        """Test that identical normalized content produces same hash."""
        title = "Test Article Title"
        link = "https://example.com/article"
        published_at = datetime(2023, 1, 15, 10, 0, 0, tzinfo=UTC)
        summary = "Test summary content"

        hash1 = content_hash.compute_content_hash(title, link, published_at, summary)
        hash2 = content_hash.compute_content_hash(title, link, published_at, summary)
        assert hash1 == hash2

    def test_hash_case_insensitive_title(self):
        """Test that title case differences don't affect hash."""
        link = "https://example.com/article"
        published_at = datetime(2023, 1, 15, 10, 0, 0, tzinfo=UTC)
        summary = "Test summary"

        hash1 = content_hash.compute_content_hash(
            "Test Title", link, published_at, summary
        )
        hash2 = content_hash.compute_content_hash(
            "test title", link, published_at, summary
        )
        hash3 = content_hash.compute_content_hash(
            "TEST TITLE", link, published_at, summary
        )

        assert hash1 == hash2 == hash3

    def test_hash_canonical_link_normalization(self):
        """Test that link normalization affects hash consistently."""
        title = "Test Title"
        published_at = datetime(2023, 1, 15, 10, 0, 0, tzinfo=UTC)
        summary = "Test summary"

        # These should produce the same hash after canonicalization
        link1 = "https://example.com/article?utm_source=feed"
        link2 = "https://example.com/article"

        hash1 = content_hash.compute_content_hash(title, link1, published_at, summary)
        hash2 = content_hash.compute_content_hash(title, link2, published_at, summary)
        assert hash1 == hash2

    def test_hash_summary_prefix_only(self):
        """Test that only first 100 chars of summary affect hash."""
        title = "Test Title"
        link = "https://example.com/article"
        published_at = datetime(2023, 1, 15, 10, 0, 0, tzinfo=UTC)

        summary1 = "A" * 100 + "B" * 100  # 200 chars
        summary2 = "A" * 100 + "C" * 100  # Same first 100, different after

        hash1 = content_hash.compute_content_hash(title, link, published_at, summary1)
        hash2 = content_hash.compute_content_hash(title, link, published_at, summary2)
        assert hash1 == hash2

    def test_hash_fallback_timestamp(self):
        """Test hash generation with fallback timestamp."""
        title = "Test Title"
        link = "https://example.com/article"
        summary = "Test summary"

        # When published_at is None, should use fallback
        hash_with_fallback = content_hash.compute_content_hash(
            title, link, None, summary
        )
        assert len(hash_with_fallback) == 64  # SHA256 hex length
        assert isinstance(hash_with_fallback, str)

    def test_hash_whitespace_normalization(self):
        """Test that whitespace differences don't affect hash."""
        link = "https://example.com/article"
        published_at = datetime(2023, 1, 15, 10, 0, 0, tzinfo=UTC)
        summary = "Test summary"

        title1 = "Test Title"
        title2 = "  Test   Title  "
        title3 = "Test\n\nTitle"

        hash1 = content_hash.compute_content_hash(title1, link, published_at, summary)
        hash2 = content_hash.compute_content_hash(title2, link, published_at, summary)
        hash3 = content_hash.compute_content_hash(title3, link, published_at, summary)

        assert hash1 == hash2 == hash3

    def test_hash_html_normalization(self):
        """Test that HTML differences don't affect hash."""
        link = "https://example.com/article"
        published_at = datetime(2023, 1, 15, 10, 0, 0, tzinfo=UTC)

        title1 = "Test Title"
        title2 = "<h1>Test Title</h1>"
        summary1 = "Test summary content"
        summary2 = "<p>Test <em>summary</em> content</p>"

        hash1 = content_hash.compute_content_hash(title1, link, published_at, summary1)
        hash2 = content_hash.compute_content_hash(title2, link, published_at, summary2)
        assert hash1 == hash2

    def test_hash_different_content_different_hash(self):
        """Test that genuinely different content produces different hashes."""
        link = "https://example.com/article"
        published_at = datetime(2023, 1, 15, 10, 0, 0, tzinfo=UTC)
        summary = "Test summary"

        hash1 = content_hash.compute_content_hash(
            "Title One", link, published_at, summary
        )
        hash2 = content_hash.compute_content_hash(
            "Title Two", link, published_at, summary
        )
        assert hash1 != hash2


class TestHashStability:
    """Test hash stability across different conditions."""

    def test_hash_unicode_normalization(self):
        """Test that Unicode normalization produces stable hashes."""
        link = "https://example.com/article"
        published_at = datetime(2023, 1, 15, 10, 0, 0, tzinfo=UTC)
        summary = "Test summary"

        # Composed vs decomposed Unicode characters
        title1 = "café"  # é as single character
        title2 = "cafe\u0301"  # e + combining acute accent

        hash1 = content_hash.compute_content_hash(title1, link, published_at, summary)
        hash2 = content_hash.compute_content_hash(title2, link, published_at, summary)
        assert hash1 == hash2

    def test_hash_timezone_normalization(self):
        """Test that timezone differences don't affect hash."""
        title = "Test Title"
        link = "https://example.com/article"
        summary = "Test summary"

        # Same moment in different timezones
        utc_time = datetime(2023, 1, 15, 10, 0, 0, tzinfo=UTC)
        # EST is UTC-5, so 5:00 EST = 10:00 UTC
        from datetime import timedelta, timezone

        est = timezone(timedelta(hours=-5))
        est_time = datetime(2023, 1, 15, 5, 0, 0, tzinfo=est)

        hash1 = content_hash.compute_content_hash(title, link, utc_time, summary)
        hash2 = content_hash.compute_content_hash(title, link, est_time, summary)
        assert hash1 == hash2


class TestContentHashValidation:
    """Test content hash validation."""

    def test_hash_format_validation(self):
        """Test that generated hashes are valid SHA256."""
        title = "Test Title"
        link = "https://example.com/article"
        published_at = datetime(2023, 1, 15, 10, 0, 0, tzinfo=UTC)
        summary = "Test summary"

        hash_result = content_hash.compute_content_hash(
            title, link, published_at, summary
        )

        # Should be 64-character hex string
        assert len(hash_result) == 64
        assert all(c in "0123456789abcdef" for c in hash_result)

    def test_hash_input_sanitization(self):
        """Test that hash inputs are properly sanitized."""
        # XSS and SQL injection attempts should be sanitized before hashing
        malicious_title = "<script>alert('xss')</script>Test Title"
        malicious_summary = "Summary; DELETE FROM articles; --"
        link = "https://example.com/article"
        published_at = datetime(2023, 1, 15, 10, 0, 0, tzinfo=UTC)

        # Should not throw exception and should produce valid hash
        hash_result = content_hash.compute_content_hash(
            malicious_title, link, published_at, malicious_summary
        )
        assert len(hash_result) == 64

    def test_hash_reproducibility_across_runs(self):
        """Test that hash generation is reproducible across multiple runs."""
        title = "Test Title"
        link = "https://example.com/article"
        published_at = datetime(2023, 1, 15, 10, 0, 0, tzinfo=UTC)
        summary = "Test summary"

        hashes = []
        for _ in range(10):
            hash_result = content_hash.compute_content_hash(
                title, link, published_at, summary
            )
            hashes.append(hash_result)

        # All hashes should be identical
        assert len(set(hashes)) == 1


class TestDeduplicationLogic:
    """Test deduplication logic and database interaction."""

    def test_duplicate_detection_by_hash(self):
        """Test that duplicate content is detected by hash."""
        # This test would require database setup and article creation
        # Implementation depends on actual database models
        pass

    def test_near_duplicate_handling(self):
        """Test handling of near-duplicate articles."""
        # Test with the near_duplicate_samples.xml fixture
        # Should result in only unique articles being stored
        pass

    def test_cross_source_deduplication(self):
        """Test that duplicates from different sources are deduplicated."""
        # source_id is not part of hash, so same article from different sources
        # should be deduplicated
        pass

    def test_idempotent_ingestion(self):
        """Test that re-ingesting same feed produces no new records."""
        # Integration test to verify idempotent behavior
        pass
