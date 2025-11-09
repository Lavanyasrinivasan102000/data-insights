"""Data editing routes."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database.connection import get_db
from app.models.catalog import Catalog, File as FileModel
from app.services.data_editor import data_editor
from pydantic import BaseModel
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/data", tags=["data-edit"])


class UpdateRowRequest(BaseModel):
    """Request to update a single row."""
    table_name: str
    row_id: int
    updates: Dict[str, Any]


class InsertRowRequest(BaseModel):
    """Request to insert a new row."""
    table_name: str
    data: Dict[str, Any]


class DeleteRowRequest(BaseModel):
    """Request to delete a row."""
    table_name: str
    row_id: int


class AIBatchEditRequest(BaseModel):
    """Request for AI-driven batch edit."""
    table_name: str
    instruction: str
    user_id: str


@router.post("/update-row")
async def update_row(request: UpdateRowRequest, db: Session = Depends(get_db)):
    """Update a single row."""
    logger.info(f"Update row request for table {request.table_name}, row {request.row_id}")

    result = data_editor.update_row(
        table_name=request.table_name,
        row_id=request.row_id,
        updates=request.updates
    )

    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error", "Update failed"))

    return result


@router.post("/insert-row")
async def insert_row(request: InsertRowRequest, db: Session = Depends(get_db)):
    """Insert a new row."""
    logger.info(f"Insert row request for table {request.table_name}")

    result = data_editor.insert_row(
        table_name=request.table_name,
        data=request.data
    )

    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error", "Insert failed"))

    return result


@router.post("/delete-row")
async def delete_row(request: DeleteRowRequest, db: Session = Depends(get_db)):
    """Delete a row."""
    logger.info(f"Delete row request for table {request.table_name}, row {request.row_id}")

    result = data_editor.delete_row(
        table_name=request.table_name,
        row_id=request.row_id
    )

    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error", "Delete failed"))

    return result


@router.post("/ai-batch-edit")
async def ai_batch_edit(request: AIBatchEditRequest, db: Session = Depends(get_db)):
    """Execute AI-driven batch edit based on natural language instruction."""
    logger.info(f"AI batch edit request: {request.instruction}")

    # Get catalog for context
    file_record = db.query(FileModel).filter(
        FileModel.file_id == request.table_name,
        FileModel.user_id == request.user_id
    ).first()

    if not file_record:
        raise HTTPException(status_code=404, detail="Table not found")

    catalog = db.query(Catalog).filter(Catalog.file_id == request.table_name).first()
    catalog_summary = catalog.summary if catalog else "No catalog available"

    result = data_editor.ai_batch_edit(
        table_name=request.table_name,
        user_instruction=request.instruction,
        catalog_summary=catalog_summary
    )

    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error", "Batch edit failed"))

    return result
