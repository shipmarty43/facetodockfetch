"""Admin-related models."""
from pydantic import BaseModel
from typing import Optional, Dict, List
from datetime import datetime


class SystemStats(BaseModel):
    """System statistics."""
    total_documents: int
    total_faces: int
    total_users: int
    documents_by_status: Dict[str, int]
    documents_by_type: Dict[str, int]
    storage_size_bytes: int
    database_size_bytes: int
    recent_activity: List[dict]


class TaskQueueStatus(BaseModel):
    """Celery task queue status."""
    active_tasks: int
    pending_tasks: int
    failed_tasks: int
    workers_online: int


class ReindexRequest(BaseModel):
    """Reindex request."""
    reindex_type: str = "full"  # full, failed_only, date_range
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    components: List[str] = ["ocr", "faces"]  # What to reindex


class ReindexResponse(BaseModel):
    """Reindex response."""
    task_id: str
    message: str
    estimated_documents: int


class LogEntry(BaseModel):
    """System log entry."""
    id: int
    level: str
    user_id: Optional[int]
    action: str
    details: Optional[dict]
    ip_address: Optional[str]
    created_at: datetime


class LogsResponse(BaseModel):
    """Logs response."""
    total: int
    page: int
    page_size: int
    logs: List[LogEntry]
