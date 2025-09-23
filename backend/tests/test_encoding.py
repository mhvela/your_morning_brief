"""Tests for character encoding detection and normalization."""

import pytest

from app.processing import encoding


class TestEncodingDetection:
    """Test character encoding detection functionality."""

    def test_detect_utf8_encoding(self):
        """Test UTF-8 encoding detection."""
        # Use longer content to improve detection accuracy
        content = (
            "Test UTF-8 content with unicode characters: café naïve résumé 🤖 " * 10
        )
        result = encoding.detect_encoding(content.encode("utf-8"))
        assert result.encoding.lower() in ["utf-8", "ascii"]  # ASCII is subset of UTF-8
        assert result.confidence >= 0.8

    def test_detect_iso8859_encoding(self):
        """Test ISO-8859-1 encoding detection."""
        # Use content with specific ISO-8859-1 characters
        content = "Test ISO content: café naïve résumé " * 20
        result = encoding.detect_encoding(content.encode("iso-8859-1"))
        assert result.encoding.lower() in [
            "iso-8859-1",
            "windows-1252",
        ]  # Windows-1252 is superset
        assert result.confidence >= 0.8

    def test_detect_windows1252_encoding(self):
        """Test Windows-1252 encoding detection."""
        content = "Test Windows content with 'smart quotes'"
        result = encoding.detect_encoding(content.encode("windows-1252"))
        assert result.encoding == "windows-1252"
        assert result.confidence >= 0.8

    def test_validate_allowed_encoding(self):
        """Test encoding validation against whitelist."""
        assert encoding.is_encoding_allowed("utf-8") is True
        assert encoding.is_encoding_allowed("iso-8859-1") is True
        assert encoding.is_encoding_allowed("windows-1252") is True
        assert encoding.is_encoding_allowed("ascii") is True
        assert encoding.is_encoding_allowed("utf-16") is True
        assert encoding.is_encoding_allowed("big5") is False
        assert encoding.is_encoding_allowed("shift_jis") is False

    def test_confidence_threshold_validation(self):
        """Test encoding confidence threshold validation."""
        # Low confidence should be rejected
        assert encoding.is_confidence_acceptable(0.5) is False
        assert encoding.is_confidence_acceptable(0.79) is False
        # High confidence should be accepted
        assert encoding.is_confidence_acceptable(0.8) is True
        assert encoding.is_confidence_acceptable(0.95) is True

    def test_sample_size_limit(self):
        """Test encoding detection sample size limiting."""
        large_content = b"x" * 20480  # 20KB
        result = encoding.detect_encoding(large_content)
        # Should only analyze first 10KB
        assert len(result.sample_analyzed) <= 10240

    def test_encoding_normalization_utf8_fallback(self):
        """Test fallback to UTF-8 with replace error handling."""
        invalid_bytes = b"\xff\xfe\x00\x00invalid"
        result = encoding.normalize_content(invalid_bytes)
        assert isinstance(result, str)
        # Should contain replacement characters for invalid bytes
        assert "�" in result or result == "invalid"

    def test_unicode_nfkc_normalization(self):
        """Test Unicode NFKC normalization."""
        # Composed vs decomposed characters
        text = "café"  # é as single character
        decomposed = "cafe\u0301"  # e + combining acute accent
        assert encoding.normalize_unicode(text) == encoding.normalize_unicode(
            decomposed
        )

    def test_security_reject_disallowed_encoding(self):
        """Test security: reject disallowed encodings."""
        with pytest.raises(ValueError, match="not allowed"):
            encoding.validate_encoding_security("big5", 0.9)

    def test_security_reject_low_confidence(self):
        """Test security: reject low confidence detection."""
        with pytest.raises(ValueError, match="confidence too low"):
            encoding.validate_encoding_security("utf-8", 0.5)


class TestEncodingSecurityValidation:
    """Test encoding security validation."""

    def test_malformed_encoding_attack_handling(self):
        """Test handling of malformed encoding attacks."""
        malformed_bytes = b"\x80\x81\x82\x83"
        result = encoding.normalize_content(malformed_bytes)
        # Should handle gracefully without throwing exceptions
        assert isinstance(result, str)

    def test_dos_prevention_sample_size(self):
        """Test DoS prevention through sample size limiting."""
        huge_content = b"a" * (1024 * 1024)  # 1MB
        result = encoding.detect_encoding(huge_content)
        # Should process only limited sample
        assert len(result.sample_analyzed) <= 10240
