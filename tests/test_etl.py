"""
Test suite for ETL pipeline
Tests data loading, merging, validation, and output generation
"""

import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch

import pandas as pd
import pytest

from etl.clean import ETLPipeline, ValidationResult


class TestETLPipeline:
    """Test cases for ETL Pipeline"""
    
    @pytest.fixture
    def sample_data(self):
        """Create sample data for testing"""
        # Sample aisles data
        aisles_data = pd.DataFrame({
            'aisle_id': [1, 2, 3],
            'aisle': ['bakery', 'dairy', 'produce']
        })
        
        # Sample departments data
        departments_data = pd.DataFrame({
            'department_id': [1, 2, 3],
            'department': ['frozen', 'dairy eggs', 'produce']
        })
        
        # Sample products data
        products_data = pd.DataFrame({
            'product_id': [1, 2, 3, 4, 5],
            'product_name': ['Bread', 'Milk', 'Apples', 'Ice Cream', 'Cheese'],
            'aisle_id': [1, 2, 3, 1, 2],
            'department_id': [1, 2, 3, 1, 2]
        })
        
        # Sample orders data
        orders_data = pd.DataFrame({
            'order_id': [1, 2, 3, 4, 5],
            'user_id': [1, 1, 2, 2, 3],
            'order_number': [1, 2, 1, 2, 1],
            'order_dow': [1, 2, 3, 4, 5],
            'order_hour_of_day': [10, 11, 12, 13, 14],
            'days_since_prior_order': [None, 7, None, 14, None]
        })
        
        return {
            'aisles': aisles_data,
            'departments': departments_data,
            'products': products_data,
            'orders': orders_data
        }
    
    @pytest.fixture
    def temp_directories(self):
        """Create temporary directories for testing"""
        with tempfile.TemporaryDirectory() as temp_dir:
            raw_dir = Path(temp_dir) / 'raw'
            clean_dir = Path(temp_dir) / 'clean'
            raw_dir.mkdir()
            clean_dir.mkdir()
            
            yield {
                'raw': str(raw_dir),
                'clean': str(clean_dir)
            }
    
    def test_etl_initialization(self, temp_directories):
        """Test ETL pipeline initialization"""
        pipeline = ETLPipeline(
            raw_data_path=temp_directories['raw'],
            clean_data_path=temp_directories['clean']
        )
        
        assert pipeline.raw_data_path == Path(temp_directories['raw'])
        assert pipeline.clean_data_path == Path(temp_directories['clean'])
        assert pipeline.validation_result is None
    
    def test_load_raw_data_success(self, temp_directories, sample_data):
        """Test successful loading of raw data"""
        # Create sample CSV files
        raw_dir = Path(temp_directories['raw'])
        sample_data['aisles'].to_csv(raw_dir / 'aisles.csv', index=False)
        sample_data['departments'].to_csv(raw_dir / 'departments.csv', index=False)
        sample_data['products'].to_csv(raw_dir / 'products.csv', index=False)
        sample_data['orders'].to_csv(raw_dir / 'orders.csv', index=False)
        
        pipeline = ETLPipeline(
            raw_data_path=temp_directories['raw'],
            clean_data_path=temp_directories['clean']
        )
        
        aisles_df, departments_df, products_df, orders_df = pipeline.load_raw_data()
        
        assert len(aisles_df) == 3
        assert len(departments_df) == 3
        assert len(products_df) == 5
        assert len(orders_df) == 5
        assert 'aisle_id' in aisles_df.columns
        assert 'department_id' in departments_df.columns
    
    def test_load_raw_data_missing_file(self, temp_directories):
        """Test loading raw data with missing files"""
        pipeline = ETLPipeline(
            raw_data_path=temp_directories['raw'],
            clean_data_path=temp_directories['clean']
        )
        
        with pytest.raises(Exception):
            pipeline.load_raw_data()
    
    def test_merge_data(self, temp_directories, sample_data):
        """Test data merging functionality"""
        pipeline = ETLPipeline(
            raw_data_path=temp_directories['raw'],
            clean_data_path=temp_directories['clean']
        )
        
        merged_df = pipeline.merge_data(
            sample_data['aisles'],
            sample_data['departments'], 
            sample_data['products'],
            sample_data['orders']
        )
        
        # Check merged data structure
        assert len(merged_df) == 5  # Same as products
        assert 'aisle' in merged_df.columns
        assert 'department' in merged_df.columns
        assert 'product_name_length' in merged_df.columns
        assert 'has_special_chars' in merged_df.columns
        
        # Check data integrity
        assert merged_df['product_name_length'].iloc[0] == len('Bread')
        assert merged_df['aisle'].iloc[0] == 'bakery'  # product_id 1 -> aisle_id 1 -> bakery
    
    def test_validate_schema_success(self, temp_directories, sample_data):
        """Test schema validation with valid data"""
        pipeline = ETLPipeline(
            raw_data_path=temp_directories['raw'],
            clean_data_path=temp_directories['clean']
        )
        
        merged_df = pipeline.merge_data(
            sample_data['aisles'],
            sample_data['departments'],
            sample_data['products'],
            sample_data['orders']
        )
        
        errors = pipeline.validate_schema(merged_df)
        assert len(errors) == 0
    
    def test_validate_schema_missing_columns(self, temp_directories):
        """Test schema validation with missing columns"""
        pipeline = ETLPipeline(
            raw_data_path=temp_directories['raw'],
            clean_data_path=temp_directories['clean']
        )
        
        # Create dataframe with missing required columns
        invalid_df = pd.DataFrame({
            'product_id': [1, 2, 3],
            'some_other_column': ['a', 'b', 'c']
        })
        
        errors = pipeline.validate_schema(invalid_df)
        assert len(errors) > 0
        assert any('Missing required column' in error for error in errors)
    
    def test_calculate_quality_metrics(self, temp_directories, sample_data):
        """Test quality metrics calculation"""
        pipeline = ETLPipeline(
            raw_data_path=temp_directories['raw'],
            clean_data_path=temp_directories['clean']
        )
        
        merged_df = pipeline.merge_data(
            sample_data['aisles'],
            sample_data['departments'],
            sample_data['products'],
            sample_data['orders']
        )
        
        metrics = pipeline.calculate_quality_metrics(merged_df)
        
        assert 'completeness_ratio' in metrics
        assert 'product_id_uniqueness' in metrics
        assert 'valid_product_names_ratio' in metrics
        assert 'avg_product_name_length' in metrics
        
        # Check metric ranges
        assert 0 <= metrics['completeness_ratio'] <= 1
        assert 0 <= metrics['product_id_uniqueness'] <= 1
        assert 0 <= metrics['valid_product_names_ratio'] <= 1
    
    def test_save_clean_data(self, temp_directories, sample_data):
        """Test saving cleaned data to CSV"""
        pipeline = ETLPipeline(
            raw_data_path=temp_directories['raw'],
            clean_data_path=temp_directories['clean']
        )
        
        merged_df = pipeline.merge_data(
            sample_data['aisles'],
            sample_data['departments'],
            sample_data['products'],
            sample_data['orders']
        )
        
        output_file = pipeline.save_clean_data(merged_df)
        
        # Check file exists
        assert os.path.exists(output_file)
        
        # Check file content
        saved_df = pd.read_csv(output_file)
        assert len(saved_df) == len(merged_df)
        assert list(saved_df.columns) == list(merged_df.columns)
    
    def test_save_validation_results(self, temp_directories):
        """Test saving validation results to JSON"""
        pipeline = ETLPipeline(
            raw_data_path=temp_directories['raw'],
            clean_data_path=temp_directories['clean']
        )
        
        validation_result = ValidationResult(
            timestamp="2023-01-01T00:00:00",
            total_records=100,
            validation_errors=[],
            data_quality_metrics={'completeness_ratio': 0.95},
            schema_valid=True,
            file_size_mb=1.5
        )
        
        output_file = pipeline.save_validation_results(validation_result)
        
        # Check file exists
        assert os.path.exists(output_file)
        
        # Check file content
        with open(output_file, 'r') as f:
            saved_data = json.load(f)
        
        assert saved_data['total_records'] == 100
        assert saved_data['schema_valid'] is True
        assert saved_data['file_size_mb'] == 1.5
    
    def test_run_pipeline_success(self, temp_directories, sample_data):
        """Test complete pipeline run with success"""
        # Create sample CSV files
        raw_dir = Path(temp_directories['raw'])
        sample_data['aisles'].to_csv(raw_dir / 'aisles.csv', index=False)
        sample_data['departments'].to_csv(raw_dir / 'departments.csv', index=False)
        sample_data['products'].to_csv(raw_dir / 'products.csv', index=False)
        sample_data['orders'].to_csv(raw_dir / 'orders.csv', index=False)
        
        pipeline = ETLPipeline(
            raw_data_path=temp_directories['raw'],
            clean_data_path=temp_directories['clean']
        )
        
        success = pipeline.run()
        
        assert success is True
        assert pipeline.validation_result is not None
        assert pipeline.validation_result.schema_valid is True
        
        # Check output files exist
        clean_dir = Path(temp_directories['clean'])
        assert (clean_dir / 'instacart_clean.csv').exists()
        assert (clean_dir / 'validation_results.json').exists()
    
    def test_run_pipeline_failure(self, temp_directories):
        """Test pipeline run with missing data"""
        pipeline = ETLPipeline(
            raw_data_path=temp_directories['raw'],
            clean_data_path=temp_directories['clean']
        )
        
        success = pipeline.run()
        assert success is False


class TestValidationResult:
    """Test cases for ValidationResult model"""
    
    def test_validation_result_creation(self):
        """Test ValidationResult model creation"""
        result = ValidationResult(
            timestamp="2023-01-01T00:00:00",
            total_records=1000,
            validation_errors=['Test error'],
            data_quality_metrics={'completeness': 0.95},
            schema_valid=False,
            file_size_mb=2.5
        )
        
        assert result.timestamp == "2023-01-01T00:00:00"
        assert result.total_records == 1000
        assert len(result.validation_errors) == 1
        assert result.schema_valid is False
        assert result.file_size_mb == 2.5
    
    def test_validation_result_serialization(self):
        """Test ValidationResult JSON serialization"""
        result = ValidationResult(
            timestamp="2023-01-01T00:00:00",
            total_records=500,
            validation_errors=[],
            data_quality_metrics={'completeness': 1.0},
            schema_valid=True,
            file_size_mb=1.0
        )
        
        json_data = result.model_dump()
        
        assert json_data['timestamp'] == "2023-01-01T00:00:00"
        assert json_data['total_records'] == 500
        assert json_data['validation_errors'] == []
        assert json_data['schema_valid'] is True