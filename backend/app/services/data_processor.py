"""Data processing service."""
import pandas as pd
import json
from typing import Dict, List, Any, Optional
from pathlib import Path


def load_csv(file_path: str) -> pd.DataFrame:
    """Load CSV file into pandas DataFrame."""
    try:
        df = pd.read_csv(file_path)
        return df
    except Exception as e:
        raise ValueError(f"Error loading CSV: {str(e)}")


def load_json(file_path: str) -> pd.DataFrame:
    """Load JSON file into pandas DataFrame."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Normalize JSON data
        df = normalize_json_data(data)
        return df
    except Exception as e:
        raise ValueError(f"Error loading JSON: {str(e)}")


def normalize_json_data(data: Any) -> pd.DataFrame:
    """Normalize JSON data to tabular format."""
    if isinstance(data, list):
        # Array of objects
        if len(data) > 0 and isinstance(data[0], dict):
            return pd.json_normalize(data)
        else:
            # Array of primitives
            return pd.DataFrame({"value": data})
    elif isinstance(data, dict):
        # Single object or nested structure
        # Try to normalize - if it's a single object, wrap in list
        normalized = pd.json_normalize([data])
        return normalized
    else:
        # Primitive value
        return pd.DataFrame({"value": [data]})


def get_sample_rows(df: pd.DataFrame, n: int = 20) -> List[Dict[str, Any]]:
    """Get sample rows from DataFrame."""
    sample_size = min(n, len(df))
    sample_df = df.head(sample_size)
    # Replace NaN with None for JSON serialization
    return sample_df.replace({pd.NA: None, pd.NaT: None}).to_dict(orient='records')


def infer_types(df: pd.DataFrame) -> Dict[str, str]:
    """Infer data types for each column."""
    type_mapping = {
        'int64': 'integer',
        'float64': 'float',
        'bool': 'boolean',
        'datetime64[ns]': 'datetime',
        'object': 'string'
    }
    
    inferred = {}
    for col in df.columns:
        dtype = str(df[col].dtype)
        inferred[col] = type_mapping.get(dtype, 'string')
    
    return inferred


def get_basic_stats(df: pd.DataFrame) -> Dict[str, Any]:
    """Get basic statistics for the DataFrame."""
    stats = {
        "row_count": len(df),
        "column_count": len(df.columns),
        "columns": list(df.columns),
        "null_counts": df.isnull().sum().to_dict(),
        "null_rates": (df.isnull().sum() / len(df) * 100).to_dict()
    }
    
    # Numeric statistics
    numeric_cols = df.select_dtypes(include=['number']).columns
    if len(numeric_cols) > 0:
        stats["numeric_stats"] = df[numeric_cols].describe().to_dict()
    
    # Categorical cardinality
    categorical_cols = df.select_dtypes(include=['object']).columns
    if len(categorical_cols) > 0:
        stats["categorical_cardinality"] = {
            col: df[col].nunique() for col in categorical_cols
        }
    
    return stats

