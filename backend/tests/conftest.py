"""Test configuration and fixtures."""

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client():
    """Create test client."""
    from main import create_app

    app = create_app()
    return TestClient(app)
