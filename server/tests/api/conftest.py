import pytest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock

# Simple mock app for API testing
from fastapi import FastAPI

# Create a mock app for testing
@pytest.fixture
def mock_app():
    """Create a mock FastAPI app for API testing"""
    app = FastAPI()

    # Simple health check endpoint for testing
    @app.get("/health")
    async def health_check():
        return {"status": "ok"}

    return app

@pytest.fixture
def client(mock_app):
    """Create FastAPI test client with mock app"""
    return TestClient(mock_app)

# Mock environment variables for API tests
@pytest.fixture(autouse=True)
def mock_environment(monkeypatch):
    """Mock environment variables for all API tests."""
    monkeypatch.setenv("DATABASE_URL", "sqlite+aiosqlite:///:memory:")
    monkeypatch.setenv("UPLOAD_DIR", "/tmp/test_uploads")
    monkeypatch.setenv("OPENAI_API_KEY", "test-api-key")
    monkeypatch.setenv("LOG_LEVEL", "WARNING")