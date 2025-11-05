"""
Test suite for CEO Discovery REST API endpoints.

This test ensures the API endpoints correctly expose
CEO Discovery data through the FastAPI server.
"""
import pytest
from fastapi.testclient import TestClient


def test_api_imports():
    """Test that server module can be imported"""
    try:
        from dashboard.server import app
        assert app is not None
    except ImportError:
        pytest.fail("Failed to import server app")


def test_ceo_status_endpoint():
    """Test CEO Discovery status endpoint"""
    from dashboard.server import app

    client = TestClient(app)
    response = client.get("/api/ceo/status")

    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "session_id" in data or data["status"] == "idle"
    assert "patterns" in data
    assert "proposals" in data


def test_ceo_proposals_endpoint():
    """Test proposals endpoint with filtering"""
    from dashboard.server import app

    client = TestClient(app)
    response = client.get("/api/ceo/proposals?min_roi=3.0&limit=5")

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


def test_ceo_proposals_default_params():
    """Test proposals endpoint with default parameters"""
    from dashboard.server import app

    client = TestClient(app)
    response = client.get("/api/ceo/proposals")

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


def test_ceo_patterns_endpoint():
    """Test patterns endpoint with type filter"""
    from dashboard.server import app

    client = TestClient(app)
    response = client.get("/api/ceo/patterns?type=repetitive")

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


def test_ceo_patterns_no_filter():
    """Test patterns endpoint without filter"""
    from dashboard.server import app

    client = TestClient(app)
    response = client.get("/api/ceo/patterns")

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


def test_ceo_history_endpoint():
    """Test history endpoint"""
    from dashboard.server import app

    client = TestClient(app)
    response = client.get("/api/ceo/history?limit=5")

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


def test_ceo_pain_points_endpoint():
    """Test pain points endpoint"""
    from dashboard.server import app

    client = TestClient(app)
    response = client.get("/api/ceo/pain-points")

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
