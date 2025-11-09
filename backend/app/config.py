"""Configuration settings for the application."""

from pydantic_settings import BaseSettings
from typing import List
import os


class Settings(BaseSettings):
    """Application settings."""

    # Gemini API
    GEMINI_API_KEY: str = ""

    # Database
    DATABASE_URL: str = "sqlite:///./rag.db"

    # File Upload
    CATALOG_DIR: str = "./catalog"
    MAX_FILE_SIZE: int = 10485760  # 10MB
    ALLOWED_FILE_TYPES: str = "csv,json"

    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    DEBUG: bool = True

    # CORS
    CORS_ORIGINS: str = "http://localhost:3000,http://localhost:3001"

    # Security
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"

    class Config:
        env_file = ".env"
        case_sensitive = True

    @property
    def allowed_file_types_list(self) -> List[str]:
        """Get list of allowed file types."""
        return [ext.strip() for ext in self.ALLOWED_FILE_TYPES.split(",")]

    @property
    def cors_origins_list(self) -> List[str]:
        """Get list of CORS origins."""
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]


# Create settings instance
settings = Settings()

# Ensure catalog directory exists
os.makedirs(settings.CATALOG_DIR, exist_ok=True)
