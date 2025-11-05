"""
Test suite for FastAPI server base functionality.

This test ensures the server starts correctly and provides
a health check endpoint for monitoring.
"""
import pytest
from fastapi.testclient import TestClient


def test_server_imports():
    """Test that server module can be imported."""
    try:
        from dashboard.server import app
        assert app is not None
    except ImportError:
        pytest.fail("Failed to import server module")


def test_health_check_endpoint():
    """Test health check endpoint returns correct status."""
    from dashboard.server import app

    client = TestClient(app)
    response = client.get("/api/status")

    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert data["status"] == "operational"
    assert "service" in data
    assert data["service"] == "ceo-discovery-dashboard"


def test_cors_enabled():
    """Test CORS is properly configured."""
    from dashboard.server import app

    client = TestClient(app)
    response = client.options(
        "/api/status",
        headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "GET"
        }
    )

    assert response.status_code == 200
    assert "access-control-allow-origin" in response.headers


def test_root_endpoint():
    """Test root endpoint provides service info."""
    from dashboard.server import app

    client = TestClient(app)
    response = client.get("/")

    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert "version" in data
