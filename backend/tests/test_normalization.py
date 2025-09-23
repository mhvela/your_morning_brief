"""Tests for content normalization functionality."""

from datetime import UTC, datetime

from app.processing import normalization


class TestTitleNormalization:
    """Test title normalization functionality."""

    def test_title_whitespace_normalization(self):
        """Test title whitespace trimming and collapsing."""
        assert normalization.normalize_title("  Title  ") == "Title"
        assert (
            normalization.normalize_title("Title\n\nwith\t\tspaces")
            == "Title with spaces"
        )
        assert (
            normalization.normalize_title("Multiple   internal   spaces")
            == "Multiple internal spaces"
        )

    def test_title_html_stripping(self):
        """Test HTML tag removal from titles."""
        assert normalization.normalize_title("<h1>Title</h1>") == "Title"
        assert (
            normalization.normalize_title("Title <em>with</em> tags")
            == "Title with tags"
        )
        assert (
            normalization.normalize_title("Title &amp; entities") == "Title & entities"
        )

    def test_title_case_preservation(self):
        """Test title case preservation for display."""
        result = normalization.normalize_title("Mixed Case Title")
        assert result == "Mixed Case Title"  # Original case preserved

    def test_title_lowercase_for_hash(self):
        """Test title lowercase conversion for hashing."""
        result = normalization.normalize_title_for_hash("Mixed Case Title")
        assert result == "mixed case title"

    def test_title_unicode_normalization(self):
        """Test Unicode NFKC normalization in titles."""
        # Decomposed vs composed characters should normalize the same
        title1 = "café"  # é as single character
        title2 = "cafe\u0301"  # e + combining acute accent
        assert normalization.normalize_title(title1) == normalization.normalize_title(
            title2
        )


class TestLinkCanonicalization:
    """Test URL canonicalization functionality."""

    def test_scheme_host_lowercasing(self):
        """Test scheme and host lowercasing."""
        url = "HTTPS://EXAMPLE.COM/Path"
        result = normalization.canonicalize_url(url)
        assert result.startswith("https://example.com/")

    def test_tracking_parameter_removal(self):
        """Test removal of tracking parameters."""
        url = (
            "https://example.com/article?utm_source=feed&utm_medium=rss&real_param=keep"
        )
        result = normalization.canonicalize_url(url)
        assert "utm_source" not in result
        assert "utm_medium" not in result
        assert "real_param=keep" in result

    def test_fragment_removal(self):
        """Test fragment removal."""
        url = "https://example.com/article#section1"
        result = normalization.canonicalize_url(url)
        assert "#section1" not in result

    def test_default_port_removal(self):
        """Test default port removal."""
        assert ":80" not in normalization.canonicalize_url("http://example.com:80/path")
        assert ":443" not in normalization.canonicalize_url(
            "https://example.com:443/path"
        )

    def test_query_param_sorting(self):
        """Test query parameter sorting for stability."""
        url = "https://example.com/path?z=1&a=2&b=3"
        result = normalization.canonicalize_url(url)
        # Parameters should be sorted alphabetically
        assert "a=2&b=3&z=1" in result

    def test_trailing_slash_normalization(self):
        """Test trailing slash removal."""
        url = "https://example.com/path/"
        result = normalization.canonicalize_url(url)
        assert not result.endswith("/")

    def test_url_basic_normalization(self):
        """Test basic URL normalization."""
        url = "https://example.com/path"
        result = normalization.canonicalize_url(url)
        assert result == "https://example.com/path"


class TestSummaryNormalization:
    """Test summary normalization functionality."""

    def test_html_tag_removal(self):
        """Test complete HTML tag removal."""
        html = "<p>Content <strong>with</strong> <em>tags</em></p>"
        result = normalization.normalize_summary(html)
        assert result == "Content with tags"

    def test_javascript_removal(self):
        """Test JavaScript content removal."""
        html = "<script>alert('xss')</script><p>Safe content</p>"
        result = normalization.normalize_summary(html)
        assert "alert" not in result
        assert "script" not in result
        assert "Safe content" in result

    def test_html_entity_decoding(self):
        """Test HTML entity decoding."""
        html = "Content &amp; entities &lt;test&gt; &quot;quotes&quot;"
        result = normalization.normalize_summary(html)
        assert "&amp;" not in result
        assert "&lt;" not in result
        assert "&quot;" not in result

    def test_whitespace_collapsing(self):
        """Test whitespace collapsing."""
        html = "<p>Content\n\nwith\t\tmultiple   spaces</p>"
        result = normalization.normalize_summary(html)
        assert result == "Content with multiple spaces"

    def test_length_limiting(self):
        """Test summary length limiting."""
        long_content = "x" * 5000
        result = normalization.normalize_summary(long_content)
        assert len(result) <= 4000

    def test_xss_payload_removal(self):
        """Test XSS payload complete removal."""
        xss_payloads = [
            "<script>alert('xss')</script>",
            "<img src=x onerror=alert(1)>",
            "javascript:alert(1)",
            "<iframe src='javascript:alert(1)'></iframe>",
        ]
        for payload in xss_payloads:
            result = normalization.normalize_summary(payload)
            # Result may be None if everything is removed
            if result:
                assert "alert" not in result
                assert "javascript" not in result
                assert "<" not in result
                assert ">" not in result


