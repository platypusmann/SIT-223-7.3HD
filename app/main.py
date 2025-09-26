"""
FastAPI application for serving Instacart cleaned data
Provides REST API endpoints for data access and validation results
"""

import json
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Union

import pandas as pd
import uvicorn
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Instacart Data API",
    description="REST API for accessing cleaned Instacart dataset and validation results",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configuration
DATA_PATH = Path("data/clean")
CLEAN_DATA_FILE = DATA_PATH / "instacart_clean.csv"
VALIDATION_FILE = DATA_PATH / "validation_results.json"

# Global data cache
_data_cache: Optional[pd.DataFrame] = None
_validation_cache: Optional[Dict] = None


# Pydantic models for API responses
class HealthResponse(BaseModel):
    """Health check response model"""
    status: str = Field(..., description="API status")
    timestamp: str = Field(..., description="Current timestamp")
    data_available: bool = Field(..., description="Whether clean data is available")
    total_records: Optional[int] = Field(None, description="Total number of records in dataset")


class SummaryResponse(BaseModel):
    """Dataset summary response model"""
    total_records: int = Field(..., description="Total number of records")
    total_products: int = Field(..., description="Number of unique products")
    total_aisles: int = Field(..., description="Number of unique aisles")
    total_departments: int = Field(..., description="Number of unique departments")
    avg_product_name_length: float = Field(..., description="Average product name length")
    data_quality_score: float = Field(..., description="Overall data quality score (0-1)")


class ValidationResponse(BaseModel):
    """Validation results response model"""
    timestamp: str = Field(..., description="Validation timestamp")
    total_records: int = Field(..., description="Total number of records processed")
    validation_errors: List[str] = Field(..., description="List of validation errors")
    data_quality_metrics: Dict[str, float] = Field(..., description="Data quality metrics")
    schema_valid: bool = Field(..., description="Whether schema validation passed")
    file_size_mb: float = Field(..., description="Output file size in MB")


def load_data() -> pd.DataFrame:
    """Load cleaned data with caching"""
    global _data_cache
    
    if _data_cache is None:
        if not CLEAN_DATA_FILE.exists():
            raise HTTPException(
                status_code=404, 
                detail=f"Clean data file not found: {CLEAN_DATA_FILE}"
            )
        
        try:
            _data_cache = pd.read_csv(CLEAN_DATA_FILE)
            logger.info(f"Loaded {len(_data_cache)} records from clean data file")
        except Exception as e:
            logger.error(f"Error loading clean data: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Error loading clean data: {str(e)}"
            )
    
    return _data_cache


def load_validation_results() -> Dict:
    """Load validation results with caching"""
    global _validation_cache
    
    if _validation_cache is None:
        if not VALIDATION_FILE.exists():
            raise HTTPException(
                status_code=404,
                detail=f"Validation file not found: {VALIDATION_FILE}"
            )
        
        try:
            with open(VALIDATION_FILE, 'r') as f:
                _validation_cache = json.load(f)
            logger.info("Loaded validation results from file")
        except Exception as e:
            logger.error(f"Error loading validation results: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Error loading validation results: {str(e)}"
            )
    
    return _validation_cache


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """
    Health check endpoint
    Returns API status and data availability
    """
    try:
        data_available = CLEAN_DATA_FILE.exists()
        total_records = None
        
        if data_available:
            try:
                df = load_data()
                total_records = len(df)
            except Exception:
                data_available = False
        
        return HealthResponse(
            status="healthy",
            timestamp=datetime.now().isoformat(),
            data_available=data_available,
            total_records=total_records
        )
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return JSONResponse(
            status_code=500,
            content={
                "status": "unhealthy",
                "timestamp": datetime.now().isoformat(),
                "error": str(e),
                "data_available": False
            }
        )


