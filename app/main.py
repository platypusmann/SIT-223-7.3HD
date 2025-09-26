"""Main FastAPI application module."""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict, Any
import logging
import os

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


class HealthResponse(BaseModel):
    """Health check response model."""
    status: str


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