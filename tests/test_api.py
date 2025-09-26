"""Tests for FastAPI application."""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
import pandas as pd
from pathlib import Path
import tempfile
import shutil
from app.main import app


@pytest.fixture
def client():
    """Create test client for FastAPI app."""
    return TestClient(app)


@pytest.fixture
def sample_clean_data():
    """Create sample clean data for testing."""
    return {
        "cleaned_orders.csv": pd.DataFrame({
            "order_id": [1, 2, 3],
            "user_id": [1, 1, 2],
            "eval_set": ["prior", "prior", "prior"],
            "order_number": [1, 2, 1],
            "order_dow": [2, 3, 1],
            "order_hour_of_day": [8, 10, 14],
            "days_since_prior_order": [None, 15.0, None]
        }),
        "cleaned_products.csv": pd.DataFrame({
            "product_id": [196, 10258, 14084],
            "product_name": ["Soda", "Dive Olives", "Pancake Mix"],
            "aisle_id": [77, 2, 130],
            "department_id": [7, 13, 13]
        })
    }


@pytest.fixture
def temp_data_dir(sample_clean_data):
    """Create temporary data directory with sample files."""
    temp_dir = tempfile.mkdtemp()
    clean_dir = Path(temp_dir) / "data" / "clean"
    clean_dir.mkdir(parents=True)
    
    # Save sample data
    for filename, df in sample_clean_data.items():
        df.to_csv(clean_dir / filename, index=False)
    
    yield clean_dir
    
    # Cleanup
    shutil.rmtree(temp_dir)


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


class TestSummaryEndpoint:
    """Test suite for summary endpoint."""
    
    @patch("app.main.CLEAN_DATA_DIR")
    @patch("app.main.load_cleaned_data")
    def test_summary_with_data(self, mock_load_data, mock_clean_dir, client, sample_clean_data):
        """Test summary endpoint with available data."""
        # Mock data loading
        def mock_load_side_effect(filename):
            return sample_clean_data.get(filename)
        
        mock_load_data.side_effect = mock_load_side_effect
        mock_clean_dir.exists.return_value = True
        mock_clean_dir.glob.return_value = []
        
        response = client.get("/summary")
        
        assert response.status_code == 200
        data = response.json()
        assert "files_processed" in data
        assert "total_records" in data
        assert "tables" in data
        assert "last_updated" in data
    
    def test_summary_no_data(self, client):
        """Test summary endpoint with no processed data."""
        response = client.get("/summary")
        
        assert response.status_code == 200
        data = response.json()
        assert data["files_processed"] == 0
        assert data["total_records"] == 0


class TestFilterEndpoint:
    """Test suite for filter endpoint."""
    
    @patch("app.main.load_cleaned_data")
    def test_filter_products_success(self, mock_load_data, client, sample_clean_data):
        """Test filtering products successfully."""
        mock_load_data.return_value = sample_clean_data["cleaned_products.csv"]
        
        response = client.get("/filter?table=products&limit=2")
        
        assert response.status_code == 200
        data = response.json()
        assert data["table"] == "products"
        assert data["total_rows"] <= 2
        assert "data" in data
    
    @patch("app.main.load_cleaned_data")
    def test_filter_orders_by_user(self, mock_load_data, client, sample_clean_data):
        """Test filtering orders by user ID."""
        mock_load_data.return_value = sample_clean_data["cleaned_orders.csv"]
        
        response = client.get("/filter?table=orders&user_id=1&limit=5")
        
        assert response.status_code == 200
        data = response.json()
        assert data["table"] == "orders"
        assert data["filters"]["user_id"] == 1
    
    def test_filter_invalid_table(self, client):
        """Test filtering with invalid table name."""
        response = client.get("/filter?table=invalid")
        
        assert response.status_code == 400
        data = response.json()
        assert "Invalid table" in data["detail"]
    
    @patch("app.main.load_cleaned_data")
    def test_filter_table_not_found(self, mock_load_data, client):
        """Test filtering when table file doesn't exist."""
        mock_load_data.return_value = None
        
        response = client.get("/filter?table=products")
        
        assert response.status_code == 404
        data = response.json()
        assert "not found" in data["detail"]


class TestValidationsEndpoint:
    """Test suite for validations endpoint."""
    
    @patch("app.main.load_cleaned_data")
    @patch("app.main.CLEAN_DATA_DIR")
    def test_validations_with_data(self, mock_clean_dir, mock_load_data, client, sample_clean_data):
        """Test validations endpoint with processed data."""
        # Mock file system
        mock_file = MagicMock()
        mock_file.stat.return_value.st_mtime = 1640995200  # 2022-01-01
        mock_clean_dir.__truediv__.return_value = mock_file
        
        # Mock data loading
        def mock_load_side_effect(filename):
            if filename in sample_clean_data:
                return sample_clean_data[filename]
            return None
        
        mock_load_data.side_effect = mock_load_side_effect
        
        response = client.get("/validations/last")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0
        
        # Check validation result structure
        validation = data[0]
        assert "file" in validation
        assert "status" in validation
        assert "timestamp" in validation
        assert "errors" in validation
        assert "warnings" in validation
    
    @patch("app.main.load_cleaned_data")
    def test_validations_missing_files(self, mock_load_data, client):
        """Test validations endpoint with missing files."""
        mock_load_data.return_value = None
        
        response = client.get("/validations/last")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        
        # All validations should show missing status
        for validation in data:
            assert validation["status"] == "missing"
            assert len(validation["errors"]) > 0


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
    
    def test_filter_endpoint_validation(self, client):
        """Test query parameter validation."""
        # Test invalid limit
        response = client.get("/filter?table=products&limit=0")
        assert response.status_code == 422
        
        # Test limit too high
        response = client.get("/filter?table=products&limit=2000")
        assert response.status_code == 422


class TestIntegrationScenarios:
    """Integration test scenarios."""
    
    @pytest.mark.integration
    def test_complete_api_flow(self, client):
        """Test complete API workflow."""
        # Health check
        health_response = client.get("/health")
        assert health_response.status_code == 200
        
        # Get summary (may be empty if no data processed)
        summary_response = client.get("/summary")
        assert summary_response.status_code == 200
        
        # Get validations (may show missing files)
        validation_response = client.get("/validations/last")
        assert validation_response.status_code == 200
        
        # Try filtering (may fail if no data, but should handle gracefully)
        filter_response = client.get("/filter?table=products&limit=1")
        assert filter_response.status_code in [200, 404]  # OK or not found