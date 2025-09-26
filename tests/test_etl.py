"""Tests for ETL functionality."""

import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import tempfile
import shutil
from etl.clean import CSVCleaner


class TestCSVCleaner:
    """Test suite for CSVCleaner class."""
    
    @pytest.fixture
    def sample_data(self):
        """Create sample DataFrame for testing."""
        return pd.DataFrame({
            "ID": [1, 2, 3, 2, 4],  # Duplicate row
            "Name": ["Alice", "Bob", "Charlie", "Bob", "  David  "],  # Whitespace
            "Age": [25, np.nan, 30, np.nan, 35],  # Missing values
            "Email": ["alice@test.com", "", "charlie@test.com", "", "david@test.com"]
        })
    
    @pytest.fixture
    def temp_dirs(self):
        """Create temporary directories for testing."""
        temp_dir = tempfile.mkdtemp()
        raw_dir = Path(temp_dir) / "raw"
        clean_dir = Path(temp_dir) / "clean"
        raw_dir.mkdir()
        clean_dir.mkdir()
        
        yield str(raw_dir), str(clean_dir)
        
        # Cleanup
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def csv_cleaner(self, temp_dirs):
        """Create CSVCleaner instance with temporary directories."""
        raw_dir, clean_dir = temp_dirs
        return CSVCleaner(raw_data_dir=raw_dir, clean_data_dir=clean_dir)
    
    def test_clean_dataframe_removes_duplicates(self, csv_cleaner, sample_data):
        """Test that duplicate rows are removed."""
        config = {"remove_duplicates": True}
        cleaned_df = csv_cleaner.clean_dataframe(sample_data, config)
        
        assert len(cleaned_df) == 4  # One duplicate removed
        assert not cleaned_df.duplicated().any()
    
    def test_clean_dataframe_handles_missing_values(self, csv_cleaner, sample_data):
        """Test missing value handling strategies."""
        # Test drop strategy
        config = {"missing_strategy": "drop"}
        cleaned_df = csv_cleaner.clean_dataframe(sample_data, config)
        assert not cleaned_df.isnull().any().any()
        
        # Test fill mean strategy  
        config = {"missing_strategy": "fill_mean"}
        cleaned_df = csv_cleaner.clean_dataframe(sample_data, config)
        # Check that Age column (numeric) has no NaN values
        assert not cleaned_df["Age"].isnull().any()
    
    def test_clean_dataframe_strips_whitespace(self, csv_cleaner, sample_data):
        """Test whitespace stripping from string columns."""
        config = {"strip_whitespace": True}
        cleaned_df = csv_cleaner.clean_dataframe(sample_data, config)
        
        # David should have whitespace stripped
        david_row = cleaned_df[cleaned_df["Name"] == "David"]
        assert len(david_row) > 0
    
    def test_clean_dataframe_lowercase_columns(self, csv_cleaner, sample_data):
        """Test column name conversion to lowercase."""
        config = {"lowercase_columns": True}
        cleaned_df = csv_cleaner.clean_dataframe(sample_data, config)
        
        expected_columns = ["id", "name", "age", "email"]
        assert all(col in cleaned_df.columns for col in expected_columns)
    
    def test_load_csv_file_not_found(self, csv_cleaner):
        """Test error handling for missing files."""
        with pytest.raises(FileNotFoundError):
            csv_cleaner.load_csv("nonexistent.csv")
    
    def test_save_cleaned_csv(self, csv_cleaner, sample_data, temp_dirs):
        """Test saving cleaned CSV file."""
        raw_dir, clean_dir = temp_dirs
        output_path = csv_cleaner.save_cleaned_csv(sample_data, "test_output.csv")
        
        assert output_path.exists()
        loaded_df = pd.read_csv(output_path)
        assert len(loaded_df) == len(sample_data)
    
    def test_process_csv_end_to_end(self, csv_cleaner, sample_data, temp_dirs):
        """Test end-to-end CSV processing."""
        raw_dir, clean_dir = temp_dirs
        
        # Save sample data as input file
        input_file = Path(raw_dir) / "test_input.csv"
        sample_data.to_csv(input_file, index=False)
        
        # Process the file
        output_path = csv_cleaner.process_csv("test_input.csv")
        
        assert output_path.exists()
        processed_df = pd.read_csv(output_path)
        
        # Should have removed duplicates and cleaned data
        assert len(processed_df) < len(sample_data)  # Duplicates removed
        assert all(col.islower() for col in processed_df.columns)  # Lowercase columns
    
    def test_get_data_summary(self, csv_cleaner, sample_data):
        """Test data summary generation."""
        summary = csv_cleaner.get_data_summary(sample_data)
        
        assert "shape" in summary
        assert "columns" in summary
        assert "dtypes" in summary
        assert "missing_values" in summary
        assert summary["shape"] == sample_data.shape
        assert len(summary["columns"]) == len(sample_data.columns)