@app.get("/summary", response_model=SummaryResponse)
async def get_summary():
    """
    Get dataset summary statistics
    Returns key metrics about the cleaned dataset
    """
    try:
        df = load_data()
        
        # Calculate summary statistics
        total_records = len(df)
        total_products = df['product_id'].nunique() if 'product_id' in df.columns else 0
        total_aisles = df['aisle_id'].nunique() if 'aisle_id' in df.columns else 0
        total_departments = df['department_id'].nunique() if 'department_id' in df.columns else 0
        
        avg_name_length = df['product_name_length'].mean() if 'product_name_length' in df.columns else 0
        
        # Calculate data quality score based on completeness
        total_cells = df.shape[0] * df.shape[1]
        non_null_cells = df.count().sum()
        data_quality_score = non_null_cells / total_cells if total_cells > 0 else 0
        
        return SummaryResponse(
            total_records=total_records,
            total_products=total_products,
            total_aisles=total_aisles,
            total_departments=total_departments,
            avg_product_name_length=round(avg_name_length, 2),
            data_quality_score=round(data_quality_score, 3)
        )
        
    except Exception as e:
        logger.error(f"Error generating summary: {e}")
        raise HTTPException(status_code=500, detail=f"Error generating summary: {str(e)}")


@app.get("/filter")
async def filter_data(
    department: Optional[str] = Query(None, description="Filter by department name"),
    aisle: Optional[str] = Query(None, description="Filter by aisle name"),
    min_name_length: Optional[int] = Query(None, description="Minimum product name length"),
    max_name_length: Optional[int] = Query(None, description="Maximum product name length"),
    limit: int = Query(100, description="Maximum number of records to return", le=1000)
):
    """
    Filter and return dataset records
    Supports filtering by department, aisle, and product name length
    """
    try:
        df = load_data()
        
        # Apply filters
        filtered_df = df.copy()
        
        if department:
            if 'department' in filtered_df.columns:
                filtered_df = filtered_df[
                    filtered_df['department'].str.contains(department, case=False, na=False)
                ]
            else:
                raise HTTPException(status_code=400, detail="Department column not available")
        
        if aisle:
            if 'aisle' in filtered_df.columns:
                filtered_df = filtered_df[
                    filtered_df['aisle'].str.contains(aisle, case=False, na=False)
                ]
            else:
                raise HTTPException(status_code=400, detail="Aisle column not available")
        
        if min_name_length is not None:
            if 'product_name_length' in filtered_df.columns:
                filtered_df = filtered_df[filtered_df['product_name_length'] >= min_name_length]
            else:
                raise HTTPException(status_code=400, detail="Product name length column not available")
        
        if max_name_length is not None:
            if 'product_name_length' in filtered_df.columns:
                filtered_df = filtered_df[filtered_df['product_name_length'] <= max_name_length]
            else:
                raise HTTPException(status_code=400, detail="Product name length column not available")
        
        # Apply limit
        filtered_df = filtered_df.head(limit)
        
        # Convert to JSON-serializable format
        result = {
            "total_filtered_records": len(filtered_df),
            "records": filtered_df.to_dict('records')
        }
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error filtering data: {e}")
        raise HTTPException(status_code=500, detail=f"Error filtering data: {str(e)}")


@app.get("/validations/last", response_model=ValidationResponse)
async def get_last_validation():
    """
    Get the last validation results
    Returns validation metrics and data quality information
    """
    try:
        validation_data = load_validation_results()
        
        return ValidationResponse(**validation_data)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving validation results: {e}")
        raise HTTPException(status_code=500, detail=f"Error retrieving validation results: {str(e)}")


@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "message": "Instacart Data API",
        "version": "1.0.0",
        "endpoints": {
            "health": "/health",
            "summary": "/summary", 
            "filter": "/filter",
            "validations": "/validations/last",
            "docs": "/docs"
        }
    }


# Health check for container orchestration
@app.get("/ping")
async def ping():
    """Simple ping endpoint for load balancers"""
    return {"ping": "pong"}


if __name__ == "__main__":
    # For development
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )