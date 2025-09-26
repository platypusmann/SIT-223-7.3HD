"""Data validation schemas using Pandera for Instacart dataset."""

import pandera as pa
from pandera import Column, DataFrameSchema, Check
from pandera.typing import DataFrame, Series
import pandas as pd
from typing import Optional


class BaseInstacartSchema(pa.DataFrameModel):
    """Base schema for Instacart data validation."""
    
    class Config:
        """Pandera configuration."""
        strict = False  # Allow extra columns
        coerce = True


class OrdersSchema(BaseInstacartSchema):
    """Schema for orders.csv data."""
    
    order_id: Series[int] = pa.Field(ge=1, description="Unique order identifier")
    user_id: Series[int] = pa.Field(ge=1, description="User identifier")
    eval_set: Series[str] = pa.Field(isin=["prior", "train", "test"], description="Evaluation set")
    order_number: Series[int] = pa.Field(ge=1, description="Order sequence number for user")
    order_dow: Series[int] = pa.Field(ge=0, le=6, description="Day of week (0=Sunday)")
    order_hour_of_day: Series[int] = pa.Field(ge=0, le=23, description="Hour of day")
    days_since_prior_order: Optional[Series[float]] = pa.Field(
        ge=0, nullable=True, description="Days since previous order"
    )


class ProductsSchema(BaseInstacartSchema):
    """Schema for products.csv data."""
    
    product_id: Series[int] = pa.Field(ge=1, description="Unique product identifier")
    product_name: Series[str] = pa.Field(str_length={"min_val": 1}, description="Product name")
    aisle_id: Series[int] = pa.Field(ge=1, description="Aisle identifier")
    department_id: Series[int] = pa.Field(ge=1, description="Department identifier")


class AislesSchema(BaseInstacartSchema):
    """Schema for aisles.csv data."""
    
    aisle_id: Series[int] = pa.Field(ge=1, unique=True, description="Unique aisle identifier")
    aisle: Series[str] = pa.Field(str_length={"min_val": 1}, description="Aisle name")


class DepartmentsSchema(BaseInstacartSchema):
    """Schema for departments.csv data."""
    
    department_id: Series[int] = pa.Field(ge=1, unique=True, description="Unique department identifier")
    department: Series[str] = pa.Field(str_length={"min_val": 1}, description="Department name")


class OrderProductsSchema(BaseInstacartSchema):
    """Schema for order_products__*.csv data."""
    
    order_id: Series[int] = pa.Field(ge=1, description="Order identifier")
    product_id: Series[int] = pa.Field(ge=1, description="Product identifier")
    add_to_cart_order: Series[int] = pa.Field(ge=1, description="Order in which product was added to cart")
    reordered: Series[int] = pa.Field(isin=[0, 1], description="1 if reordered, 0 if not")


def validate_instacart_data(df: pd.DataFrame, schema_class: type, filename: str = "") -> tuple[pd.DataFrame, list[str]]:
    """Validate Instacart DataFrame against schema.
    
    Args:
        df: DataFrame to validate
        schema_class: Pandera schema class
        filename: Optional filename for error context
        
    Returns:
        Tuple of (validated_df, list_of_errors)
    """
    errors = []
    
    try:
        # Validate with schema
        validated_df = schema_class.validate(df, lazy=True)
        
        # Additional business logic checks
        if "order_id" in df.columns:
            if df["order_id"].duplicated().any():
                errors.append("Duplicate order_id values found")
        
        if "product_id" in df.columns and "product_name" in df.columns:
            # Check for products with same ID but different names
            product_consistency = df.groupby("product_id")["product_name"].nunique()
            inconsistent = product_consistency[product_consistency > 1]
            if len(inconsistent) > 0:
                errors.append(f"Inconsistent product names for {len(inconsistent)} product IDs")
        
        return validated_df, errors
        
    except pa.errors.SchemaErrors as e:
        # Handle multiple validation errors
        for error in e.schema_errors:
            errors.append(f"{filename}: {error}")
        return df, errors
    except pa.errors.SchemaError as e:
        errors.append(f"{filename}: {str(e)}")
        return df, errors
    except Exception as e:
        errors.append(f"{filename}: Unexpected validation error: {str(e)}")
        return df, errors


def get_validation_summary(df: pd.DataFrame, schema_class: type) -> dict:
    """Get validation summary for a DataFrame.
    
    Args:
        df: DataFrame to analyze
        schema_class: Schema class used for validation
        
    Returns:
        Dictionary with validation summary
    """
    _, errors = validate_instacart_data(df, schema_class)
    
    return {
        "schema": schema_class.__name__,
        "rows": len(df),
        "columns": len(df.columns),
        "errors": len(errors),
        "error_details": errors,
        "missing_values": df.isnull().sum().to_dict(),
        "data_types": df.dtypes.to_dict()
    }


# Schema mapping for different Instacart files
INSTACART_SCHEMAS = {
    "orders.csv": OrdersSchema,
    "products.csv": ProductsSchema,
    "aisles.csv": AislesSchema, 
    "departments.csv": DepartmentsSchema,
    "order_products__prior.csv": OrderProductsSchema,
    "order_products__train.csv": OrderProductsSchema,
}

# Cleaned data schemas (same structure but lowercase columns)
CLEANED_SCHEMAS = {
    "cleaned_orders.csv": OrdersSchema,
    "cleaned_products.csv": ProductsSchema,
    "cleaned_aisles.csv": AislesSchema,
    "cleaned_departments.csv": DepartmentsSchema,
    "cleaned_order_products__prior.csv": OrderProductsSchema,
}