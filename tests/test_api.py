"""Tests for FastAPI application."""

import pytest
from fastapi.testclient import TestClient
from app.main import app


@pytest.fixture
def client():
    """Create test client for FastAPI app."""
    return TestClient(app)


class TestHealthEndpoint:
    """Test suite for health check endpoint."""
    
    def test_health_check_returns_ok(self, client):
        """Test that health endpoint returns OK status."""
        response = client.get("/health")
        
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}
    
    def test_health_check_response_structure(self, client):
        """Test health endpoint response structure."""
        response = client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)
        assert "status" in data
        assert isinstance(data["status"], str)


class TestRootEndpoint:
    """Test suite for root endpoint."""
    
    def test_root_endpoint(self, client):
        """Test root endpoint returns welcome message."""
        response = client.get("/")
        
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "CSV Clean API" in data["message"]


class TestAPIDocumentation:
    """Test suite for API documentation endpoints."""
    
    def test_openapi_docs_accessible(self, client):
        """Test that OpenAPI docs are accessible."""
        response = client.get("/docs")
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]
    
    def test_redoc_docs_accessible(self, client):
        """Test that ReDoc documentation is accessible."""
        response = client.get("/redoc")
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]
    
    def test_openapi_json_schema(self, client):
        """Test that OpenAPI JSON schema is available."""
        response = client.get("/openapi.json")
        assert response.status_code == 200
        
        schema = response.json()
        assert "openapi" in schema
        assert "info" in schema
        assert schema["info"]["title"] == "CSV Clean API"


class TestErrorHandling:
    """Test suite for error handling."""
    
    def test_nonexistent_endpoint_returns_404(self, client):
        """Test that nonexistent endpoints return 404."""
        response = client.get("/nonexistent")
        assert response.status_code == 404
    
    def test_wrong_method_returns_405(self, client):
        """Test that wrong HTTP methods return 405."""
        response = client.post("/health")
        assert response.status_code == 405


class TestCORS:
    """Test suite for CORS handling (if needed)."""
    
    def test_cors_headers_present(self, client):
        """Test CORS headers if configured."""
        response = client.get("/health")
        
        # This test would be more relevant if CORS is configured
        # For now, just ensure the request succeeds
        assert response.status_code == 200