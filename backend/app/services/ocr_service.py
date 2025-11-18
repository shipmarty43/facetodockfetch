"""OCR service using Surya OCR for text extraction."""
import logging
from typing import Optional, Dict, Any, List
from pathlib import Path
import time
from PIL import Image
from pdf2image import convert_from_path
import os

logger = logging.getLogger(__name__)


class OCRService:
    """Service for OCR operations using Surya OCR."""

    def __init__(self):
        """Initialize OCR service."""
        self.model = None
        self.processor = None
        self._load_model()

    def _load_model(self):
        """Load Surya OCR model."""
        try:
            # Import Surya OCR (lazy import to avoid loading if not needed)
            # Try new API first (surya 0.4+)
            try:
                from surya.model.detection import load_model as load_det_model
                from surya.model.recognition import load_model as load_rec_model
            except ImportError:
                # Fallback to old API
                from surya.model.detection.segformer import load_model as load_det_model
                from surya.model.recognition.model import load_model as load_rec_model

            logger.info("Loading Surya OCR models...")
            # Load detection and recognition models
            self.det_model = load_det_model()
            self.rec_model = load_rec_model()
            logger.info("Surya OCR models loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load Surya OCR models: {e}")
            logger.warning("OCR functionality will be limited")
            self.det_model = None
            self.rec_model = None

    def extract_text_from_image(
        self,
        image_path: str,
        attempt: int = 1
    ) -> Dict[str, Any]:
        """
        Extract text from an image using Surya OCR.

        Args:
            image_path: Path to the image file
            attempt: Attempt number (1-3)

        Returns:
            Dict with OCR results
        """
        start_time = time.time()

        try:
            if self.det_model is None or self.rec_model is None:
                raise Exception("OCR models not loaded")

            # Import OCR function (try both APIs)
            try:
                from surya.ocr import run_ocr
            except ImportError:
                # Try alternative import
                from surya import run_ocr

            # Load image
            image = Image.open(image_path)

            # Run OCR
            logger.info(f"Running OCR on {image_path} (attempt {attempt})")

            # Try to run OCR (API may vary by version)
            try:
                # New API (0.4+)
                predictions = run_ocr([image], [["en", "ru"]], self.det_model, self.rec_model)
            except TypeError:
                # Older API - different parameters
                predictions = run_ocr([image], self.det_model, self.rec_model, langs=[["en", "ru"]])

            # Extract text and structure
            full_text = ""
            structured_data = {
                "blocks": [],
                "languages": []
            }

            if predictions and len(predictions) > 0:
                prediction = predictions[0]

                # Extract text blocks
                for text_line in prediction.text_lines:
                    full_text += text_line.text + "\n"
                    structured_data["blocks"].append({
                        "text": text_line.text,
                        "bbox": text_line.bbox,
                        "confidence": getattr(text_line, 'confidence', 1.0)
                    })

                # Detect languages
                structured_data["languages"] = prediction.languages if hasattr(prediction, 'languages') else ["unknown"]

            processing_time = time.time() - start_time

            return {
                "full_text": full_text.strip(),
                "structured_data": structured_data,
                "language_detected": structured_data["languages"][0] if structured_data["languages"] else "unknown",
                "confidence_score": self._calculate_confidence(structured_data),
                "processing_time_seconds": processing_time,
                "attempt_number": attempt,
                "success": True
            }

        except Exception as e:
            logger.error(f"OCR failed (attempt {attempt}): {e}")
            processing_time = time.time() - start_time

            return {
                "full_text": None,
                "structured_data": None,
                "language_detected": None,
                "confidence_score": 0.0,
                "processing_time_seconds": processing_time,
                "attempt_number": attempt,
                "success": False,
                "error": str(e)
            }

    def _calculate_confidence(self, structured_data: Dict) -> float:
        """Calculate average confidence from OCR results."""
        if not structured_data or not structured_data.get("blocks"):
            return 0.0

        confidences = [block.get("confidence", 0.0) for block in structured_data["blocks"]]
        return sum(confidences) / len(confidences) if confidences else 0.0

    def extract_text_from_pdf(
        self,
        pdf_path: str,
        attempt: int = 1
    ) -> Dict[str, Any]:
        """
        Extract text from a PDF file.

        Args:
            pdf_path: Path to the PDF file
            attempt: Attempt number (1-3)

        Returns:
            Dict with OCR results
        """
        start_time = time.time()

        try:
            # Convert PDF to images
            logger.info(f"Converting PDF to images: {pdf_path}")
            images = convert_from_path(pdf_path)

            all_text = ""
            all_blocks = []
            total_confidence = 0.0
            languages = set()

            # Process each page
            for i, image in enumerate(images):
                logger.info(f"Processing page {i+1}/{len(images)}")

                # Save temporary image
                temp_image_path = f"/tmp/page_{i}.jpg"
                image.save(temp_image_path, "JPEG")

                # Extract text from page
                page_result = self.extract_text_from_image(temp_image_path, attempt)

                if page_result["success"]:
                    all_text += f"\n--- Page {i+1} ---\n" + page_result["full_text"]
                    all_blocks.extend(page_result["structured_data"]["blocks"])
                    total_confidence += page_result["confidence_score"]
                    if page_result["language_detected"]:
                        languages.add(page_result["language_detected"])

                # Clean up temp file
                if os.path.exists(temp_image_path):
                    os.remove(temp_image_path)

            processing_time = time.time() - start_time
            avg_confidence = total_confidence / len(images) if images else 0.0

            return {
                "full_text": all_text.strip(),
                "structured_data": {
                    "blocks": all_blocks,
                    "languages": list(languages),
                    "page_count": len(images)
                },
                "language_detected": list(languages)[0] if languages else "unknown",
                "confidence_score": avg_confidence,
                "processing_time_seconds": processing_time,
                "attempt_number": attempt,
                "success": True
            }

        except Exception as e:
            logger.error(f"PDF OCR failed (attempt {attempt}): {e}")
            processing_time = time.time() - start_time

            return {
                "full_text": None,
                "structured_data": None,
                "language_detected": None,
                "confidence_score": 0.0,
                "processing_time_seconds": processing_time,
                "attempt_number": attempt,
                "success": False,
                "error": str(e)
            }

    def extract_mrz_zone(self, image_path: str) -> Optional[Dict[str, Any]]:
        """
        Detect and extract MRZ (Machine Readable Zone) from document.

        Args:
            image_path: Path to the image

        Returns:
            Dict with MRZ data or None
        """
        try:
            from mrz.checker.td1 import TD1CodeChecker
            from mrz.checker.td2 import TD2CodeChecker
            from mrz.checker.td3 import TD3CodeChecker

            # First, run OCR to get text
            ocr_result = self.extract_text_from_image(image_path)

            if not ocr_result["success"]:
                return None

            full_text = ocr_result["full_text"]

            # Try to find MRZ patterns in the text
            lines = full_text.split('\n')

            # Try different MRZ formats
            for i in range(len(lines)):
                # TD3 (2 lines, 44 chars each) - Passports
                if i + 1 < len(lines):
                    line1 = lines[i].strip()
                    line2 = lines[i + 1].strip()

                    if len(line1) == 44 and len(line2) == 44:
                        try:
                            mrz_code = line1 + '\n' + line2
                            td3_check = TD3CodeChecker(mrz_code)
                            if td3_check.valid():
                                return self._parse_td3(td3_check)
                        except:
                            pass

                # TD1 (3 lines, 30 chars each) - ID cards
                if i + 2 < len(lines):
                    line1 = lines[i].strip()
                    line2 = lines[i + 1].strip()
                    line3 = lines[i + 2].strip()

                    if len(line1) == 30 and len(line2) == 30 and len(line3) == 30:
                        try:
                            mrz_code = line1 + '\n' + line2 + '\n' + line3
                            td1_check = TD1CodeChecker(mrz_code)
                            if td1_check.valid():
                                return self._parse_td1(td1_check)
                        except:
                            pass

                # TD2 (2 lines, 36 chars each) - ID cards
                if i + 1 < len(lines):
                    line1 = lines[i].strip()
                    line2 = lines[i + 1].strip()

                    if len(line1) == 36 and len(line2) == 36:
                        try:
                            mrz_code = line1 + '\n' + line2
                            td2_check = TD2CodeChecker(mrz_code)
                            if td2_check.valid():
                                return self._parse_td2(td2_check)
                        except:
                            pass

            return None

        except Exception as e:
            logger.error(f"MRZ extraction failed: {e}")
            return None

    def _parse_td3(self, checker) -> Dict[str, Any]:
        """Parse TD3 MRZ data."""
        return {
            "document_type": "TD3",
            "country_code": checker.country,
            "surname": checker.surname,
            "given_names": checker.name,
            "document_number": checker.document_number,
            "nationality": checker.nationality,
            "date_of_birth": checker.birth_date,
            "sex": checker.sex,
            "expiry_date": checker.expiry_date,
            "checksum_valid": checker.valid(),
            "raw_mrz_line1": checker.mrz_code.split('\n')[0],
            "raw_mrz_line2": checker.mrz_code.split('\n')[1]
        }

    def _parse_td1(self, checker) -> Dict[str, Any]:
        """Parse TD1 MRZ data."""
        lines = checker.mrz_code.split('\n')
        return {
            "document_type": "TD1",
            "country_code": checker.country,
            "surname": checker.surname,
            "given_names": checker.name,
            "document_number": checker.document_number,
            "nationality": checker.nationality,
            "date_of_birth": checker.birth_date,
            "sex": checker.sex,
            "expiry_date": checker.expiry_date,
            "checksum_valid": checker.valid(),
            "raw_mrz_line1": lines[0] if len(lines) > 0 else "",
            "raw_mrz_line2": lines[1] if len(lines) > 1 else "",
            "raw_mrz_line3": lines[2] if len(lines) > 2 else ""
        }

    def _parse_td2(self, checker) -> Dict[str, Any]:
        """Parse TD2 MRZ data."""
        return {
            "document_type": "TD2",
            "country_code": checker.country,
            "surname": checker.surname,
            "given_names": checker.name,
            "document_number": checker.document_number,
            "nationality": checker.nationality,
            "date_of_birth": checker.birth_date,
            "sex": checker.sex,
            "expiry_date": checker.expiry_date,
            "checksum_valid": checker.valid(),
            "raw_mrz_line1": checker.mrz_code.split('\n')[0],
            "raw_mrz_line2": checker.mrz_code.split('\n')[1]
        }


# Global OCR service instance
ocr_service = OCRService()
