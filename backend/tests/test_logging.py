import json
import logging

from app.core.logging import (
    StructuredFormatter,
    get_logger,
    get_request_id,
    set_request_id,
    setup_logging,
)


def test_structured_formatter() -> None:
    """Test that StructuredFormatter produces valid JSON logs."""
    formatter = StructuredFormatter(datefmt="%Y-%m-%dT%H:%M:%S")

    # Create a log record
    logger = logging.getLogger("test")
    record = logger.makeRecord(
        name="test",
        level=logging.INFO,
        fn="",
        lno=0,
        msg="Test message",
        args=(),
        exc_info=None,
    )

    # Format the record
    formatted = formatter.format(record)

    # Should be valid JSON
    log_data = json.loads(formatted)

    assert "timestamp" in log_data
    assert log_data["level"] == "INFO"
    assert log_data["message"] == "Test message"
    assert log_data["component"] == "test"


def test_request_id_context() -> None:
    """Test request ID context management."""
    # Initially should be empty
    assert get_request_id() == ""

    # Set a custom request ID
    request_id = set_request_id("test-123")
    assert request_id == "test-123"
    assert get_request_id() == "test-123"

    # Set auto-generated request ID
    auto_id = set_request_id()
    assert auto_id.startswith("req_")
    assert len(auto_id) == 12  # "req_" + 8 chars
    assert get_request_id() == auto_id


def test_get_logger() -> None:
    """Test that get_logger returns a proper logger instance."""
    logger = get_logger("test.module")

    assert isinstance(logger, logging.Logger)
    assert logger.name == "test.module"


def test_setup_logging() -> None:
    """Test that setup_logging configures logging correctly."""
    # Capture initial state
    root_logger = logging.getLogger()
    initial_handlers = root_logger.handlers[:]

    try:
        setup_logging()

        # Should have handlers configured
        assert len(root_logger.handlers) > 0

        # Should have structured formatter
        handler = root_logger.handlers[0]
        assert isinstance(handler.formatter, StructuredFormatter)

    finally:
        # Restore initial state
        for handler in root_logger.handlers[:]:
            root_logger.removeHandler(handler)
        for handler in initial_handlers:
            root_logger.addHandler(handler)
