"""Data cleaning and transformation module."""

import pandas as pd
import numpy as np
from pathlib import Path
from typing import Optional, Dict, Any, List
import logging

logger = logging.getLogger(__name__)


class CSVCleaner:
    """CSV data cleaning and transformation utilities."""
    
    def __init__(self, raw_data_dir: str = "data/raw", clean_data_dir: str = "data/clean"):
        """Initialize the CSV cleaner.
        
        Args:
            raw_data_dir: Directory containing raw CSV files
            clean_data_dir: Directory for cleaned CSV files
        """
        self.raw_data_dir = Path(raw_data_dir)
        self.clean_data_dir = Path(clean_data_dir)
        self.clean_data_dir.mkdir(parents=True, exist_ok=True)
    
    def load_csv(self, filename: str, **kwargs) -> pd.DataFrame:
        """Load a CSV file from the raw data directory.
        
        Args:
            filename: Name of the CSV file
            **kwargs: Additional pandas read_csv parameters
            
        Returns:
            Loaded DataFrame
        """
        filepath = self.raw_data_dir / filename
        if not filepath.exists():
            raise FileNotFoundError(f"File {filepath} not found")
        
        logger.info(f"Loading CSV file: {filepath}")
        return pd.read_csv(filepath, **kwargs)
    
    def clean_dataframe(self, df: pd.DataFrame, config: Optional[Dict[str, Any]] = None) -> pd.DataFrame:
        """Clean a pandas DataFrame.
        
        Args:
            df: Input DataFrame
            config: Cleaning configuration dictionary
            
        Returns:
            Cleaned DataFrame
        """
        if config is None:
            config = {}
        
        cleaned_df = df.copy()
        
        # Remove duplicates
        if config.get("remove_duplicates", True):
            initial_rows = len(cleaned_df)
            cleaned_df = cleaned_df.drop_duplicates()
            removed_rows = initial_rows - len(cleaned_df)
            if removed_rows > 0:
                logger.info(f"Removed {removed_rows} duplicate rows")
        
        # Handle missing values
        missing_strategy = config.get("missing_strategy", "drop")
        if missing_strategy == "drop":
            cleaned_df = cleaned_df.dropna()
        elif missing_strategy == "fill_mean":
            numeric_columns = cleaned_df.select_dtypes(include=[np.number]).columns
            cleaned_df[numeric_columns] = cleaned_df[numeric_columns].fillna(
                cleaned_df[numeric_columns].mean()
            )
        elif missing_strategy == "fill_forward":
            cleaned_df = cleaned_df.ffill()
        
        # Strip whitespace from string columns
        if config.get("strip_whitespace", True):
            string_columns = cleaned_df.select_dtypes(include=["object"]).columns
            cleaned_df[string_columns] = cleaned_df[string_columns].apply(
                lambda x: x.str.strip() if hasattr(x, 'str') else x
            )
        
        # Convert column names to lowercase
        if config.get("lowercase_columns", True):
            cleaned_df.columns = cleaned_df.columns.str.lower().str.replace(" ", "_")
        
        logger.info(f"Cleaned DataFrame shape: {cleaned_df.shape}")
        return cleaned_df
    
    def save_cleaned_csv(self, df: pd.DataFrame, filename: str, **kwargs) -> Path:
        """Save a cleaned DataFrame to CSV.
        
        Args:
            df: DataFrame to save
            filename: Output filename
            **kwargs: Additional pandas to_csv parameters
            
        Returns:
            Path to saved file
        """
        output_path = self.clean_data_dir / filename
        df.to_csv(output_path, index=False, **kwargs)
        logger.info(f"Saved cleaned CSV to: {output_path}")
        return output_path
    
    def process_csv(
        self, 
        input_filename: str, 
        output_filename: Optional[str] = None,
        cleaning_config: Optional[Dict[str, Any]] = None,
        **read_kwargs
    ) -> Path:
        """Process a CSV file end-to-end.
        
        Args:
            input_filename: Input CSV filename
            output_filename: Output CSV filename (defaults to cleaned_{input_filename})
            cleaning_config: Configuration for cleaning operations
            **read_kwargs: Additional parameters for reading CSV
            
        Returns:
            Path to cleaned CSV file
        """
        if output_filename is None:
            output_filename = f"cleaned_{input_filename}"
        
        # Load, clean, and save
        df = self.load_csv(input_filename, **read_kwargs)
        cleaned_df = self.clean_dataframe(df, cleaning_config)
        output_path = self.save_cleaned_csv(cleaned_df, output_filename)
        
        return output_path
    
    def get_data_summary(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Get summary statistics for a DataFrame.
        
        Args:
            df: Input DataFrame
            
        Returns:
            Dictionary with summary statistics
        """
        return {
            "shape": df.shape,
            "columns": df.columns.tolist(),
            "dtypes": df.dtypes.to_dict(),
            "missing_values": df.isnull().sum().to_dict(),
            "memory_usage": df.memory_usage(deep=True).sum(),
            "numeric_summary": df.describe().to_dict() if len(df.select_dtypes(include=[np.number]).columns) > 0 else {}
        }


def process_instacart_data(raw_data_dir: str = "data/raw", clean_data_dir: str = "data/clean"):
    """Process Instacart dataset files.
    
    Args:
        raw_data_dir: Directory containing raw CSV files
        clean_data_dir: Directory for cleaned CSV files
    """
    cleaner = CSVCleaner(raw_data_dir=raw_data_dir, clean_data_dir=clean_data_dir)
    
    # Define expected Instacart files
    instacart_files = [
        "orders.csv",
        "order_products__prior.csv", 
        "products.csv",
        "aisles.csv",
        "departments.csv"
    ]
    
    # Process each file
    for filename in instacart_files:
        try:
            logger.info(f"Processing {filename}...")
            
            # Load the raw data
            df = cleaner.load_csv(filename)
            logger.info(f"Loaded {filename}: {df.shape}")
            
            # Get data summary before cleaning
            summary_before = cleaner.get_data_summary(df)
            logger.info(f"Before cleaning - Rows: {summary_before['shape'][0]}, "
                       f"Columns: {summary_before['shape'][1]}, "
                       f"Missing values: {sum(summary_before['missing_values'].values())}")
            
            # Clean the data
            cleaned_df = cleaner.clean_dataframe(df, {
                "remove_duplicates": True,
                "missing_strategy": "drop" if filename == "orders.csv" else "fill_forward",
                "strip_whitespace": True,
                "lowercase_columns": True
            })
            
            # Get data summary after cleaning
            summary_after = cleaner.get_data_summary(cleaned_df)
            logger.info(f"After cleaning - Rows: {summary_after['shape'][0]}, "
                       f"Columns: {summary_after['shape'][1]}, "
                       f"Missing values: {sum(summary_after['missing_values'].values())}")
            
            # Save cleaned data
            output_filename = f"cleaned_{filename}"
            output_path = cleaner.save_cleaned_csv(cleaned_df, output_filename)
            logger.info(f"Saved cleaned data to: {output_path}")
            
        except FileNotFoundError:
            logger.warning(f"File {filename} not found in {raw_data_dir}, skipping...")
        except Exception as e:
            logger.error(f"Error processing {filename}: {e}")
    
    logger.info("Data processing complete!")


def main():
    """Main function to run the ETL pipeline."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Instacart ETL Pipeline")
    parser.add_argument(
        "--sample", 
        action="store_true", 
        help="Use sample data from data/raw_sample/ instead of data/raw/"
    )
    parser.add_argument(
        "--raw-dir",
        type=str,
        help="Custom raw data directory path"
    )
    parser.add_argument(
        "--clean-dir", 
        type=str,
        default="data/clean",
        help="Clean data output directory (default: data/clean)"
    )
    parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        default="INFO",
        help="Set logging level (default: INFO)"
    )
    
    args = parser.parse_args()
    
    # Configure logging
    logging.basicConfig(
        level=getattr(logging, args.log_level),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Determine raw data directory
    if args.raw_dir:
        raw_data_dir = args.raw_dir
    elif args.sample:
        raw_data_dir = "data/raw_sample"
        logger.info("Using sample data from data/raw_sample/")
    else:
        raw_data_dir = "data/raw"
        logger.info("Using full data from data/raw/")
    
    # Run the ETL pipeline
    process_instacart_data(raw_data_dir=raw_data_dir, clean_data_dir=args.clean_dir)


if __name__ == "__main__":
    main()