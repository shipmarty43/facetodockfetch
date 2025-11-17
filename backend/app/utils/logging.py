"""Logging utilities and configuration."""
import logging
import json
from pathlib import Path
from logging.handlers import RotatingFileHandler
from datetime import datetime
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from ..config import settings
from ..database import SystemLog


# Configure Python logging
def setup_logging():
    """Setup application logging."""
    # Create logs directory
    Path("logs").mkdir(exist_ok=True)

    # Configure log level
    log_level = getattr(logging, settings.LOG_LEVEL.upper())

    # Create formatter
    if settings.is_debug:
        # Detailed format for debug
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s'
        )
    else:
        # JSON format for production
        formatter = logging.Formatter(
            '{"timestamp": "%(asctime)s", "level": "%(levelname)s", "logger": "%(name)s", "message": "%(message)s"}'
        )

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)

    # File handler with rotation
    file_handler = RotatingFileHandler(
        settings.LOG_FILE,
        maxBytes=settings.LOG_MAX_SIZE_MB * 1024 * 1024,
        backupCount=settings.LOG_RETENTION_DAYS
    )
    file_handler.setFormatter(formatter)

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    root_logger.addHandler(console_handler)
    root_logger.addHandler(file_handler)

    return root_logger


# Database logging functions
def log_to_database(
    db: Session,
    level: str,
    action: str,
    details: Optional[Dict[str, Any]] = None,
    user_id: Optional[int] = None,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None
):
    """Log event to database."""
    # In production mode, don't log DEBUG level to database
    if settings.is_production and level == "DEBUG":
        return

    log_entry = SystemLog(
        level=level,
        user_id=user_id,
        action=action,
        details=details,
        ip_address=ip_address,
        user_agent=user_agent,
        created_at=datetime.utcnow()
    )

    db.add(log_entry)
    db.commit()


def log_search(
    db: Session,
    user_id: int,
    search_type: str,
    query_image_hash: Optional[str],
    similarity_threshold: float,
    results_count: int,
    execution_time: float
):
    """Log search operation."""
    from ..database import SearchLog

    search_log = SearchLog(
        user_id=user_id,
        search_type=search_type,
        query_image_hash=query_image_hash,
        similarity_threshold=similarity_threshold,
        results_count=results_count,
        execution_time_seconds=execution_time
    )

    db.add(search_log)
    db.commit()


# Initialize logging on module import
logger = setup_logging()
