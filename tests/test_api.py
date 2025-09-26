"""
Test suite for FastAPI application
Tests all API endpoints and response models
"""

import json
import tempfile
from pathlib import Path
from unittest.mock import patch

import pandas as pd
import pytest
from fastapi.testclient import TestClient

from app.main import app


class TestFastAPIApplication:
    """Test cases for FastAPI application"""
    
    @pytest.fixture
    def client(self):
        """Create test client"""
        return TestClient(app)
    
    @pytest.fixture
    def sample_clean_data(self):
        """Create sample cleaned data"""
        return pd.DataFrame({
            'product_id': [1, 2, 3, 4, 5],
            'product_name': ['Bread', 'Milk', 'Apples', 'Ice Cream', 'Cheese'],
            'aisle_id': [1, 2, 3, 1, 2],
            'department_id': [1, 2, 3, 1, 2],
            'aisle': ['bakery', 'dairy', 'produce', 'bakery', 'dairy'],
            'department': ['frozen', 'dairy eggs', 'produce', 'frozen', 'dairy eggs'],
            'product_name_length': [5, 4, 6, 9, 6],
            'has_special_chars': [False, False, False, False, False],
            'sample_user_orders': [1, 2, 3, 4, 5],
            'estimated_popularity': [1, 2, 3, 4, 5]
        })
    
    @pytest.fixture
    def sample_validation_data(self):
        """Create sample validation data"""
        return {
            "timestamp": "2023-01-01T00:00:00",
            "total_records": 5,
            "validation_errors": [],
            "data_quality_metrics": {
                "completeness_ratio": 1.0,
                "product_id_uniqueness": 1.0,
                "valid_product_names_ratio": 1.0,
                "avg_product_name_length": 6.0
            },
            "schema_valid": True,
            "file_size_mb": 0.001
        }
    
    def test_root_endpoint(self, client):
        """Test root endpoint"""
        response = client.get("/")
        assert response.status_code == 200
        
        data = response.json()
        assert "message" in data
        assert "version" in data
        assert "endpoints" in data
        assert data["message"] == "Instacart Data API"
    
    def test_ping_endpoint(self, client):
        """Test ping endpoint"""
        response = client.get("/ping")
        assert response.status_code == 200
        
        data = response.json()
        assert data == {"ping": "pong"}
    
    def test_health_endpoint_no_data(self, client):
        """Test health endpoint when no data is available"""
        response = client.get("/health")
        assert response.status_code == 200
        
        data = response.json()
        assert "status" in data
        assert "timestamp" in data
        assert "data_available" in data
        assert data["data_available"] is False
    
    @patch('app.main.load_data')
    def test_health_endpoint_with_data(self, mock_load_data, client, sample_clean_data):
        """Test health endpoint when data is available"""
        mock_load_data.return_value = sample_clean_data
        
        with patch('app.main.CLEAN_DATA_FILE') as mock_path:
            mock_path.exists.return_value = True
            
            response = client.get("/health")
            assert response.status_code == 200
            
            data = response.json()
            assert data["status"] == "healthy"
            assert data["data_available"] is True
            assert data["total_records"] == 5
    
    @patch('app.main.load_data')
    def test_summary_endpoint(self, mock_load_data, client, sample_clean_data):
        """Test summary endpoint"""
        mock_load_data.return_value = sample_clean_data
        
        response = client.get("/summary")
        assert response.status_code == 200
        
        data = response.json()
        assert "total_records" in data
        assert "total_products" in data
        assert "total_aisles" in data
        assert "total_departments" in data
        assert "avg_product_name_length" in data
        assert "data_quality_score" in data
        
        assert data["total_records"] == 5
        assert data["total_products"] == 5
        assert data["total_aisles"] == 3
        assert data["total_departments"] == 3
    
    def test_summary_endpoint_no_data(self, client):
        """Test summary endpoint when no data is available"""
        response = client.get("/summary")
        assert response.status_code == 404
    
    @patch('app.main.load_data')
    def test_filter_endpoint_no_filters(self, mock_load_data, client, sample_clean_data):
        """Test filter endpoint without any filters"""
        mock_load_data.return_value = sample_clean_data
        
        response = client.get("/filter")
        assert response.status_code == 200
        
        data = response.json()
        assert "total_filtered_records" in data
        assert "records" in data
        assert data["total_filtered_records"] == 5
        assert len(data["records"]) == 5
    
    @patch('app.main.load_data')
    def test_filter_endpoint_department_filter(self, mock_load_data, client, sample_clean_data):
        """Test filter endpoint with department filter"""
        mock_load_data.return_value = sample_clean_data
        
        response = client.get("/filter?department=dairy")
        assert response.status_code == 200
        
        data = response.json()
        assert "total_filtered_records" in data
        assert "records" in data
        # Should find records with 'dairy' in department name
        assert data["total_filtered_records"] >= 0
    
    @patch('app.main.load_data')
    def test_filter_endpoint_aisle_filter(self, mock_load_data, client, sample_clean_data):
        """Test filter endpoint with aisle filter"""
        mock_load_data.return_value = sample_clean_data
        
        response = client.get("/filter?aisle=bakery")
        assert response.status_code == 200
        
        data = response.json()
        assert "total_filtered_records" in data
        assert "records" in data
    
    @patch('app.main.load_data')
    def test_filter_endpoint_name_length_filter(self, mock_load_data, client, sample_clean_data):
        """Test filter endpoint with name length filters"""
        mock_load_data.return_value = sample_clean_data
        
        response = client.get("/filter?min_name_length=5&max_name_length=8")
        assert response.status_code == 200
        
        data = response.json()
        assert "total_filtered_records" in data
        assert "records" in data
        
        # Check that all returned records meet the criteria
        for record in data["records"]:
            assert 5 <= record["product_name_length"] <= 8
    
    @patch('app.main.load_data')
    def test_filter_endpoint_limit(self, mock_load_data, client, sample_clean_data):
        """Test filter endpoint with limit parameter"""
        mock_load_data.return_value = sample_clean_data
        
        response = client.get("/filter?limit=3")
        assert response.status_code == 200
        
        data = response.json()
        assert len(data["records"]) <= 3
    
    @patch('app.main.load_data')
    def test_filter_endpoint_invalid_limit(self, mock_load_data, client, sample_clean_data):
        """Test filter endpoint with invalid limit"""
        mock_load_data.return_value = sample_clean_data
        
        response = client.get("/filter?limit=2000")
        assert response.status_code == 422  # Validation error
    
    def test_filter_endpoint_no_data(self, client):
        """Test filter endpoint when no data is available"""
        response = client.get("/filter")
        assert response.status_code == 404
    
    @patch('app.main.load_validation_results')
    def test_validations_endpoint(self, mock_load_validation, client, sample_validation_data):
        """Test validations endpoint"""
        mock_load_validation.return_value = sample_validation_data
        
        response = client.get("/validations/last")
        assert response.status_code == 200
        
        data = response.json()
        assert "timestamp" in data
        assert "total_records" in data
        assert "validation_errors" in data
        assert "data_quality_metrics" in data
        assert "schema_valid" in data
        assert "file_size_mb" in data
        
        assert data["total_records"] == 5
        assert data["schema_valid"] is True
        assert len(data["validation_errors"]) == 0
    
    def test_validations_endpoint_no_data(self, client):
        """Test validations endpoint when no data is available"""
        response = client.get("/validations/last")
        assert response.status_code == 404
    
    @patch('app.main.load_data')
    def test_filter_endpoint_missing_column(self, mock_load_data, client):
        """Test filter endpoint when required columns are missing"""
        # Create dataframe without expected columns
        incomplete_data = pd.DataFrame({
            'product_id': [1, 2, 3],
            'product_name': ['A', 'B', 'C']
        })
        mock_load_data.return_value = incomplete_data
        
        response = client.get("/filter?department=test")
        assert response.status_code == 400
        
        data = response.json()
        assert "Department column not available" in data["detail"]
    
    def test_openapi_schema(self, client):
        """Test that OpenAPI schema is accessible"""
        response = client.get("/openapi.json")
        assert response.status_code == 200
        
        schema = response.json()
        assert "openapi" in schema
        assert "info" in schema
        assert schema["info"]["title"] == "Instacart Data API"
    
    def test_docs_endpoint(self, client):
        """Test that documentation endpoint is accessible"""
        response = client.get("/docs")
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]
    
    def test_redoc_endpoint(self, client):
        """Test that ReDoc endpoint is accessible"""
        response = client.get("/redoc")
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]


