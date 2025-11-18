"""Test FastAPI application and routes"""

import pytest
import sys
from pathlib import Path
from fastapi.testclient import TestClient

# Add backend to path
backend_path = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_path))


@pytest.fixture
def client():
    """Create test client"""
    from app.main import app
    return TestClient(app)


class TestHealthCheck:
    """Test health check endpoints"""

    def test_health_check(self, client):
        """Test /health endpoint"""
        response = client.get("/health")
        assert response.status_code == 200

        data = response.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data
        assert "version" in data

    def test_root_endpoint(self, client):
        """Test root endpoint"""
        response = client.get("/")
        assert response.status_code == 200

        data = response.json()
        assert "message" in data
        assert "version" in data


class TestAPIRoutes:
    """Test API route structure"""

    def test_api_routes_exist(self, client):
        """Test that main API routes are registered"""
        from app.main import app

        # Get all routes
        routes = [route.path for route in app.routes if hasattr(route, 'path')]

        # Check critical routes exist
        assert "/health" in routes
        assert any("/api/v1/auth" in route for route in routes)
        assert any("/api/v1/documents" in route for route in routes)
        assert any("/api/v1/search" in route for route in routes)

    def test_openapi_schema(self, client):
        """Test OpenAPI schema generation"""
        response = client.get("/openapi.json")
        assert response.status_code == 200

        schema = response.json()
        assert "openapi" in schema
        assert "info" in schema
        assert "paths" in schema

        # Check API info
        assert schema["info"]["title"] == "Face Recognition & OCR System"
        assert schema["info"]["version"] == "1.0.0"


class TestAuthEndpoints:
    """Test authentication endpoints"""

    def test_login_endpoint_exists(self, client):
        """Test login endpoint is accessible"""
        # Should return 422 (validation error) for missing data, not 404
        response = client.post("/api/v1/auth/login")
        assert response.status_code in [422, 401]

    def test_register_endpoint_exists(self, client):
        """Test register endpoint is accessible"""
        # Should return 422 (validation error) for missing data, not 404
        response = client.post("/api/v1/auth/register")
        assert response.status_code in [422, 400]


class TestDocumentEndpoints:
    """Test document endpoints"""

    def test_upload_endpoint_exists(self, client):
        """Test document upload endpoint"""
        # Without authentication, should get 401 or 422
        response = client.post("/api/v1/documents/upload")
        assert response.status_code in [401, 422]

    def test_list_documents_endpoint(self, client):
        """Test document list endpoint"""
        # Without authentication, should get 401
        response = client.get("/api/v1/documents/")
        assert response.status_code == 401


class TestSearchEndpoints:
    """Test search endpoints"""

    def test_face_search_endpoint_exists(self, client):
        """Test face search endpoint"""
        # Without authentication, should get 401 or 422
        response = client.post("/api/v1/search/face")
        assert response.status_code in [401, 422]

    def test_text_search_endpoint_exists(self, client):
        """Test text search endpoint"""
        # Without authentication, should get 401 or 422
        response = client.post("/api/v1/search/text")
        assert response.status_code in [401, 422]


class TestCORS:
    """Test CORS configuration"""

    def test_cors_headers(self, client):
        """Test CORS headers are present"""
        response = client.options("/health",
                                 headers={"Origin": "http://localhost:3003"})

        # Should have CORS headers
        assert "access-control-allow-origin" in [h.lower() for h in response.headers.keys()]


class TestErrorHandling:
    """Test error handling"""

    def test_404_not_found(self, client):
        """Test 404 error handling"""
        response = client.get("/nonexistent-route")
        assert response.status_code == 404

    def test_validation_error(self, client):
        """Test validation error handling"""
        # Send invalid data to login
        response = client.post("/api/v1/auth/login",
                              json={"invalid": "data"})
        assert response.status_code == 422

        data = response.json()
        assert "detail" in data


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
