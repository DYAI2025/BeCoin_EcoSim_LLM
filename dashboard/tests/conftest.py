"""
Pytest configuration for dashboard tests.

This module provides fixtures and configuration for testing the dashboard
without authentication requirements.
"""

import os
import pytest
from fastapi.testclient import TestClient


@pytest.fixture(scope="session", autouse=True)
def disable_auth():
    """
    Automatically disable authentication for all tests.

    This fixture runs once per test session and ensures that
    AUTH_USERNAME and AUTH_PASSWORD are cleared, allowing tests
    to run without authentication requirements.
    """
    # Store original values
    original_username = os.environ.get("AUTH_USERNAME")
    original_password = os.environ.get("AUTH_PASSWORD")

    # Clear auth environment variables BEFORE any imports
    os.environ.pop("AUTH_USERNAME", None)
    os.environ.pop("AUTH_PASSWORD", None)

    yield

    # Restore original values if they existed
    if original_username is not None:
        os.environ["AUTH_USERNAME"] = original_username
    if original_password is not None:
        os.environ["AUTH_PASSWORD"] = original_password


@pytest.fixture
def client():
    """
    Provide a TestClient instance for testing the FastAPI application.
    """
    from dashboard.server import app

    return TestClient(app)