class TestAuthorNormalization:
    """Test author field normalization."""

    def test_author_whitespace_trimming(self):
        """Test author whitespace trimming."""
        assert normalization.normalize_author("  John Smith  ") == "John Smith"

    def test_author_none_handling(self):
        """Test None author handling."""
        assert normalization.normalize_author(None) is None
        assert normalization.normalize_author("") is None

    def test_author_html_stripping(self):
        """Test HTML removal from author."""
        assert (
            normalization.normalize_author("<strong>John Smith</strong>")
            == "John Smith"
        )


class TestTagsNormalization:
    """Test tags normalization functionality."""

    def test_tags_deduplication(self):
        """Test case-insensitive tag deduplication."""
        tags = ["AI", "ai", "Technology", "TECHNOLOGY", "ai"]
        result = normalization.normalize_tags(tags)
        assert len(result) == 2
        assert "AI" in result or "ai" in result
        assert "Technology" in result or "TECHNOLOGY" in result

    def test_tags_sorting(self):
        """Test tag sorting for stability."""
        tags = ["Zebra", "Apple", "Banana"]
        result = normalization.normalize_tags(tags)
        assert result == ["Apple", "Banana", "Zebra"]

    def test_tags_html_stripping(self):
        """Test HTML removal from tags."""
        tags = ["<em>AI</em>", "Technology"]
        result = normalization.normalize_tags(tags)
        assert "AI" in result
        assert "<em>" not in str(result)


class TestPublishedDateNormalization:
    """Test published date normalization."""

    def test_various_date_formats(self):
        """Test parsing various date formats."""
        dates = [
            "Mon, 15 Jan 2023 10:00:00 GMT",
            "2023-01-15T10:00:00Z",
            "2023-01-15 10:00:00",
            "January 15, 2023 10:00 AM",
        ]
        for date_str in dates:
            result = normalization.normalize_published_date(date_str)
            assert isinstance(result, datetime)
            assert result.tzinfo is not None

    def test_timezone_conversion_to_utc(self):
        """Test timezone conversion to UTC."""
        # EST timezone
        date_str = "Mon, 15 Jan 2023 10:00:00 -0500"
        result = normalization.normalize_published_date(date_str)
        assert result.tzinfo == UTC
        # Should be converted to UTC (15:00)
        assert result.hour == 15

    def test_missing_date_fallback(self):
        """Test fallback for missing dates."""
        result = normalization.normalize_published_date(None)
        assert isinstance(result, datetime)
        assert result.tzinfo == UTC

    def test_invalid_date_fallback(self):
        """Test fallback for invalid dates."""
        result = normalization.normalize_published_date("invalid date")
        assert isinstance(result, datetime)
        assert result.tzinfo == UTC


class TestSecurityValidation:
    """Test security validation in normalization."""

    def test_sql_injection_removal(self):
        """Test SQL injection attempt removal."""
        malicious_content = "Content; DELETE FROM articles; --"
        result = normalization.normalize_summary(malicious_content)
        assert "DELETE" not in result
        assert "--" not in result

    def test_suspicious_pattern_logging(self):
        """Test suspicious content pattern detection and logging."""
        # This test would verify that suspicious patterns are logged
        # Implementation would involve checking log output
        suspicious_content = "<script>document.location='http://evil.com'</script>"
        result = normalization.normalize_summary(suspicious_content)
        assert "script" not in result
        assert "document" not in result

    def test_content_length_dos_prevention(self):
        """Test DoS prevention through content length limits."""
        huge_content = "x" * 100000
        result = normalization.normalize_summary(huge_content)
        assert len(result) <= 4000
