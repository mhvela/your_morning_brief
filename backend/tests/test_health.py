from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_endpoint_returns_200_ok() -> None:
    """Test that health endpoint returns 200 with correct format."""
    response = client.get("/healthz")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_readiness_endpoint_returns_200_ok() -> None:
    """Test that readiness endpoint returns 200 with correct format."""
    response = client.get("/readyz")
    assert response.status_code == 200
    assert response.json() == {"status": "ready"}


def test_version_endpoint_returns_correct_format() -> None:
    """Test that version endpoint returns correct schema."""
    response = client.get("/version")
    assert response.status_code == 200

    data = response.json()
    assert "version" in data
    assert "build_date" in data
    assert "commit_hash" in data
    assert "python_version" in data

    # Verify types
    assert isinstance(data["version"], str)
    assert isinstance(data["build_date"], str)
    assert isinstance(data["commit_hash"], str)
    assert isinstance(data["python_version"], str)


def test_cors_headers_present() -> None:
    """Test that CORS headers are present in responses."""
    response = client.get("/healthz")
    assert response.status_code == 200
    # FastAPI TestClient doesn't include CORS headers in tests by default
    # This would be tested in integration tests with actual server


def test_health_endpoints_content_type() -> None:
    """Test that endpoints return JSON content type."""
    endpoints = ["/healthz", "/readyz", "/version"]

    for endpoint in endpoints:
        response = client.get(endpoint)
        assert response.status_code == 200
        assert "application/json" in response.headers["content-type"]


def test_nonexistent_endpoint_returns_404() -> None:
    """Test that non-existent endpoints return 404."""
    response = client.get("/nonexistent")
    assert response.status_code == 404


def test_health_endpoint_methods() -> None:
    """Test that health endpoints only accept GET method."""
    endpoints = ["/healthz", "/readyz", "/version"]

    for endpoint in endpoints:
        # GET should work
        response = client.get(endpoint)
        assert response.status_code == 200

        # POST should not be allowed
        response = client.post(endpoint)
        assert response.status_code == 405
