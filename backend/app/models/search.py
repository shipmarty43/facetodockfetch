"""Search-related models."""
from pydantic import BaseModel, Field
from typing import Optional, List, Literal
from datetime import datetime


class FaceSearchRequest(BaseModel):
    """Face search request."""
    image_base64: str
    similarity_threshold: float = Field(0.6, ge=0.0, le=1.0)
    max_results: int = Field(10, ge=1, le=100)


class FaceSearchResult(BaseModel):
    """Single face search result."""
    document_id: int
    face_id: int
    similarity_score: float
    document_info: dict
    face_bbox: Optional[dict]
    mrz_data: Optional[dict]


class FaceSearchResponse(BaseModel):
    """Face search response."""
    query_image_hash: str
    similarity_threshold: float
    results_count: int
    execution_time_seconds: float
    results: List[FaceSearchResult]


class TextSearchRequest(BaseModel):
    """Text search request."""
    query: str = Field(..., min_length=1)
    search_in: Literal["all", "ocr", "mrz"] = "all"
    max_results: int = Field(20, ge=1, le=100)


class TextSearchResult(BaseModel):
    """Text search result."""
    document_id: int
    score: float
    highlight: Optional[str]
    document_info: dict


class TextSearchResponse(BaseModel):
    """Text search response."""
    query: str
    results_count: int
    execution_time_seconds: float
    results: List[TextSearchResult]
