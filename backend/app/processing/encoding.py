"""Character encoding detection and normalization functionality."""

import unicodedata
from dataclasses import dataclass

import chardet

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


@dataclass
class EncodingResult:
    """Result of encoding detection."""

    encoding: str
    confidence: float
    sample_analyzed: bytes


def detect_encoding(content: bytes) -> EncodingResult:
    """
    Detect character encoding with security constraints.

    Args:
        content: Raw bytes to analyze

    Returns:
        EncodingResult with detected encoding and confidence

    Raises:
        ValueError: If encoding detection fails or is not allowed
    """
    # Limit sample size to prevent DoS
    sample = content[: settings.encoding_sample_size]

    # Use chardet for encoding detection
    detection = chardet.detect(sample)

    if not detection or not detection.get("encoding"):
        raise ValueError("Could not detect encoding")

    encoding_raw = detection["encoding"]
    if not encoding_raw:
        raise ValueError("Could not detect encoding")

    encoding = encoding_raw.lower()
    confidence = detection.get("confidence", 0.0)

    # Validate encoding and confidence
    validate_encoding_security(encoding, confidence)

    return EncodingResult(
        encoding=encoding, confidence=confidence, sample_analyzed=sample
    )


def is_encoding_allowed(encoding: str) -> bool:
    """
    Check if encoding is in the allowed whitelist.

    Args:
        encoding: Encoding name to check

    Returns:
        True if encoding is allowed, False otherwise
    """
    return encoding.lower() in [enc.lower() for enc in settings.allowed_encodings]


def is_confidence_acceptable(confidence: float) -> bool:
    """
    Check if encoding detection confidence meets minimum threshold.

    Args:
        confidence: Confidence score (0.0 to 1.0)

    Returns:
        True if confidence is acceptable, False otherwise
    """
    return confidence >= settings.encoding_confidence_min


def validate_encoding_security(encoding: str, confidence: float) -> None:
    """
    Validate encoding detection meets security requirements.

    Args:
        encoding: Detected encoding
        confidence: Detection confidence

    Raises:
        ValueError: If encoding is not allowed or confidence too low
    """
    if not is_encoding_allowed(encoding):
        logger.warning(
            "Disallowed encoding detected",
            extra={"encoding": encoding, "confidence": confidence},
        )
        raise ValueError(f"Encoding '{encoding}' is not allowed")

    if not is_confidence_acceptable(confidence):
        logger.warning(
            "Low confidence encoding detection",
            extra={"encoding": encoding, "confidence": confidence},
        )
        raise ValueError(f"Encoding detection confidence {confidence} too low")


def normalize_content(content: bytes) -> str:
    """
    Normalize byte content to string with fallback handling.

    Args:
        content: Raw bytes to normalize

    Returns:
        Normalized string content
    """
    try:
        # Try to detect encoding first
        result = detect_encoding(content)
        return content.decode(result.encoding)
    except (ValueError, UnicodeDecodeError) as e:
        logger.warning(
            "Encoding detection/decode failed, using UTF-8 fallback",
            extra={"error": str(e)},
        )
        # Fallback to UTF-8 with replace error handling
        return content.decode("utf-8", errors="replace")


def normalize_unicode(text: str) -> str:
    """
    Normalize Unicode text using NFKC normalization.

    Args:
        text: Text to normalize

    Returns:
        NFKC normalized text
    """
    return unicodedata.normalize("NFKC", text)
