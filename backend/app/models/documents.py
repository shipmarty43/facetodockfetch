"""Document-related models."""
from pydantic import BaseModel, Field
from typing import Optional, List, Literal
from datetime import datetime


class DocumentUploadResponse(BaseModel):
    """Response after document upload."""
    document_id: int
    file_hash: str
    original_filename: str
    processing_status: str
    message: str


class DocumentResponse(BaseModel):
    """Document metadata response."""
    id: int
    file_hash: str
    original_filename: str
    file_type: str
    file_size_bytes: int
    uploaded_by: int
    uploaded_at: datetime
    processing_status: str
    version_number: int
    page_count: Optional[int]
    has_mrz: bool

    class Config:
        from_attributes = True


class DocumentDetailResponse(DocumentResponse):
    """Detailed document response with OCR and faces."""
    ocr_text: Optional[str]
    mrz_data: Optional[dict]
    faces: List[dict]
    processing_failures: List[dict]


class OCRResultResponse(BaseModel):
    """OCR result response."""
    full_text: Optional[str]
    structured_data: Optional[dict]
    language_detected: Optional[str]
    confidence_score: Optional[float]
    processing_time_seconds: Optional[float]


class MRZDataResponse(BaseModel):
    """MRZ data response."""
    document_type: Optional[str]
    document_number: Optional[str]
    country_code: Optional[str]
    surname: Optional[str]
    given_names: Optional[str]
    nationality: Optional[str]
    date_of_birth: Optional[str]
    sex: Optional[str]
    expiry_date: Optional[str]
    checksum_valid: Optional[bool]


class FaceResponse(BaseModel):
    """Face metadata response."""
    id: int
    document_id: int
    face_image_path: Optional[str]
    bbox: Optional[dict]
    quality_score: Optional[float]
    embedding_id: Optional[str]

    class Config:
        from_attributes = True


class DocumentFilter(BaseModel):
    """Document filter parameters."""
    file_type: Optional[Literal["pdf", "jpg", "png"]] = None
    processing_status: Optional[Literal["pending", "processing", "completed", "failed", "requires_review"]] = None
    has_mrz: Optional[bool] = None
    uploaded_by: Optional[int] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    page: int = Field(1, ge=1)
    page_size: int = Field(50, ge=10, le=200)


class DocumentListResponse(BaseModel):
    """Paginated document list response."""
    total: int
    page: int
    page_size: int
    documents: List[DocumentResponse]


class BatchIndexRequest(BaseModel):
    """Batch indexing request."""
    directory_path: str
    recursive: bool = True
    file_types: List[str] = ["pdf", "jpg", "png"]
