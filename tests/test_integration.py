"""
Integration tests for the complete pipeline
Tests end-to-end functionality from ETL to API
"""

import json
import tempfile
from pathlib import Path

import pandas as pd
import pytest
from fastapi.testclient import TestClient

from app.main import app
from etl.clean import ETLPipeline


@pytest.mark.integration
class TestEndToEndPipeline:
    """End-to-end integration tests"""
    
    @pytest.fixture
    def sample_instacart_data(self):
        """Create realistic sample Instacart data"""
        # Aisles data
        aisles_data = pd.DataFrame({
            'aisle_id': [1, 2, 3, 4, 5],
            'aisle': ['fresh vegetables', 'fresh fruits', 'packaged vegetables fruits', 
                     'yogurt', 'packaged cheese']
        })
        
        # Departments data
        departments_data = pd.DataFrame({
            'department_id': [1, 2, 3, 4],
            'department': ['produce', 'dairy eggs', 'beverages', 'snacks']
        })
        
        # Products data
        products_data = pd.DataFrame({
            'product_id': [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
            'product_name': [
                'Banana', 'Organic Strawberries', 'Avocado', 'Greek Yogurt Plain',
                'Cheddar Cheese', 'Sparkling Water', 'Organic Carrots', 'Apples',
                'String Cheese', 'Orange Juice'
            ],
            'aisle_id': [2, 2, 1, 4, 5, 3, 1, 2, 5, 3],
            'department_id': [1, 1, 1, 2, 2, 3, 1, 1, 2, 3]
        })
        
        # Orders data (smaller sample)
        orders_data = pd.DataFrame({
            'order_id': list(range(1, 21)),
            'user_id': [1, 1, 2, 2, 3, 3, 4, 4, 5, 5, 6, 6, 7, 7, 8, 8, 9, 9, 10, 10],
            'order_number': [1, 2, 1, 2, 1, 2, 1, 2, 1, 2, 1, 2, 1, 2, 1, 2, 1, 2, 1, 2],
            'order_dow': [1, 2, 3, 4, 5, 6, 0, 1, 2, 3, 4, 5, 6, 0, 1, 2, 3, 4, 5, 6],
            'order_hour_of_day': [10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17],
            'days_since_prior_order': [None, 7, None, 14, None, 21, None, 7, None, 10, None, 5, None, 30, None, 3, None, 12, None, 8]
        })
        
        return {
            'aisles': aisles_data,
            'departments': departments_data,
            'products': products_data,
            'orders': orders_data
        }
    
    def test_complete_pipeline_flow(self, sample_instacart_data):
        """Test complete flow: ETL -> API endpoints"""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Setup directories
            raw_dir = Path(temp_dir) / 'raw'
            clean_dir = Path(temp_dir) / 'clean'
            raw_dir.mkdir()
            clean_dir.mkdir()
            
            # Create raw data files
            sample_instacart_data['aisles'].to_csv(raw_dir / 'aisles.csv', index=False)
            sample_instacart_data['departments'].to_csv(raw_dir / 'departments.csv', index=False)
            sample_instacart_data['products'].to_csv(raw_dir / 'products.csv', index=False)
            sample_instacart_data['orders'].to_csv(raw_dir / 'orders.csv', index=False)
            
            # Run ETL pipeline
            pipeline = ETLPipeline(str(raw_dir), str(clean_dir))
            success = pipeline.run()
            
            assert success is True
            assert (clean_dir / 'instacart_clean.csv').exists()
            assert (clean_dir / 'validation_results.json').exists()
            
            # Verify clean data
            clean_data = pd.read_csv(clean_dir / 'instacart_clean.csv')
            assert len(clean_data) == 10  # Same as products
            assert 'aisle' in clean_data.columns
            assert 'department' in clean_data.columns
            assert 'product_name_length' in clean_data.columns
            
            # Verify validation results
            with open(clean_dir / 'validation_results.json', 'r') as f:
                validation_data = json.load(f)
            
            assert validation_data['total_records'] == 10
            assert validation_data['schema_valid'] is True
            
            # Test API with the generated data
            client = TestClient(app)
            
            # Mock the file paths to point to our temp directory
            from app import main as app_main
            original_clean_file = app_main.CLEAN_DATA_FILE
            original_validation_file = app_main.VALIDATION_FILE
            
            try:
                app_main.CLEAN_DATA_FILE = clean_dir / 'instacart_clean.csv'
                app_main.VALIDATION_FILE = clean_dir / 'validation_results.json'
                
                # Reset cache to force reload
                app_main._data_cache = None
                app_main._validation_cache = None
                
                # Test health endpoint
                response = client.get("/health")
                assert response.status_code == 200
                health_data = response.json()
                assert health_data["data_available"] is True
                assert health_data["total_records"] == 10
                
                # Test summary endpoint
                response = client.get("/summary")
                assert response.status_code == 200
                summary_data = response.json()
                assert summary_data["total_records"] == 10
                assert summary_data["total_products"] == 10
                assert summary_data["total_aisles"] == 5
                assert summary_data["total_departments"] == 3  # Only departments referenced in products
                
                # Test filter endpoint
                response = client.get("/filter?department=produce")
                assert response.status_code == 200
                filter_data = response.json()
                assert "records" in filter_data
                
                # Test validations endpoint
                response = client.get("/validations/last")
                assert response.status_code == 200
                validation_response = response.json()
                assert validation_response["total_records"] == 10
                assert validation_response["schema_valid"] is True
                
            finally:
                # Restore original file paths
                app_main.CLEAN_DATA_FILE = original_clean_file
                app_main.VALIDATION_FILE = original_validation_file
                app_main._data_cache = None
                app_main._validation_cache = None
    
    def test_pipeline_with_data_quality_issues(self):
        """Test pipeline behavior with data quality issues"""
        with tempfile.TemporaryDirectory() as temp_dir:
            raw_dir = Path(temp_dir) / 'raw'
            clean_dir = Path(temp_dir) / 'clean'
            raw_dir.mkdir()
            clean_dir.mkdir()
            
            # Create data with quality issues
            # Missing values, inconsistent data types, etc.
            aisles_data = pd.DataFrame({
                'aisle_id': [1, 2, None],  # Missing value
                'aisle': ['bakery', 'dairy', 'produce']
            })
            
            departments_data = pd.DataFrame({
                'department_id': [1, 2, 3],
                'department': ['frozen', None, 'produce']  # Missing value
            })
            
            products_data = pd.DataFrame({
                'product_id': [1, 2, 3],
                'product_name': ['Bread', '', 'Apples'],  # Empty string
                'aisle_id': [1, 2, 3],
                'department_id': [1, 2, 3]
            })
            
            orders_data = pd.DataFrame({
                'order_id': [1, 2, 3],
                'user_id': [1, 2, 3],
                'order_number': [1, 1, 1],
                'order_dow': [1, 2, 3],
                'order_hour_of_day': [10, 11, 12],
                'days_since_prior_order': [None, 7, 14]
            })
            
            # Save data files
            aisles_data.to_csv(raw_dir / 'aisles.csv', index=False)
            departments_data.to_csv(raw_dir / 'departments.csv', index=False)
            products_data.to_csv(raw_dir / 'products.csv', index=False)
            orders_data.to_csv(raw_dir / 'orders.csv', index=False)
            
            # Run ETL pipeline
            pipeline = ETLPipeline(str(raw_dir), str(clean_dir))
            success = pipeline.run()
            
            # Pipeline should complete but with validation errors
            assert (clean_dir / 'instacart_clean.csv').exists()
            assert (clean_dir / 'validation_results.json').exists()
            
            # Check validation results contain errors
            with open(clean_dir / 'validation_results.json', 'r') as f:
                validation_data = json.load(f)
            
            # Should have validation errors due to missing values
            assert len(validation_data['validation_errors']) > 0
            assert validation_data['schema_valid'] is False
    
    @pytest.mark.slow
    def test_api_performance_with_large_dataset(self):
        """Test API performance with larger dataset"""
        with tempfile.TemporaryDirectory() as temp_dir:
            clean_dir = Path(temp_dir)
            
            # Generate larger dataset (1000 records)
            large_data = pd.DataFrame({
                'product_id': range(1000),
                'product_name': [f'Product {i}' for i in range(1000)],
                'aisle_id': [i % 50 + 1 for i in range(1000)],
                'department_id': [i % 20 + 1 for i in range(1000)],
                'aisle': [f'Aisle {i % 50 + 1}' for i in range(1000)],
                'department': [f'Department {i % 20 + 1}' for i in range(1000)],
                'product_name_length': [9 + (i % 10) for i in range(1000)],
                'has_special_chars': [i % 2 == 0 for i in range(1000)],
                'sample_user_orders': [i % 20 + 1 for i in range(1000)],
                'estimated_popularity': [i % 100 for i in range(1000)]
            })
            
            # Save dataset
            clean_file = clean_dir / 'instacart_clean.csv'
            large_data.to_csv(clean_file, index=False)
            
            # Create validation file
            validation_data = {
                "timestamp": "2023-01-01T00:00:00",
                "total_records": 1000,
                "validation_errors": [],
                "data_quality_metrics": {"completeness_ratio": 1.0},
                "schema_valid": True,
                "file_size_mb": 0.1
            }
            
            validation_file = clean_dir / 'validation_results.json'
            with open(validation_file, 'w') as f:
                json.dump(validation_data, f)
            
            # Test API performance
            client = TestClient(app)
            
            from app import main as app_main
            original_clean_file = app_main.CLEAN_DATA_FILE
            original_validation_file = app_main.VALIDATION_FILE
            
            try:
                app_main.CLEAN_DATA_FILE = clean_file
                app_main.VALIDATION_FILE = validation_file
                app_main._data_cache = None
                app_main._validation_cache = None
                
                # Test summary endpoint with large dataset
                import time
                start_time = time.time()
                response = client.get("/summary")
                end_time = time.time()
                
                assert response.status_code == 200
                assert end_time - start_time < 2.0  # Should complete within 2 seconds
                
                summary_data = response.json()
                assert summary_data["total_records"] == 1000
                
                # Test filtering with large dataset
                start_time = time.time()
                response = client.get("/filter?limit=50")
                end_time = time.time()
                
                assert response.status_code == 200
                assert end_time - start_time < 1.0  # Should complete within 1 second
                
                filter_data = response.json()
                assert len(filter_data["records"]) == 50
                
            finally:
                app_main.CLEAN_DATA_FILE = original_clean_file
                app_main.VALIDATION_FILE = original_validation_file
                app_main._data_cache = None
                app_main._validation_cache = None