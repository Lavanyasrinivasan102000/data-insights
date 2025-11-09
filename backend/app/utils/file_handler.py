"""File handling utilities."""
import os
from pathlib import Path
from typing import Optional
from app.config import settings


def generate_file_id(user_id: str, file_index: int, file_extension: str) -> str:
    """Generate a deterministic file ID."""
    ext = file_extension.lower().replace(".", "")
    # Replace hyphens with underscores for SQL table name compatibility
    sanitized_user_id = user_id.replace("-", "_")
    return f"{sanitized_user_id}_input_file_{file_index}_{ext}"


def get_file_path(file_id: str, file_extension: str) -> str:
    """Get the full file path for a file ID."""
    ext = file_extension.lower().replace(".", "")
    return os.path.join(settings.CATALOG_DIR, f"{file_id}.{ext}")


def get_catalog_path(file_id: str) -> str:
    """Get the catalog text file path."""
    return os.path.join(settings.CATALOG_DIR, f"{file_id}.txt")


def save_file(file_content: bytes, file_path: str) -> None:
    """Save file content to disk."""
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    with open(file_path, "wb") as f:
        f.write(file_content)


def file_exists(file_path: str) -> bool:
    """Check if file exists."""
    return os.path.exists(file_path)

