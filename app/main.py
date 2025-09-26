"""Main FastAPI application module."""

from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
import logging
import os
import pandas as pd
import json
from pathlib import Path
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app instance
app = FastAPI(
    title="CSV Clean API",
    description="ETL service for cleaning and processing CSV data",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Data directories
CLEAN_DATA_DIR = Path("data/clean")
REPORTS_DIR = Path("reports")


class HealthResponse(BaseModel):
    """Health check response model."""
    status: str


class DataSummary(BaseModel):
    """Data summary response model."""
    files_processed: int
    total_records: int
    tables: Dict[str, Dict[str, Any]]
    last_updated: str


class ValidationResult(BaseModel):
    """Validation result response model."""
    file: str
    status: str
    timestamp: str
    errors: List[str]
    warnings: List[str]


def load_cleaned_data(filename: str) -> Optional[pd.DataFrame]:
    """Load cleaned CSV data if it exists."""
    filepath = CLEAN_DATA_DIR / filename
    if filepath.exists():
        try:
            return pd.read_csv(filepath)
        except Exception as e:
            logger.error(f"Error loading {filename}: {e}")
            return None
    return None


def get_data_summary_stats(df: pd.DataFrame) -> Dict[str, Any]:
    """Get summary statistics for a DataFrame."""
    return {
        "rows": len(df),
        "columns": len(df.columns),
        "missing_values": df.isnull().sum().sum(),
        "dtypes": df.dtypes.to_dict(),
        "memory_usage_mb": round(df.memory_usage(deep=True).sum() / 1024 / 1024, 2)
    }


@app.get("/health", response_model=HealthResponse)
async def health_check() -> Dict[str, str]:
    """Health check endpoint.
    
    Returns:
        Dict containing service status
    """
    return {"status": "ok"}


@app.get("/")
async def root() -> Dict[str, str]:
    """Root endpoint."""
    return {"message": "CSV Clean API - ETL Service"}


@app.get("/summary", response_model=DataSummary)
async def get_summary() -> DataSummary:
    """Get data summary statistics.
    
    Returns:
        Summary of processed data files
    """
    try:
        # Define expected cleaned files
        expected_files = [
            "cleaned_orders.csv",
            "cleaned_order_products__prior.csv", 
            "cleaned_products.csv",
            "cleaned_aisles.csv",
            "cleaned_departments.csv"
        ]
        
        tables = {}
        total_records = 0
        files_processed = 0
        
        for filename in expected_files:
            df = load_cleaned_data(filename)
            if df is not None:
                files_processed += 1
                total_records += len(df)
                tables[filename.replace("cleaned_", "").replace(".csv", "")] = get_data_summary_stats(df)
        
        # Get last modified time of clean directory
        last_updated = datetime.now().isoformat()
        if CLEAN_DATA_DIR.exists():
            try:
                last_modified = max(
                    f.stat().st_mtime for f in CLEAN_DATA_DIR.glob("*.csv") if f.is_file()
                )
                last_updated = datetime.fromtimestamp(last_modified).isoformat()
            except ValueError:
                pass  # No files found, use current time
        
        return DataSummary(
            files_processed=files_processed,
            total_records=total_records,
            tables=tables,
            last_updated=last_updated
        )
        
    except Exception as e:
        logger.error(f"Error generating summary: {e}")
        raise HTTPException(status_code=500, detail=f"Error generating summary: {str(e)}")


@app.get("/filter")
async def filter_data(
    table: str = Query("products", description="Table to filter (products, orders, aisles, departments)"),
    user_id: Optional[int] = Query(None, description="Filter by user ID (orders table only)"),
    department_id: Optional[int] = Query(None, description="Filter by department ID"),
    limit: int = Query(10, ge=1, le=1000, description="Maximum number of records to return")
) -> Dict[str, Any]:
    """Filter data from cleaned tables.
    
    Args:
        table: Table name to filter
        user_id: Filter by user ID (orders only)
        department_id: Filter by department ID  
        limit: Maximum records to return
        
    Returns:
        Filtered data records
    """
    try:
        # Map table names to files
        table_files = {
            "products": "cleaned_products.csv",
            "orders": "cleaned_orders.csv", 
            "aisles": "cleaned_aisles.csv",
            "departments": "cleaned_departments.csv",
            "order_products": "cleaned_order_products__prior.csv"
        }
        
        if table not in table_files:
            raise HTTPException(
                status_code=400, 
                detail=f"Invalid table '{table}'. Available: {list(table_files.keys())}"
            )
        
        # Load the requested table
        df = load_cleaned_data(table_files[table])
        if df is None:
            raise HTTPException(
                status_code=404, 
                detail=f"Table '{table}' not found. Run ETL pipeline first."
            )
        
        # Apply filters
        filtered_df = df.copy()
        
        if user_id is not None and "user_id" in filtered_df.columns:
            filtered_df = filtered_df[filtered_df["user_id"] == user_id]
        
        if department_id is not None and "department_id" in filtered_df.columns:
            filtered_df = filtered_df[filtered_df["department_id"] == department_id]
        
        # Apply limit
        filtered_df = filtered_df.head(limit)
        
        # Convert to records
        records = filtered_df.to_dict(orient="records")
        
        return {
            "table": table,
            "filters": {
                "user_id": user_id,
                "department_id": department_id,
                "limit": limit
            },
            "total_rows": len(records),
            "data": records
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error filtering data: {e}")
        raise HTTPException(status_code=500, detail=f"Error filtering data: {str(e)}")


@app.get("/validations/last", response_model=List[ValidationResult])
async def get_last_validations() -> List[ValidationResult]:
    """Get the latest validation results.
    
    Returns:
        List of validation results for processed files
    """
    try:
        validations = []
        
        # Check for validation results from ETL process
        validation_files = [
            ("orders", "cleaned_orders.csv"),
            ("order_products", "cleaned_order_products__prior.csv"),
            ("products", "cleaned_products.csv"), 
            ("aisles", "cleaned_aisles.csv"),
            ("departments", "cleaned_departments.csv")
        ]
        
        for table_name, filename in validation_files:
            df = load_cleaned_data(filename)
            
            if df is not None:
                # Basic validation checks
                errors = []
                warnings = []
                
                # Check for empty data
                if len(df) == 0:
                    errors.append("No data found after cleaning")
                
                # Check for missing values in key columns
                if table_name == "orders" and "order_id" in df.columns:
                    if df["order_id"].isnull().any():
                        errors.append("Missing order_id values found")
                
                if table_name == "products" and "product_id" in df.columns:
                    if df["product_id"].isnull().any():
                        errors.append("Missing product_id values found")
                
                # Check data types
                if df.select_dtypes(include=['object']).empty and len(df.columns) > 2:
                    warnings.append("No string columns found - possible parsing issues")
                
                # Get file timestamp
                filepath = CLEAN_DATA_DIR / filename
                timestamp = datetime.fromtimestamp(filepath.stat().st_mtime).isoformat()
                
                status = "error" if errors else ("warning" if warnings else "success")
                
                validations.append(ValidationResult(
                    file=table_name,
                    status=status,
                    timestamp=timestamp,
                    errors=errors,
                    warnings=warnings
                ))
            else:
                validations.append(ValidationResult(
                    file=table_name,
                    status="missing",
                    timestamp=datetime.now().isoformat(),
                    errors=[f"File {filename} not found"],
                    warnings=[]
                ))
        
        return validations
        
    except Exception as e:
        logger.error(f"Error getting validations: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting validations: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    
    port = int(os.getenv("PORT", 8000))
    host = os.getenv("HOST", "0.0.0.0")
    
    uvicorn.run(
        "app.main:app",
        host=host,
        port=port,
        reload=True,
        log_level="info"
    )