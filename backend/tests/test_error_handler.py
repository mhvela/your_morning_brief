from unittest.mock import AsyncMock, patch

import pytest
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.testclient import TestClient

from app.middleware.error_handler import (
    ErrorResponse,
    global_exception_handler,
    setup_error_handling,
)


def test_error_response_model() -> None:
    """Test ErrorResponse model structure."""
    error_data = {
        "code": "TEST_ERROR",
        "message": "Test error message",
        "request_id": "req_123",
    }

    response = ErrorResponse(error=error_data)
    assert response.error == error_data


@pytest.mark.asyncio
async def test_global_exception_handler() -> None:
    """Test global exception handler returns proper error response."""
    # Mock request
    request = AsyncMock(spec=Request)
    request.method = "GET"
    request.url.path = "/test"

    # Mock exception
    test_exception = Exception("Test error")

    with patch("app.middleware.error_handler.get_request_id", return_value="req_123"):
        response = await global_exception_handler(request, test_exception)

    assert isinstance(response, JSONResponse)
    assert response.status_code == 500

    # Check response content
    body = response.body
    content = body.decode() if isinstance(body, bytes) else bytes(body).decode()
    assert "INTERNAL_ERROR" in content
    assert "req_123" in content
    assert "An unexpected error occurred" in content


def test_setup_error_handling() -> None:
    """Test that error handling is properly configured on FastAPI app."""
    app = FastAPI()

    # Should start with no middleware
    initial_middleware_count = len(app.user_middleware)

    setup_error_handling(app)

    # Should have added middleware
    assert len(app.user_middleware) > initial_middleware_count


def test_error_handling_with_main_app() -> None:
    """Test that error handling works with the main application."""
    from app.main import app

    client = TestClient(app)

    # Test with a non-existent endpoint that will trigger a 404
    # This verifies our middleware is working without causing exceptions
    response = client.get("/nonexistent-endpoint")
    assert response.status_code == 404
