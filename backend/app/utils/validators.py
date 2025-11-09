"""Validation utilities."""
from fastapi import UploadFile, HTTPException
from app.config import settings


def validate_file_type(filename: str) -> str:
    """Validate file type and return extension."""
    ext = filename.split(".")[-1].lower()
    if ext not in settings.allowed_file_types_list:
        raise HTTPException(
            status_code=400,
            detail=f"File type '{ext}' not allowed. Allowed types: {settings.ALLOWED_FILE_TYPES}"
        )
    return ext


def validate_file_size(file: UploadFile) -> None:
    """Validate file size."""
    # Note: FastAPI doesn't provide file size before reading
    # This is a placeholder - actual validation happens during upload
    pass

