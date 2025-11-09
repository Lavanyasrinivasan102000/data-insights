"""Catalog generation service."""
from typing import Dict, Any
from app.services.data_processor import (
    get_sample_rows,
    infer_types,
    get_basic_stats
)
from app.services.gemini_service import gemini_service
from app.utils.file_handler import get_catalog_path
import pandas as pd


def generate_catalog(
    df: pd.DataFrame,
    file_id: str
) -> Dict[str, Any]:
    """Generate catalog for a DataFrame."""
    # Get schema information
    types = infer_types(df)
    stats = get_basic_stats(df)
    
    # Get distinct values for categorical columns (important for filtering queries)
    categorical_values = {}
    for col in df.columns:
        if df[col].dtype == 'object' or df[col].dtype.name == 'category':
            # Get unique values, limit to first 20 for display
            unique_vals = df[col].dropna().unique()[:20]
            if len(unique_vals) <= 20:  # Only include if reasonable number of unique values
                categorical_values[col] = sorted([str(v) for v in unique_vals])
    
    # Prepare schema dict
    schema = {
        "columns": stats["columns"],
        "types": types,
        "row_count": stats["row_count"],
        "categorical_values": categorical_values  # Add distinct values for categorical columns
    }
    
    # Get sample rows (10-20)
    sample_size = min(20, len(df))
    sample_rows = get_sample_rows(df, sample_size)
    
    # Generate catalog using Gemini
    catalog_text = gemini_service.generate_catalog(
        schema=schema,
        sample_rows=sample_rows,
        row_count=len(df)
    )
    
    # Prepare metadata
    metadata = {
        "schema": schema,
        "stats": {
            "row_count": stats["row_count"],
            "column_count": stats["column_count"],
            "null_rates": stats["null_rates"],
            "numeric_stats": stats.get("numeric_stats", {}),
            "categorical_cardinality": stats.get("categorical_cardinality", {})
        }
    }
    
    # Save catalog to file
    catalog_path = get_catalog_path(file_id)
    with open(catalog_path, 'w', encoding='utf-8') as f:
        f.write(catalog_text)
    
    return {
        "summary": catalog_text,
        "metadata": metadata
    }

