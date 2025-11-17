"""Celery tasks for document processing."""
import logging
from pathlib import Path
from sqlalchemy.orm import Session
from ..celery_app import celery_app
from ..database import SessionLocal, Document, OCRResult, MRZData, Face, ProcessingFailure
from ..services.ocr_service import ocr_service
from ..services.face_recognition import face_recognition_service
from ..services.elasticsearch_service import elasticsearch_service
from ..config import settings

logger = logging.getLogger(__name__)


@celery_app.task(bind=True, max_retries=3)
def process_document_task(self, document_id: int):
    """
    Process a document: OCR, face detection, indexing.

    Args:
        document_id: ID of document to process
    """
    db = SessionLocal()

    try:
        # Get document
        document = db.query(Document).filter(Document.id == document_id).first()
        if not document:
            logger.error(f"Document not found: {document_id}")
            return

        # Update status to processing
        document.processing_status = "processing"
        db.commit()

        logger.info(f"Processing document {document_id}: {document.original_filename}")

        # Determine file type and process accordingly
        file_path = document.file_path

        # Step 1: OCR Processing
        ocr_result = None
        mrz_data = None

        for attempt in range(1, settings.MAX_RETRIES_OCR + 1):
            logger.info(f"OCR attempt {attempt}/{settings.MAX_RETRIES_OCR}")

            if document.file_type == "pdf":
                ocr_result = ocr_service.extract_text_from_pdf(file_path, attempt)
            else:
                ocr_result = ocr_service.extract_text_from_image(file_path, attempt)

            if ocr_result["success"]:
                # Save OCR result
                ocr_record = OCRResult(
                    document_id=document_id,
                    full_text=ocr_result["full_text"],
                    structured_data=ocr_result["structured_data"],
                    language_detected=ocr_result["language_detected"],
                    confidence_score=ocr_result["confidence_score"],
                    processing_time_seconds=ocr_result["processing_time_seconds"],
                    attempt_number=attempt
                )
                db.add(ocr_record)
                db.commit()

                # Try to extract MRZ
                mrz_data = ocr_service.extract_mrz_zone(file_path)
                if mrz_data:
                    mrz_record = MRZData(
                        document_id=document_id,
                        **mrz_data
                    )
                    db.add(mrz_record)
                    document.has_mrz = True
                    db.commit()

                # Index in Elasticsearch
                elasticsearch_service.index_document_text(
                    document_id,
                    ocr_result["full_text"],
                    mrz_data
                )

                break  # Success, exit retry loop
            else:
                # Save failure
                failure = ProcessingFailure(
                    document_id=document_id,
                    failure_type="ocr_failed",
                    attempt_number=attempt,
                    error_message=ocr_result.get("error", "Unknown error"),
                    stack_trace=None
                )
                db.add(failure)
                db.commit()

        # If all OCR attempts failed
        if not ocr_result or not ocr_result["success"]:
            document.processing_status = "requires_review"
            db.commit()
            logger.warning(f"All OCR attempts failed for document {document_id}")
            # Continue to face detection anyway

        # Step 2: Face Detection and Recognition
        # Convert PDF to images if needed
        image_paths = []
        if document.file_type == "pdf":
            from pdf2image import convert_from_path
            images = convert_from_path(file_path)
            for i, image in enumerate(images):
                temp_path = f"/tmp/doc_{document_id}_page_{i}.jpg"
                image.save(temp_path, "JPEG")
                image_paths.append(temp_path)
        else:
            image_paths = [file_path]

        # Detect faces in all images
        all_faces = []
        for img_path in image_paths:
            faces = face_recognition_service.detect_faces(
                img_path,
                min_confidence=settings.FACE_DETECTION_CONFIDENCE
            )
            all_faces.extend([(img_path, face) for face in faces])

        # Save faces to database and index embeddings
        for img_path, face_data in all_faces:
            # Create face crop directory
            face_crops_dir = Path(settings.UPLOAD_DIR) / "face_crops"
            face_crops_dir.mkdir(exist_ok=True)

            # Save cropped face
            face_crop_path = face_crops_dir / f"doc_{document_id}_face_{face_data['face_index']}.jpg"
            face_recognition_service.extract_face_crop(
                img_path,
                face_data["bbox"],
                str(face_crop_path)
            )

            # Save to database
            face_record = Face(
                document_id=document_id,
                face_image_path=str(face_crop_path),
                bbox_x=face_data["bbox"]["x"],
                bbox_y=face_data["bbox"]["y"],
                bbox_width=face_data["bbox"]["width"],
                bbox_height=face_data["bbox"]["height"],
                quality_score=face_data["quality_score"]
            )
            db.add(face_record)
            db.flush()

            # Index embedding in Elasticsearch
            elasticsearch_service.index_face_embedding(
                face_record.id,
                document_id,
                face_data["embedding"],
                face_data["quality_score"]
            )

            face_record.embedding_id = str(face_record.id)
            db.commit()

        # Clean up temp files
        for img_path in image_paths:
            if "/tmp/" in img_path:
                Path(img_path).unlink(missing_ok=True)

        # Update document status
        if ocr_result and ocr_result["success"]:
            document.processing_status = "completed"
        else:
            document.processing_status = "requires_review"

        document.page_count = len(image_paths)
        db.commit()

        logger.info(f"Document {document_id} processed successfully")

    except Exception as e:
        logger.error(f"Document processing failed: {e}", exc_info=True)

        # Save failure
        try:
            failure = ProcessingFailure(
                document_id=document_id,
                failure_type="processing_error",
                attempt_number=1,
                error_message=str(e),
                stack_trace=None
            )
            db.add(failure)

            document = db.query(Document).filter(Document.id == document_id).first()
            if document:
                document.processing_status = "failed"

            db.commit()
        except:
            pass

    finally:
        db.close()


@celery_app.task
def batch_process_documents(document_ids: list):
    """
    Process multiple documents in batch.

    Args:
        document_ids: List of document IDs to process
    """
    for doc_id in document_ids:
        process_document_task.delay(doc_id)
