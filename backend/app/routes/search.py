"""Search routes."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from ..database import get_db, User
from ..models.search import (
    FaceSearchRequest,
    FaceSearchResponse,
    TextSearchRequest,
    TextSearchResponse
)
from ..dependencies import get_current_user
from ..services.search_service import search_service
from ..utils.logging import log_search
import logging

router = APIRouter(prefix="/search", tags=["Search"])
logger = logging.getLogger(__name__)


@router.post("/face", response_model=FaceSearchResponse)
def search_by_face(
    request: FaceSearchRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Search for faces similar to the uploaded image.

    Upload a base64-encoded image and receive similar faces from the database.
    """
    try:
        # Perform search
        result = search_service.search_by_face(
            db,
            request.image_base64,
            request.similarity_threshold,
            request.max_results
        )

        # Log search
        log_search(
            db,
            user_id=current_user.id,
            search_type="photo",
            query_image_hash=result.get("query_image_hash"),
            similarity_threshold=request.similarity_threshold,
            results_count=result["results_count"],
            execution_time=result["execution_time_seconds"]
        )

        if "error" in result:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result["error"]
            )

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Face search error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Search failed"
        )


@router.post("/text", response_model=TextSearchResponse)
def search_by_text(
    request: TextSearchRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Full-text search in documents.

    Search in OCR text and MRZ data.
    """
    try:
        result = search_service.search_by_text(
            db,
            request.query,
            request.search_in,
            request.max_results
        )

        if "error" in result:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result["error"]
            )

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Text search error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Search failed"
        )
