"""Document management routes."""
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session
from typing import List, Optional
import shutil
from pathlib import Path
from datetime import datetime
from ..database import get_db, Document, OCRResult, MRZData, Face, User
from ..models.documents import (
    DocumentUploadResponse,
    DocumentResponse,
    DocumentDetailResponse,
    DocumentFilter,
    DocumentListResponse,
    BatchIndexRequest
)
from ..dependencies import get_current_user, require_admin
from ..utils.security import calculate_file_hash, sanitize_filename
from ..tasks.document_processing import process_document_task, batch_process_documents
from ..config import settings
from ..utils.logging import log_to_database
import logging

router = APIRouter(prefix="/documents", tags=["Documents"])
logger = logging.getLogger(__name__)


@router.post("/upload", response_model=DocumentUploadResponse)
async def upload_document(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Upload a document for processing.

    Supported formats: PDF, JPG, PNG
    """
    # Validate file type
    file_ext = Path(file.filename).suffix.lower()
    if file_ext not in [".pdf", ".jpg", ".jpeg", ".png"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid file type. Supported: PDF, JPG, PNG"
        )

    # Check file size
    file.file.seek(0, 2)  # Seek to end
    file_size = file.file.tell()
    file.file.seek(0)  # Reset to beginning

    if file_size > settings.max_upload_size_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File too large. Maximum size: {settings.MAX_UPLOAD_SIZE_MB}MB"
        )

    # Save file
    filename = sanitize_filename(file.filename)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_filename = f"{timestamp}_{filename}"
    file_path = Path(settings.UPLOAD_DIR) / safe_filename

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # Calculate file hash
    file_hash = calculate_file_hash(str(file_path))

    # Check for duplicates
    existing_doc = db.query(Document).filter(Document.file_hash == file_hash).first()
    if existing_doc:
        # Remove the duplicate file we just saved
        file_path.unlink()

        log_to_database(
            db,
            "INFO",
            "document_duplicate_detected",
            {"document_id": existing_doc.id, "filename": filename, "original_upload": existing_doc.original_filename},
            user_id=current_user.id
        )

        return {
            "document_id": existing_doc.id,
            "file_hash": existing_doc.file_hash,
            "original_filename": existing_doc.original_filename,
            "processing_status": existing_doc.processing_status,
            "message": f"Document already exists (uploaded as '{existing_doc.original_filename}'). Returning existing document.",
            "is_duplicate": True
        }

    # Create document record (only for new files)
    document = Document(
        file_hash=file_hash,
        original_filename=filename,
        file_path=str(file_path),
        file_type=file_ext.lstrip("."),
        file_size_bytes=file_size,
        uploaded_by=current_user.id,
        processing_status="pending",
        version_number=1,
        parent_document_id=None
    )

    db.add(document)
    db.commit()
    db.refresh(document)

    # Queue for processing (with fallback to synchronous if Celery unavailable)
    processing_mode = "async"
    try:
        process_document_task.delay(document.id)
    except Exception as e:
        # Celery/Redis not available - process synchronously
        logger.warning(f"Celery unavailable ({str(e)}), processing document synchronously")
        processing_mode = "sync"
        try:
            # Call the task function directly (bypassing Celery)
            from ..tasks.document_processing import process_document_sync
            process_document_sync(document.id)
        except Exception as proc_error:
            logger.error(f"Synchronous processing failed: {proc_error}", exc_info=True)
            document.processing_status = "failed"
            db.commit()

    log_to_database(
        db,
        "INFO",
        "document_uploaded",
        {"document_id": document.id, "filename": filename, "processing_mode": processing_mode},
        user_id=current_user.id
    )

    return {
        "document_id": document.id,
        "file_hash": file_hash,
        "original_filename": filename,
        "processing_status": document.processing_status,
        "message": "Document uploaded and queued for processing",
        "is_duplicate": False
    }


@router.get("", response_model=DocumentListResponse)
def list_documents(
    page: int = 1,
    page_size: int = 50,
    file_type: Optional[str] = None,
    processing_status: Optional[str] = None,
    has_mrz: Optional[bool] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    List all documents with filtering and pagination.
    """
    query = db.query(Document)

    # Apply filters
    if file_type:
        query = query.filter(Document.file_type == file_type)
    if processing_status:
        query = query.filter(Document.processing_status == processing_status)
    if has_mrz is not None:
        query = query.filter(Document.has_mrz == has_mrz)

    # Get total count
    total = query.count()

    # Apply pagination
    documents = query.order_by(Document.uploaded_at.desc()).offset(
        (page - 1) * page_size
    ).limit(page_size).all()

    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "documents": documents
    }


