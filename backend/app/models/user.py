"""User model."""
from sqlalchemy import Column, String, DateTime
from sqlalchemy.sql import func
from app.database.connection import Base
import uuid


class User(Base):
    """User model."""
    __tablename__ = "users"
    
    user_id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