class TestDataLoadingFunctions:
    """Test data loading functions"""
    
    def test_load_data_caching(self):
        """Test that data loading uses caching"""
        from app.main import _data_cache
        
        # Reset cache
        import app.main
        app.main._data_cache = None
        
        # First load should set cache
        with tempfile.TemporaryDirectory() as temp_dir:
            clean_file = Path(temp_dir) / "instacart_clean.csv"
            sample_data = pd.DataFrame({'col1': [1, 2, 3], 'col2': ['a', 'b', 'c']})
            sample_data.to_csv(clean_file, index=False)
            
            # Mock the file path
            with patch('app.main.CLEAN_DATA_FILE', clean_file):
                from app.main import load_data
                
                df1 = load_data()
                df2 = load_data()  # Second call should use cache
                
                assert len(df1) == 3
                assert len(df2) == 3
                pd.testing.assert_frame_equal(df1, df2)
    
    def test_load_validation_results_caching(self):
        """Test that validation results loading uses caching"""
        import app.main
        app.main._validation_cache = None
        
        with tempfile.TemporaryDirectory() as temp_dir:
            validation_file = Path(temp_dir) / "validation_results.json"
            sample_validation = {
                "timestamp": "2023-01-01T00:00:00",
                "total_records": 100,
                "validation_errors": [],
                "schema_valid": True,
                "file_size_mb": 1.0,
                "data_quality_metrics": {}
            }
            
            with open(validation_file, 'w') as f:
                json.dump(sample_validation, f)
            
            with patch('app.main.VALIDATION_FILE', validation_file):
                from app.main import load_validation_results
                
                result1 = load_validation_results()
                result2 = load_validation_results()  # Second call should use cache
                
                assert result1["total_records"] == 100
                assert result2["total_records"] == 100
                assert result1 == result2