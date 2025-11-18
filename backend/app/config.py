"""
Application configuration module.
Handles environment variables and settings for different modes (debug/production).
"""
from pydantic_settings import BaseSettings
from typing import Literal
import os
from pathlib import Path

# Determine project root (2 levels up from this file: backend/app/config.py -> root)
PROJECT_ROOT = Path(__file__).parent.parent.parent
ENV_FILE = PROJECT_ROOT / ".env"


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Application Mode
    MODE: Literal["debug", "production"] = "debug"

    # Security
    SECRET_KEY: str = "dev-secret-key-change-in-production"
    ENCRYPTION_KEY: str = ""

    # Database (use absolute path to avoid issues with working directory)
    DATABASE_URL: str = f"sqlite:///{PROJECT_ROOT}/data/db/face_recognition.db"

    # Elasticsearch
    ELASTICSEARCH_URL: str = "http://localhost:9200"
    ELASTICSEARCH_INDEX_FACES: str = "face_embeddings"
    ELASTICSEARCH_INDEX_DOCUMENTS: str = "documents_fulltext"

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # Celery
    CELERY_BROKER_URL: str = "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/0"

    # File Storage (use absolute path)
    UPLOAD_DIR: str = str(PROJECT_ROOT / "data" / "uploads")
    MAX_UPLOAD_SIZE_MB: int = 50

    # JWT Settings
    JWT_SECRET_KEY: str = "jwt-secret-key-change-in-production"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # ML Models (use absolute paths)
    FACE_MODEL_PATH: str = str(PROJECT_ROOT / "models" / "face_recognition")
    OCR_MODEL_PATH: str = str(PROJECT_ROOT / "models" / "surya_ocr")
    FACE_DETECTION_CONFIDENCE: float = 0.5
    FACE_SIMILARITY_THRESHOLD: float = 0.6

    # Processing
    CELERY_WORKERS: int = 8
    MAX_RETRIES_OCR: int = 3
    BATCH_SIZE: int = 32

    # GPU/CUDA Settings
    USE_GPU: bool = False
    CUDA_VISIBLE_DEVICES: str = "0"
    PYTORCH_CUDA_ALLOC_CONF: str = "expandable_segments:True"

    # Surya OCR Settings
    DETECTOR_TEXT_THRESHOLD: float = 0.2
    DETECTOR_BATCH_SIZE: int = 8
    RECOGNITION_BATCH_SIZE: int = 15
    LAYOUT_BATCH_SIZE: int = 52

    # Logging (use absolute path)
    LOG_LEVEL: str = "DEBUG"
    LOG_FILE: str = str(PROJECT_ROOT / "logs" / "app.log")
    LOG_MAX_SIZE_MB: int = 100
    LOG_RETENTION_DAYS: int = 30

    # CORS
    CORS_ORIGINS: str = "http://localhost:3003,http://localhost:30000"

    # API
    API_V1_PREFIX: str = "/api/v1"

    class Config:
        env_file = str(ENV_FILE)
        env_file_encoding = 'utf-8'
        case_sensitive = True

    @property
    def is_production(self) -> bool:
        """Check if running in production mode."""
        return self.MODE == "production"

    @property
    def is_debug(self) -> bool:
        """Check if running in debug mode."""
        return self.MODE == "debug"

    @property
    def cors_origins_list(self) -> list[str]:
        """Parse CORS origins into a list."""
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]

    @property
    def max_upload_size_bytes(self) -> int:
        """Convert max upload size to bytes."""
        return self.MAX_UPLOAD_SIZE_MB * 1024 * 1024

    def ensure_directories(self):
        """Create necessary directories if they don't exist."""
        directories = [
            self.UPLOAD_DIR,
            str(PROJECT_ROOT / "data" / "db"),
            str(PROJECT_ROOT / "data" / "cache"),
            str(PROJECT_ROOT / "logs"),
            self.FACE_MODEL_PATH,
            self.OCR_MODEL_PATH,
        ]
        for directory in directories:
            Path(directory).mkdir(parents=True, exist_ok=True)


# Global settings instance
settings = Settings()

# Ensure directories exist on import
settings.ensure_directories()
