"""Admin routes."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from ..database import get_db, User, Document, Face, SystemLog
from ..models.admin import SystemStats, TaskQueueStatus, ReindexRequest, ReindexResponse, LogsResponse
from ..models.auth import UserCreate, UserUpdate, UserResponse
from ..dependencies import require_admin
from ..utils.security import hash_password
from ..utils.logging import log_to_database
from pathlib import Path
import logging

router = APIRouter(prefix="/admin", tags=["Admin"])
logger = logging.getLogger(__name__)


@router.get("/stats", response_model=SystemStats)
def get_system_stats(
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Get system statistics (admin only)."""
    # Count totals
    total_documents = db.query(Document).count()
    total_faces = db.query(Face).count()
    total_users = db.query(User).count()

    # Documents by status
    from sqlalchemy import func
    docs_by_status = db.query(
        Document.processing_status,
        func.count(Document.id)
    ).group_by(Document.processing_status).all()

    docs_by_status_dict = {status: count for status, count in docs_by_status}

    # Documents by type
    docs_by_type = db.query(
        Document.file_type,
        func.count(Document.id)
    ).group_by(Document.file_type).all()

    docs_by_type_dict = {ftype: count for ftype, count in docs_by_type}

    # Calculate storage sizes
    from ..config import settings
    upload_dir = Path(settings.UPLOAD_DIR)
    storage_size = sum(f.stat().st_size for f in upload_dir.rglob('*') if f.is_file())

    db_path = Path(settings.DATABASE_URL.replace("sqlite:///", ""))
    db_size = db_path.stat().st_size if db_path.exists() else 0

    # Recent activity
    recent_logs = db.query(SystemLog).order_by(
        SystemLog.created_at.desc()
    ).limit(10).all()

    recent_activity = [
        {
            "timestamp": log.created_at.isoformat(),
            "action": log.action,
            "user_id": log.user_id,
            "level": log.level
        }
        for log in recent_logs
    ]

    return {
        "total_documents": total_documents,
        "total_faces": total_faces,
        "total_users": total_users,
        "documents_by_status": docs_by_status_dict,
        "documents_by_type": docs_by_type_dict,
        "storage_size_bytes": storage_size,
        "database_size_bytes": db_size,
        "recent_activity": recent_activity
    }


@router.get("/tasks", response_model=TaskQueueStatus)
def get_task_queue_status(
    current_user: User = Depends(require_admin)
):
    """Get Celery task queue status (admin only)."""
    try:
        from ..celery_app import celery_app

        # Get active tasks
        inspect = celery_app.control.inspect()
        active_tasks = inspect.active()
        scheduled_tasks = inspect.scheduled()
        reserved_tasks = inspect.reserved()

        active_count = sum(len(tasks) for tasks in (active_tasks or {}).values())
        pending_count = sum(len(tasks) for tasks in (reserved_tasks or {}).values())

        # Count workers
        stats = inspect.stats()
        workers_online = len(stats) if stats else 0

        return {
            "active_tasks": active_count,
            "pending_tasks": pending_count,
            "failed_tasks": 0,  # Would need Redis inspection for this
            "workers_online": workers_online
        }

    except Exception as e:
        logger.error(f"Failed to get task status: {e}")
        return {
            "active_tasks": 0,
            "pending_tasks": 0,
            "failed_tasks": 0,
            "workers_online": 0
        }


@router.post("/reindex", response_model=ReindexResponse)
def reindex_database(
    request: ReindexRequest,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Start database reindexing (admin only)."""
    # Get documents to reindex
    query = db.query(Document)

    if request.reindex_type == "failed_only":
        query = query.filter(Document.processing_status == "failed")
    elif request.reindex_type == "date_range":
        if request.date_from:
            query = query.filter(Document.uploaded_at >= request.date_from)
        if request.date_to:
            query = query.filter(Document.uploaded_at <= request.date_to)

    documents = query.all()
    document_ids = [doc.id for doc in documents]

    # Queue for reprocessing
    from ..tasks.document_processing import batch_process_documents
    task = batch_process_documents.delay(document_ids)

    log_to_database(
        db,
        "INFO",
        "reindex_started",
        {
            "reindex_type": request.reindex_type,
            "document_count": len(document_ids),
            "task_id": task.id
        },
        user_id=current_user.id
    )

    return {
        "task_id": task.id,
        "message": f"Reindexing {len(document_ids)} documents",
        "estimated_documents": len(document_ids)
    }


@router.get("/users", response_model=List[UserResponse])
def list_users(
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """List all users (admin only)."""
    users = db.query(User).all()
    return users


@router.post("/users", response_model=UserResponse)
def create_user(
    user_data: UserCreate,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Create a new user (admin only)."""
    # Check if username exists
    existing = db.query(User).filter(User.username == user_data.username).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already exists"
        )

    # Create user
    user = User(
        username=user_data.username,
        password_hash=hash_password(user_data.password),
        role=user_data.role,
        is_active=True
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    log_to_database(
        db,
        "INFO",
        "user_created",
        {"username": user.username, "role": user.role},
        user_id=current_user.id
    )

    return user


@router.put("/users/{user_id}", response_model=UserResponse)
def update_user(
    user_id: int,
    user_data: UserUpdate,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Update user (admin only)."""
    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    # Update fields
    if user_data.password:
        user.password_hash = hash_password(user_data.password)
    if user_data.role:
        user.role = user_data.role
    if user_data.is_active is not None:
        user.is_active = user_data.is_active
    if user_data.settings:
        user.settings_json = user_data.settings

    db.commit()
    db.refresh(user)

    log_to_database(
        db,
        "INFO",
        "user_updated",
        {"user_id": user_id},
        user_id=current_user.id
    )

    return user


@router.delete("/users/{user_id}")
def delete_user(
    user_id: int,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Delete user (admin only)."""
    if user_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete yourself"
        )

    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    db.delete(user)
    db.commit()

    log_to_database(
        db,
        "INFO",
        "user_deleted",
        {"user_id": user_id, "username": user.username},
        user_id=current_user.id
    )

    return {"message": "User deleted successfully"}


@router.get("/logs", response_model=LogsResponse)
def get_logs(
    page: int = 1,
    page_size: int = 50,
    level: str = None,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Get system logs (admin only)."""
    query = db.query(SystemLog)

    if level:
        query = query.filter(SystemLog.level == level.upper())

    total = query.count()

    logs = query.order_by(SystemLog.created_at.desc()).offset(
        (page - 1) * page_size
    ).limit(page_size).all()

    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "logs": [
            {
                "id": log.id,
                "level": log.level,
                "user_id": log.user_id,
                "action": log.action,
                "details": log.details,
                "ip_address": log.ip_address,
                "created_at": log.created_at
            }
            for log in logs
        ]
    }