@router.get("/{document_id}", response_model=DocumentDetailResponse)
def get_document(
    document_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get detailed document information."""
    document = db.query(Document).filter(Document.id == document_id).first()

    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )

    # Get OCR result
    ocr_text = None
    ocr = db.query(OCRResult).filter(OCRResult.document_id == document_id).first()
    if ocr:
        ocr_text = ocr.full_text

    # Get MRZ data
    mrz_data = None
    if document.has_mrz:
        mrz = db.query(MRZData).filter(MRZData.document_id == document_id).first()
        if mrz:
            mrz_data = {
                "document_type": mrz.document_type,
                "document_number": mrz.document_number,
                "country_code": mrz.country_code,
                "surname": mrz.surname,
                "given_names": mrz.given_names,
                "nationality": mrz.nationality,
                "date_of_birth": mrz.date_of_birth,
                "sex": mrz.sex,
                "expiry_date": mrz.expiry_date,
                "checksum_valid": mrz.checksum_valid
            }

    # Get faces
    faces = db.query(Face).filter(Face.document_id == document_id).all()
    faces_data = [
        {
            "id": face.id,
            "bbox": {
                "x": face.bbox_x,
                "y": face.bbox_y,
                "width": face.bbox_width,
                "height": face.bbox_height
            } if face.bbox_x is not None else None,
            "quality_score": face.quality_score
        }
        for face in faces
    ]

    return {
        **document.__dict__,
        "ocr_text": ocr_text,
        "mrz_data": mrz_data,
        "faces": faces_data,
        "processing_failures": []
    }


@router.delete("/{document_id}")
def delete_document(
    document_id: int,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    Delete a document (admin only).

    Cascades to all related data.
    """
    document = db.query(Document).filter(Document.id == document_id).first()

    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )

    # Delete from Elasticsearch
    from ..services.elasticsearch_service import elasticsearch_service

    # Delete face embeddings
    faces = db.query(Face).filter(Face.document_id == document_id).all()
    for face in faces:
        elasticsearch_service.delete_face_embedding(face.id)

    # Delete document text
    elasticsearch_service.delete_document_text(document_id)

    # Delete file
    file_path = Path(document.file_path)
    if file_path.exists():
        file_path.unlink()

    # Delete from database (cascades automatically)
    db.delete(document)
    db.commit()

    log_to_database(
        db,
        "INFO",
        "document_deleted",
        {"document_id": document_id},
        user_id=current_user.id
    )

    return {"message": "Document deleted successfully"}


@router.post("/index-directory")
def index_directory(
    request: BatchIndexRequest,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    Index all documents in a directory (admin only).
    """
    directory = Path(request.directory_path)

    if not directory.exists() or not directory.is_dir():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid directory path"
        )

    # Find all files
    patterns = [f"*.{ft}" for ft in request.file_types]
    files = []

    if request.recursive:
        for pattern in patterns:
            files.extend(directory.rglob(pattern))
    else:
        for pattern in patterns:
            files.extend(directory.glob(pattern))

    # Queue documents for processing
    document_ids = []

    for file_path in files:
        # Similar logic to upload_document
        file_hash = calculate_file_hash(str(file_path))

        # Check if already indexed
        existing = db.query(Document).filter(Document.file_hash == file_hash).first()
        if existing:
            continue

        # Create document record
        document = Document(
            file_hash=file_hash,
            original_filename=file_path.name,
            file_path=str(file_path),
            file_type=file_path.suffix.lstrip(".").lower(),
            file_size_bytes=file_path.stat().st_size,
            uploaded_by=current_user.id,
            processing_status="pending"
        )

        db.add(document)
        db.flush()
        document_ids.append(document.id)

    db.commit()

    # Queue batch processing
    batch_process_documents.delay(document_ids)

    log_to_database(
        db,
        "INFO",
        "batch_index_started",
        {"directory": request.directory_path, "document_count": len(document_ids)},
        user_id=current_user.id
    )

    return {
        "message": f"Queued {len(document_ids)} documents for processing",
        "document_count": len(document_ids)
    }
