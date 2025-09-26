#!/usr/bin/env python3
"""
Instacart Data ETL Pipeline
Merges raw CSV files into a cleaned, denormalized dataset
"""

import json
import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import pandas as pd
from pydantic import BaseModel, Field, ValidationError

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ValidationResult(BaseModel):
    """Data validation result model"""
    timestamp: str = Field(..., description="Validation timestamp")
    total_records: int = Field(..., description="Total number of records processed")
    validation_errors: List[str] = Field(default_factory=list, description="List of validation errors")
    data_quality_metrics: Dict[str, float] = Field(default_factory=dict, description="Data quality metrics")
    schema_valid: bool = Field(..., description="Whether schema validation passed")
    file_size_mb: float = Field(..., description="Output file size in MB")


class ETLPipeline:
    """Main ETL Pipeline class"""
    
    def __init__(self, raw_data_path: str = "data/raw", clean_data_path: str = "data/clean"):
        self.raw_data_path = Path(raw_data_path)
        self.clean_data_path = Path(clean_data_path)
        self.validation_result: Optional[ValidationResult] = None
        
        # Ensure clean data directory exists
        self.clean_data_path.mkdir(parents=True, exist_ok=True)
    
    def load_raw_data(self) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
        """Load all raw CSV files"""
        logger.info("Loading raw data files...")
        
        try:
            # Load reference tables
            aisles_df = pd.read_csv(self.raw_data_path / "aisles.csv")
            departments_df = pd.read_csv(self.raw_data_path / "departments.csv")
            products_df = pd.read_csv(self.raw_data_path / "products.csv")
            
            # For demo purposes, we'll use a sample of orders data to avoid memory issues
            # In production, you'd process this in chunks
            orders_df = pd.read_csv(self.raw_data_path / "orders.csv", nrows=10000)
            
            logger.info(f"Loaded {len(aisles_df)} aisles, {len(departments_df)} departments, "
                       f"{len(products_df)} products, {len(orders_df)} orders")
            
            return aisles_df, departments_df, products_df, orders_df
            
        except Exception as e:
            logger.error(f"Error loading raw data: {e}")
            raise
    
    def merge_data(self, aisles_df: pd.DataFrame, departments_df: pd.DataFrame, 
                  products_df: pd.DataFrame, orders_df: pd.DataFrame) -> pd.DataFrame:
        """Merge all dataframes into a denormalized table"""
        logger.info("Merging data...")
        
        try:
            # Start with products and join reference tables
            merged_df = products_df.copy()
            
            # Join aisles
            merged_df = merged_df.merge(aisles_df, on='aisle_id', how='left')
            
            # Join departments  
            merged_df = merged_df.merge(departments_df, on='department_id', how='left')
            
            # Add some computed fields for analytics
            merged_df['product_name_length'] = merged_df['product_name'].str.len()
            merged_df['has_special_chars'] = merged_df['product_name'].str.contains(r'[^a-zA-Z0-9\s]', regex=True)
            
            # Add order statistics (simplified for demo)
            order_stats = orders_df.groupby('user_id').agg({
                'order_id': 'count',
                'days_since_prior_order': 'mean'
            }).rename(columns={
                'order_id': 'user_total_orders',
                'days_since_prior_order': 'avg_days_between_orders'
            }).reset_index()
            
            # For demo, add some sample order stats to products (in reality you'd join through order_products)
            merged_df['sample_user_orders'] = merged_df.index % 20 + 1  # Simulate order frequency
            merged_df['estimated_popularity'] = merged_df['product_id'] % 100  # Simulate popularity score
            
            logger.info(f"Merged data contains {len(merged_df)} records")
            return merged_df
            
        except Exception as e:
            logger.error(f"Error merging data: {e}")
            raise
    
    def validate_schema(self, df: pd.DataFrame) -> List[str]:
        """Validate the schema of the merged dataframe"""
        logger.info("Validating schema...")
        
        errors = []
        
        # Required columns
        required_columns = [
            'product_id', 'product_name', 'aisle_id', 'department_id',
            'aisle', 'department', 'product_name_length'
        ]
        
        for col in required_columns:
            if col not in df.columns:
                errors.append(f"Missing required column: {col}")
        
        # Data type checks
        if 'product_id' in df.columns and not pd.api.types.is_numeric_dtype(df['product_id']):
            errors.append("product_id should be numeric")
        
        if 'aisle_id' in df.columns and not pd.api.types.is_numeric_dtype(df['aisle_id']):
            errors.append("aisle_id should be numeric")
            
        if 'department_id' in df.columns and not pd.api.types.is_numeric_dtype(df['department_id']):
            errors.append("department_id should be numeric")
        
        # Check for nulls in critical fields
        critical_fields = ['product_id', 'product_name', 'aisle_id', 'department_id']
        for field in critical_fields:
            if field in df.columns and df[field].isnull().any():
                null_count = df[field].isnull().sum()
                errors.append(f"{field} has {null_count} null values")
        
        return errors
    
    def calculate_quality_metrics(self, df: pd.DataFrame) -> Dict[str, float]:
        """Calculate data quality metrics"""
        logger.info("Calculating quality metrics...")
        
        metrics = {}
        
        # Completeness metrics
        total_cells = df.shape[0] * df.shape[1]
        non_null_cells = df.count().sum()
        metrics['completeness_ratio'] = non_null_cells / total_cells if total_cells > 0 else 0
        
        # Uniqueness metrics
        if 'product_id' in df.columns:
            metrics['product_id_uniqueness'] = df['product_id'].nunique() / len(df) if len(df) > 0 else 0
        
        # Validity metrics
        if 'product_name' in df.columns:
            valid_names = df['product_name'].str.len() > 0
            metrics['valid_product_names_ratio'] = valid_names.sum() / len(df) if len(df) > 0 else 0
        
        # Range checks
        if 'product_name_length' in df.columns:
            metrics['avg_product_name_length'] = df['product_name_length'].mean()
            metrics['max_product_name_length'] = df['product_name_length'].max()
        
        return metrics
    
    def save_clean_data(self, df: pd.DataFrame) -> str:
        """Save the cleaned dataframe to CSV"""
        logger.info("Saving cleaned data...")
        
        output_file = self.clean_data_path / "instacart_clean.csv"
        
        try:
            df.to_csv(output_file, index=False)
            logger.info(f"Saved {len(df)} records to {output_file}")
            return str(output_file)
        except Exception as e:
            logger.error(f"Error saving clean data: {e}")
            raise
    
    def save_validation_results(self, validation_result: ValidationResult) -> str:
        """Save validation results to JSON"""
        logger.info("Saving validation results...")
        
        output_file = self.clean_data_path / "validation_results.json"
        
        try:
            with open(output_file, 'w') as f:
                json.dump(validation_result.model_dump(), f, indent=2)
            logger.info(f"Saved validation results to {output_file}")
            return str(output_file)
        except Exception as e:
            logger.error(f"Error saving validation results: {e}")
            raise
    
    def run(self) -> bool:
        """Run the complete ETL pipeline"""
        logger.info("Starting ETL pipeline...")
        
        try:
            # Load data
            aisles_df, departments_df, products_df, orders_df = self.load_raw_data()
            
            # Merge data
            merged_df = self.merge_data(aisles_df, departments_df, products_df, orders_df)
            
            # Validate schema
            validation_errors = self.validate_schema(merged_df)
            
            # Calculate quality metrics
            quality_metrics = self.calculate_quality_metrics(merged_df)
            
            # Save clean data
            output_file = self.save_clean_data(merged_df)
            
            # Calculate file size
            file_size_mb = os.path.getsize(output_file) / (1024 * 1024)
            
            # Create validation result
            self.validation_result = ValidationResult(
                timestamp=datetime.now().isoformat(),
                total_records=len(merged_df),
                validation_errors=validation_errors,
                data_quality_metrics=quality_metrics,
                schema_valid=len(validation_errors) == 0,
                file_size_mb=round(file_size_mb, 2)
            )
            
            # Save validation results
            self.save_validation_results(self.validation_result)
            
            # Log results
            if validation_errors:
                logger.warning(f"ETL completed with {len(validation_errors)} validation errors")
                for error in validation_errors:
                    logger.warning(f"  - {error}")
            else:
                logger.info("ETL completed successfully with no validation errors")
            
            logger.info(f"Quality metrics: {quality_metrics}")
            
            return len(validation_errors) == 0
            
        except Exception as e:
            logger.error(f"ETL pipeline failed: {e}")
            return False


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Run Instacart Data ETL Pipeline')
    parser.add_argument('--raw-data-path', default='data/raw', 
                       help='Path to raw data directory')
    parser.add_argument('--clean-data-path', default='data/clean',
                       help='Path to clean data output directory')
    
    args = parser.parse_args()
    
    # Initialize and run pipeline
    pipeline = ETLPipeline(args.raw_data_path, args.clean_data_path)
    success = pipeline.run()
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()