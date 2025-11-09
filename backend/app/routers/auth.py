"""Authentication routes."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database.connection import get_db
from app.models.user import User
from pydantic import BaseModel
import uuid

router = APIRouter(prefix="/api/auth", tags=["auth"])


class SignInResponse(BaseModel):
    """Sign in response model."""
    user_id: str


@router.post("/signin", response_model=SignInResponse)
async def signin(db: Session = Depends(get_db)):
    """Sign in or create new user."""
    # For simplicity, create a new user each time
    # In production, you'd want proper authentication
    user_id = str(uuid.uuid4())
    
    # Check if user exists (optional - for this implementation we create new)
    user = User(user_id=user_id)
    db.add(user)
    db.commit()
    db.refresh(user)
    
    return SignInResponse(user_id=user_id)


@router.get("/me")
async def get_current_user(user_id: str, db: Session = Depends(get_db)):
    """Get current user information."""
    user = db.query(User).filter(User.user_id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return {"user_id": user.user_id, "created_at": user.created_at}

