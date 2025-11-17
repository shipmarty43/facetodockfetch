"""Search service combining face recognition and text search."""
import logging
import base64
import time
from typing import List, Dict, Any
from pathlib import Path
from sqlalchemy.orm import Session
from .face_recognition import face_recognition_service
from .elasticsearch_service import elasticsearch_service
from ..database import Document, Face, MRZData, OCRResult
from ..utils.security import calculate_string_hash

logger = logging.getLogger(__name__)


class SearchService:
    """Service for searching faces and documents."""

    def search_by_face(
        self,
        db: Session,
        image_base64: str,
        similarity_threshold: float = 0.6,
        max_results: int = 10
    ) -> Dict[str, Any]:
        """
        Search for similar faces in the database.

        Args:
            db: Database session
            image_base64: Base64 encoded query image
            similarity_threshold: Minimum similarity (0-1)
            max_results: Maximum number of results

        Returns:
            Dict with search results
        """
        start_time = time.time()

        try:
            # Decode base64 image
            image_data = base64.b64decode(image_base64)

            # Save temporary file
            query_hash = calculate_string_hash(image_base64)
            temp_path = f"/tmp/query_{query_hash}.jpg"
            with open(temp_path, "wb") as f:
                f.write(image_data)

            # Extract face embedding from query image
            query_embedding = face_recognition_service.get_embedding_from_image(temp_path)

            if query_embedding is None:
                return {
                    "query_image_hash": query_hash,
                    "similarity_threshold": similarity_threshold,
                    "results_count": 0,
                    "execution_time_seconds": time.time() - start_time,
                    "results": [],
                    "error": "No face detected in query image"
                }

            # Search in Elasticsearch
            es_results = elasticsearch_service.search_similar_faces(
                query_embedding,
                similarity_threshold,
                max_results
            )

            # Get document details for each result
            results = []
            for es_result in es_results:
                # Get face from database
                face = db.query(Face).filter(Face.id == es_result["face_id"]).first()
                if not face:
                    continue

                # Get document
                document = db.query(Document).filter(Document.id == face.document_id).first()
                if not document:
                    continue

                # Get MRZ data if available
                mrz_data = None
                if document.has_mrz:
                    mrz = db.query(MRZData).filter(MRZData.document_id == document.id).first()
                    if mrz:
                        mrz_data = {
                            "document_type": mrz.document_type,
                            "document_number": mrz.document_number,
                            "surname": mrz.surname,
                            "given_names": mrz.given_names,
                            "date_of_birth": mrz.date_of_birth,
                            "nationality": mrz.nationality
                        }

                results.append({
                    "document_id": document.id,
                    "face_id": face.id,
                    "similarity_score": es_result["similarity_score"],
                    "document_info": {
                        "filename": document.original_filename,
                        "file_type": document.file_type,
                        "uploaded_at": document.uploaded_at.isoformat()
                    },
                    "face_bbox": {
                        "x": face.bbox_x,
                        "y": face.bbox_y,
                        "width": face.bbox_width,
                        "height": face.bbox_height
                    } if face.bbox_x is not None else None,
                    "mrz_data": mrz_data
                })

            # Clean up temp file
            Path(temp_path).unlink(missing_ok=True)

            execution_time = time.time() - start_time

            return {
                "query_image_hash": query_hash,
                "similarity_threshold": similarity_threshold,
                "results_count": len(results),
                "execution_time_seconds": execution_time,
                "results": results
            }

        except Exception as e:
            logger.error(f"Face search failed: {e}")
            return {
                "query_image_hash": "",
                "similarity_threshold": similarity_threshold,
                "results_count": 0,
                "execution_time_seconds": time.time() - start_time,
                "results": [],
                "error": str(e)
            }

    def search_by_text(
        self,
        db: Session,
        query: str,
        search_in: str = "all",
        max_results: int = 20
    ) -> Dict[str, Any]:
        """
        Full-text search in documents.

        Args:
            db: Database session
            query: Search query
            search_in: Where to search (all, ocr, mrz)
            max_results: Maximum results

        Returns:
            Dict with search results
        """
        start_time = time.time()

        try:
            # Search in Elasticsearch
            es_results = elasticsearch_service.search_documents_text(
                query,
                search_in,
                max_results
            )

            # Get document details
            results = []
            for es_result in es_results:
                document = db.query(Document).filter(
                    Document.id == es_result["document_id"]
                ).first()

                if not document:
                    continue

                results.append({
                    "document_id": document.id,
                    "score": es_result["score"],
                    "highlight": es_result.get("highlight"),
                    "document_info": {
                        "filename": document.original_filename,
                        "file_type": document.file_type,
                        "uploaded_at": document.uploaded_at.isoformat(),
                        "has_mrz": document.has_mrz
                    }
                })

            execution_time = time.time() - start_time

            return {
                "query": query,
                "results_count": len(results),
                "execution_time_seconds": execution_time,
                "results": results
            }

        except Exception as e:
            logger.error(f"Text search failed: {e}")
            return {
                "query": query,
                "results_count": 0,
                "execution_time_seconds": time.time() - start_time,
                "results": [],
                "error": str(e)
            }


# Global search service instance
search_service = SearchService()
