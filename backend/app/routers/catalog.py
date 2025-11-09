"""Catalog routes."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database.connection import get_db
from app.models.catalog import Catalog, File as FileModel
from pydantic import BaseModel
from typing import List

router = APIRouter(prefix="/api/catalog", tags=["catalog"])


class CatalogSummary(BaseModel):
    """Catalog summary model."""
    file_id: str
    summary: str


class CatalogListResponse(BaseModel):
    """Catalog list response."""
    catalogs: List[CatalogSummary]


@router.get("/{user_id}", response_model=List[CatalogSummary])
async def get_user_catalogs(user_id: str, db: Session = Depends(get_db)):
    """Retrieve all catalogs for a user."""
    # Get all files for user
    files = db.query(FileModel).filter(FileModel.user_id == user_id).all()
    
    if not files:
        return []
    
    # Get catalogs for these files
    file_ids = [f.file_id for f in files]
    catalogs = db.query(Catalog).filter(Catalog.file_id.in_(file_ids)).all()
    
    # Create catalog map
    catalog_map = {cat.file_id: cat for cat in catalogs}
    
    # Build response
    result = []
    for file in files:
        catalog = catalog_map.get(file.file_id)
        if catalog:
            result.append(CatalogSummary(
                file_id=file.file_id,
                summary=catalog.summary
            ))
    
    return result


@router.get("/file/{file_id}")
async def get_file_catalog(file_id: str, db: Session = Depends(get_db)):
    """Get specific catalog for a file."""
    catalog = db.query(Catalog).filter(Catalog.file_id == file_id).first()
    if not catalog:
        raise HTTPException(status_code=404, detail="Catalog not found")
    
    return {
        "file_id": catalog.file_id,
        "summary": catalog.summary,
        "metadata": catalog.metadata_json,
        "created_at": catalog.created_at
    }

