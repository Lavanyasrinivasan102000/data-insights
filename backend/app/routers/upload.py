"""File upload routes."""
from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database.connection import get_db
from app.models.catalog import File as FileModel
from app.services.data_processor import load_csv, load_json
from app.services.catalog_generator import generate_catalog
from app.services.sql_executor import sql_executor
from app.utils.file_handler import (
    generate_file_id,
    get_file_path,
    save_file
)
from app.utils.validators import validate_file_type
from app.config import settings
from pydantic import BaseModel
from typing import List
import os

router = APIRouter(prefix="/api/upload", tags=["upload"])


class UploadResponse(BaseModel):
    """Upload response model."""
    file_id: str
    filename: str
    status: str
    row_count: int


@router.post("/", response_model=UploadResponse)
async def upload_file(
    user_id: str = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """Upload a file and process it."""
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        logger.info(f"Received upload request for user {user_id}, file: {file.filename}")
        
        # Validate file type
        try:
            file_ext = validate_file_type(file.filename)
            logger.info(f"File type validated: {file_ext}")
        except Exception as e:
            logger.error(f"File type validation failed: {str(e)}")
            raise HTTPException(status_code=400, detail=f"Invalid file type: {str(e)}")
        
        # Read file content
        try:
            content = await file.read()
            file_size = len(content)
            logger.info(f"File read successfully. Size: {file_size} bytes")
        except Exception as e:
            logger.error(f"Error reading file: {str(e)}")
            raise HTTPException(status_code=400, detail=f"Error reading file: {str(e)}")
        
        # Check file size
        if file_size > settings.MAX_FILE_SIZE:
            logger.warning(f"File size {file_size} exceeds maximum {settings.MAX_FILE_SIZE}")
            raise HTTPException(
                status_code=400,
                detail=f"File size ({file_size} bytes) exceeds maximum allowed size of {settings.MAX_FILE_SIZE} bytes ({settings.MAX_FILE_SIZE / 1024 / 1024:.1f} MB)"
            )
        
        # Get next available file index for user
        # We need to find the next file_index that doesn't have a conflicting file_id
        # This handles cases where files were deleted or uploads failed
        existing_files_count = db.query(FileModel).filter(
            FileModel.user_id == user_id
        ).count()
        
        # Start with the count + 1, but check for conflicts
        file_index = existing_files_count + 1
        file_id = generate_file_id(user_id, file_index, file_ext)
        
        # Check if file_id already exists, if so, find next available index
        max_attempts = 100  # Prevent infinite loop
        attempt = 0
        while db.query(FileModel).filter(FileModel.file_id == file_id).first() is not None:
            attempt += 1
            if attempt >= max_attempts:
                # Fallback: use timestamp to make it unique
                import time
                file_index = int(time.time() * 1000)  # Use timestamp as index
                file_id = generate_file_id(user_id, file_index, file_ext)
                logger.warning(f"Could not find available file_index after {max_attempts} attempts, using timestamp-based index: {file_index}")
                break
            file_index += 1
            file_id = generate_file_id(user_id, file_index, file_ext)
            logger.info(f"File ID conflict detected, trying next index: {file_index}")
        
        logger.info(f"Generated file_id: {file_id} (index: {file_index})")
        
        # Save file
        file_path = get_file_path(file_id, file_ext)
        save_file(content, file_path)
        
        # Load data
        try:
            if file_ext == "csv":
                df = load_csv(file_path)
            elif file_ext == "json":
                df = load_json(file_path)
            else:
                raise HTTPException(status_code=400, detail="Unsupported file type")
        except Exception as e:
            # Clean up file on error
            if os.path.exists(file_path):
                os.remove(file_path)
            raise HTTPException(status_code=400, detail=f"Error processing file: {str(e)}")
        
        # Generate catalog
        try:
            logger.info("Generating catalog...")
            catalog_data = generate_catalog(df, file_id)
            logger.info("Catalog generated successfully")
        except Exception as e:
            logger.error(f"Error generating catalog: {str(e)}", exc_info=True)
            # Clean up file on error
            if os.path.exists(file_path):
                os.remove(file_path)
            raise HTTPException(status_code=500, detail=f"Error generating catalog: {str(e)}")
        
        # Create SQL table
        table_name = file_id
        try:
            logger.info(f"Creating SQL table: {table_name}")
            # Check if table already exists and drop it if it does (cleanup from previous failed upload)
            from sqlalchemy import text, inspect
            from app.database.connection import engine
            inspector = inspect(engine)
            if table_name in inspector.get_table_names():
                logger.warning(f"Table {table_name} already exists, dropping it before recreating")
                db.execute(text(f'DROP TABLE IF EXISTS "{table_name}"'))
                db.commit()
            sql_executor.create_table_from_dataframe(df, table_name)
            logger.info("SQL table created successfully")
        except Exception as e:
            logger.error(f"Error creating table: {str(e)}", exc_info=True)
            # Clean up file on error
            if os.path.exists(file_path):
                os.remove(file_path)
            raise HTTPException(status_code=500, detail=f"Error creating table: {str(e)}")
        
        # Save to database
        try:
            # Check if file_id already exists (double-check before inserting)
            existing_file = db.query(FileModel).filter(FileModel.file_id == file_id).first()
            if existing_file:
                logger.error(f"File ID {file_id} already exists in database. This should not happen after conflict check.")
                # Clean up file on error
                if os.path.exists(file_path):
                    os.remove(file_path)
                raise HTTPException(
                    status_code=409,
                    detail=f"A file with ID {file_id} already exists. Please try uploading again or delete the existing file first."
                )
            
            file_record = FileModel(
                file_id=file_id,
                user_id=user_id,
                original_filename=file.filename,
                file_type=file_ext,
                file_path=file_path,
                row_count=len(df)
            )
            db.add(file_record)
            
            # Save catalog to database
            # Check if catalog already exists and delete it if it does
            from app.models.catalog import Catalog
            existing_catalog = db.query(Catalog).filter(Catalog.file_id == file_id).first()
            if existing_catalog:
                logger.warning(f"Catalog for file_id {file_id} already exists, deleting it")
                db.delete(existing_catalog)
            
            catalog_record = Catalog(
                file_id=file_id,
                summary=catalog_data["summary"],
                metadata_json=catalog_data["metadata"]
            )
            db.add(catalog_record)
            
            db.commit()
            db.refresh(file_record)
            logger.info(f"File and catalog saved to database. File ID: {file_id}")
        except HTTPException:
            # Re-raise HTTP exceptions
            raise
        except Exception as e:
            logger.error(f"Error saving to database: {str(e)}", exc_info=True)
            db.rollback()
            # Clean up file on error
            if os.path.exists(file_path):
                os.remove(file_path)
            # Check if it's a unique constraint error
            if "UNIQUE constraint failed" in str(e) or "IntegrityError" in str(e):
                raise HTTPException(
                    status_code=409,
                    detail=f"A file with this ID already exists. This might happen if a previous upload was interrupted. Please try uploading again with a different filename or delete the existing file first."
                )
            raise HTTPException(status_code=500, detail=f"Error saving to database: {str(e)}")
        
        logger.info(f"Upload successful. File ID: {file_id}, Rows: {len(df)}")
        return UploadResponse(
            file_id=file_id,
            filename=file.filename,
            status="uploaded",
            row_count=len(df)
        )
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.error(f"Unexpected error during file upload: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")


@router.get("/user/{user_id}")
async def list_user_files(user_id: str, db: Session = Depends(get_db)):
    """List all files for a user."""
    files = db.query(FileModel).filter(FileModel.user_id == user_id).all()

    return [
        {
            "file_id": f.file_id,
            "filename": f.original_filename,
            "file_type": f.file_type,
            "row_count": f.row_count,
            "created_at": f.created_at
        }
        for f in files
    ]


@router.get("/{file_id}")
async def get_file_info(file_id: str, db: Session = Depends(get_db)):
    """Get file information."""
    file_record = db.query(FileModel).filter(FileModel.file_id == file_id).first()
    if not file_record:
        raise HTTPException(status_code=404, detail="File not found")

    return {
        "file_id": file_record.file_id,
        "filename": file_record.original_filename,
        "file_type": file_record.file_type,
        "row_count": file_record.row_count,
        "created_at": file_record.created_at
    }


@router.delete("/{file_id}")
async def delete_file(file_id: str, db: Session = Depends(get_db)):
    """Delete a file and its associated catalog and SQL table."""
    from app.models.catalog import Catalog
    from sqlalchemy import text
    import logging

    logger = logging.getLogger(__name__)

    # Find file record
    file_record = db.query(FileModel).filter(FileModel.file_id == file_id).first()
    if not file_record:
        raise HTTPException(status_code=404, detail="File not found")

    # Delete SQL table (handle both with and without prefixes)
    table_names_to_try = [
        file_id,
        f"base.{file_id}",
        f"main.{file_id}"
    ]

    for table_name in table_names_to_try:
        try:
            # Use double quotes to handle table names with dots
            db.execute(text(f'DROP TABLE IF EXISTS "{table_name}"'))
            logger.info(f"Attempted to drop table: {table_name}")
        except Exception as e:
            logger.warning(f"Could not drop table {table_name}: {str(e)}")

    db.commit()

    # Delete catalog record
    catalog_record = db.query(Catalog).filter(Catalog.file_id == file_id).first()
    if catalog_record:
        db.delete(catalog_record)

    # Delete file record
    db.delete(file_record)
    db.commit()

    # Delete physical files
    if os.path.exists(file_record.file_path):
        try:
            os.remove(file_record.file_path)
            logger.info(f"Deleted file: {file_record.file_path}")
        except Exception as e:
            logger.warning(f"Could not delete file {file_record.file_path}: {str(e)}")

    # Delete catalog text file
    from app.utils.file_handler import get_catalog_path
    catalog_path = get_catalog_path(file_id)
    if os.path.exists(catalog_path):
        try:
            os.remove(catalog_path)
            logger.info(f"Deleted catalog: {catalog_path}")
        except Exception as e:
            logger.warning(f"Could not delete catalog {catalog_path}: {str(e)}")

    return {
        "message": "File and catalog deleted successfully",
        "file_id": file_id
    }

