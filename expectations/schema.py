"""Data validation schemas using Pandera."""

import pandera as pa
from pandera import Column, DataFrameSchema, Check
from pandera.typing import DataFrame, Series
import pandas as pd
from typing import Optional


class BaseCSVSchema(pa.DataFrameModel):
    """Base schema for CSV data validation."""
    
    class Config:
        """Pandera configuration."""
        strict = True
        coerce = True


class SampleDataSchema(BaseCSVSchema):
    """Example schema for sample CSV data.
    
    This is a template that can be modified based on your specific data requirements.
    """
    
    # Example columns - modify these based on your actual data structure
    id: Series[int] = pa.Field(ge=1, description="Unique identifier")
    name: Series[str] = pa.Field(str_length={"min_val": 1, "max_val": 100}, description="Name field")
    email: Optional[Series[str]] = pa.Field(
        nullable=True,
        regex=r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$",
        description="Email address"
    )
    age: Optional[Series[int]] = pa.Field(ge=0, le=150, nullable=True, description="Age in years")
    created_date: Series[pd.Timestamp] = pa.Field(description="Creation timestamp")


class CleanedDataSchema(BaseCSVSchema):
    """Schema for cleaned/processed data."""
    
    # Define the expected structure after cleaning
    id: Series[int] = pa.Field(ge=1, unique=True, description="Unique identifier")
    name: Series[str] = pa.Field(str_length={"min_val": 1}, description="Cleaned name field")
    email: Optional[Series[str]] = pa.Field(
        nullable=True,
        regex=r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$",
        description="Validated email address"
    )
    age: Optional[Series[int]] = pa.Field(ge=0, le=150, nullable=True, description="Validated age")
    created_date: Series[pd.Timestamp] = pa.Field(description="Parsed creation timestamp")
    
    @pa.check("name")
    def name_not_empty(cls, series: Series[str]) -> Series[bool]:
        """Check that name is not empty after stripping whitespace."""
        return series.str.strip().str.len() > 0


class NumericDataSchema(BaseCSVSchema):
    """Schema for numeric data validation."""
    
    value: Series[float] = pa.Field(description="Numeric value")
    category: Series[str] = pa.Field(isin=["A", "B", "C"], description="Category")
    
    @pa.check("value")
    def value_not_null(cls, series: Series[float]) -> Series[bool]:
        """Check that values are not null."""
        return ~series.isna()


def validate_dataframe(df: pd.DataFrame, schema_class: type) -> pd.DataFrame:
    """Validate a DataFrame against a schema.
    
    Args:
        df: DataFrame to validate
        schema_class: Pandera schema class to validate against
        
    Returns:
        Validated DataFrame
        
    Raises:
        pandera.errors.SchemaError: If validation fails
    """
    try:
        validated_df = schema_class.validate(df)
        return validated_df
    except pa.errors.SchemaError as e:
        # Log the validation error details
        error_msg = f"Schema validation failed: {e}"
        raise pa.errors.SchemaError(error_msg) from e


def get_schema_summary(schema_class: type) -> dict:
    """Get a summary of a schema's requirements.
    
    Args:
        schema_class: Pandera schema class
        
    Returns:
        Dictionary with schema information
    """
    schema_info = {
        "schema_name": schema_class.__name__,
        "columns": {},
        "checks": []
    }
    
    # Get column information
    for field_name, field_info in schema_class.__annotations__.items():
        if hasattr(schema_class, field_name):
            field = getattr(schema_class, field_name)
            if hasattr(field, "field_info"):
                schema_info["columns"][field_name] = {
                    "type": str(field_info),
                    "nullable": getattr(field.field_info, "nullable", False),
                    "description": getattr(field.field_info, "description", "")
                }
    
    return schema_info


# Example usage schemas - create instances for common validation patterns
SAMPLE_SCHEMA = SampleDataSchema
CLEANED_SCHEMA = CleanedDataSchema
NUMERIC_SCHEMA = NumericDataSchema