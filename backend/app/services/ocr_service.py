"""OCR service using Surya OCR for text extraction."""
import logging
from typing import Optional, Dict, Any, List
from pathlib import Path
import time
import os

# Fix multiprocessing issues with Celery fork - must be set BEFORE importing torch/surya
os.environ['TOKENIZERS_PARALLELISM'] = 'false'
os.environ['OMP_NUM_THREADS'] = '1'
os.environ['MKL_NUM_THREADS'] = '1'

from PIL import Image
from pdf2image import convert_from_path

logger = logging.getLogger(__name__)


class OCRService:
    """Service for OCR operations using Surya OCR."""

    def __init__(self):
        """Initialize OCR service."""
        self.foundation_predictor = None
        self.det_predictor = None
        self.rec_predictor = None
        self._load_predictors()

    def _load_predictors(self):
        """Load Surya OCR predictors."""
        try:
            # Import Surya OCR predictors
            logger.info("Loading Surya OCR predictors...")

            from surya.foundation import FoundationPredictor
            from surya.detection import DetectionPredictor
            from surya.recognition import RecognitionPredictor
            from ..config import settings

            # Set environment variables for Surya configuration
            if settings.USE_GPU:
                os.environ['PYTORCH_CUDA_ALLOC_CONF'] = settings.PYTORCH_CUDA_ALLOC_CONF
                os.environ['CUDA_VISIBLE_DEVICES'] = settings.CUDA_VISIBLE_DEVICES
                logger.info(f"GPU enabled: CUDA_VISIBLE_DEVICES={settings.CUDA_VISIBLE_DEVICES}")

            # Set batch sizes from settings
            os.environ['DETECTOR_BATCH_SIZE'] = str(settings.DETECTOR_BATCH_SIZE)
            os.environ['RECOGNITION_BATCH_SIZE'] = str(settings.RECOGNITION_BATCH_SIZE)
            os.environ['LAYOUT_BATCH_SIZE'] = str(settings.LAYOUT_BATCH_SIZE)

            # Set detection threshold
            os.environ['DETECTOR_TEXT_THRESHOLD'] = str(settings.DETECTOR_TEXT_THRESHOLD)

            # Initialize predictors in correct order
            logger.info("Initializing foundation predictor...")
            self.foundation_predictor = FoundationPredictor()

            logger.info("Initializing detection predictor...")
            self.det_predictor = DetectionPredictor()

            logger.info("Initializing recognition predictor...")
            self.rec_predictor = RecognitionPredictor(self.foundation_predictor)

            logger.info("✓ Surya OCR predictors loaded successfully")
            logger.info(f"  Supported OCR languages: {settings.OCR_LANGUAGES}")
            logger.info(f"  Detection threshold: {settings.DETECTOR_TEXT_THRESHOLD}")
            logger.info(f"  Batch sizes - Detector: {settings.DETECTOR_BATCH_SIZE}, "
                       f"Recognition: {settings.RECOGNITION_BATCH_SIZE}, "
                       f"Layout: {settings.LAYOUT_BATCH_SIZE}")

        except ImportError as e:
            logger.warning(f"Surya OCR not available: {e}")
            logger.info("Falling back to pytesseract OCR")
            self.foundation_predictor = None
            self.det_predictor = None
            self.rec_predictor = None
        except Exception as e:
            logger.warning(f"Failed to load Surya OCR predictors: {e}")
            logger.info("Falling back to pytesseract OCR")
            self.foundation_predictor = None
            self.det_predictor = None
            self.rec_predictor = None

    def extract_text_from_image(
        self,
        image_path: str,
        attempt: int = 1
    ) -> Dict[str, Any]:
        """
        Extract text from an image using Surya OCR or pytesseract fallback.

        Args:
            image_path: Path to the image file
            attempt: Attempt number (1-3)

        Returns:
            Dict with OCR results
        """
        start_time = time.time()

        try:
            # Try Surya OCR if available
            if self.det_predictor is not None and self.rec_predictor is not None and self.foundation_predictor is not None:
                return self._extract_with_surya(image_path, attempt, start_time)
            else:
                # Fallback to pytesseract
                return self._extract_with_pytesseract(image_path, attempt, start_time)

        except Exception as e:
            logger.error(f"OCR failed (attempt {attempt}): {e}")
            import traceback
            traceback.print_exc()
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

    def _extract_with_surya(self, image_path: str, attempt: int, start_time: float) -> Dict[str, Any]:
        """Extract text using Surya OCR."""
        # Load image
        image = Image.open(image_path)

        # Run OCR
        logger.info(f"Running Surya OCR on {image_path} (attempt {attempt})")

        # Run recognition (it will use det_predictor internally for detection)
        # Correct API for Surya OCR 0.9.0+: rec_predictor([images], det_predictor=detection_predictor)
        rec_predictions = self.rec_predictor([image], det_predictor=self.det_predictor)

        # Extract text and structure
        full_text = ""
        structured_data = {
            "blocks": [],
            "languages": []
        }

        if rec_predictions and len(rec_predictions) > 0:
            prediction = rec_predictions[0]
            logger.debug(f"Surya OCR prediction type: {type(prediction)}")

            # Extract text blocks
            # Check if text_lines exists and is not empty
            text_lines = getattr(prediction, 'text_lines', [])
            if text_lines:
                logger.info(f"Found {len(text_lines)} text lines in image")
                for idx, text_line in enumerate(text_lines):
                    # Get text content
                    text = getattr(text_line, 'text', str(text_line))
                    if not text:
                        continue

                    full_text += text + "\n"

                    # Get bounding box if available
                    bbox = getattr(text_line, 'bbox', None)
                    # Convert bbox to list if it's a different type
                    if bbox is not None and not isinstance(bbox, (list, dict)):
                        try:
                            bbox = list(bbox)
                        except:
                            bbox = None

                    # Get confidence score
                    confidence = getattr(text_line, 'confidence', 1.0)

                    structured_data["blocks"].append({
                        "text": text,
                        "bbox": bbox,
                        "confidence": confidence
                    })
            else:
                logger.warning(f"No text lines found in Surya OCR prediction for {image_path}")

            # Detect languages from prediction if available
            # Note: Surya OCR may not always return languages in prediction object
            languages = getattr(prediction, 'languages', None)
            if languages and isinstance(languages, list):
                structured_data["languages"] = languages
                logger.info(f"Detected languages: {languages}")
            else:
                # Default to English if language detection not available
                structured_data["languages"] = ["en"]
                logger.debug("No language info in prediction, defaulting to English")
        else:
            logger.warning(f"Surya OCR returned empty predictions for {image_path}")

        processing_time = time.time() - start_time

        return {
            "full_text": full_text.strip(),
            "structured_data": structured_data,
            "language_detected": structured_data["languages"][0] if structured_data["languages"] else "en",
            "confidence_score": self._calculate_confidence(structured_data),
            "processing_time_seconds": processing_time,
            "attempt_number": attempt,
            "success": True if full_text.strip() else False
        }

    def _extract_with_pytesseract(self, image_path: str, attempt: int, start_time: float) -> Dict[str, Any]:
        """Extract text using pytesseract as fallback."""
        import pytesseract

        logger.info(f"Running pytesseract OCR on {image_path} (attempt {attempt})")

        # Load image
        image = Image.open(image_path)

        # Get detailed OCR data (includes confidence and position)
        ocr_data = pytesseract.image_to_data(image, output_type=pytesseract.Output.DICT)

        # Extract full text
        full_text = pytesseract.image_to_string(image)

        # Build structured data from pytesseract output
        structured_data = {
            "blocks": [],
            "languages": ["en"]  # pytesseract doesn't auto-detect language easily
        }

        # Group text by line
        n_boxes = len(ocr_data['text'])
        for i in range(n_boxes):
            text = ocr_data['text'][i].strip()
            if text:  # Only include non-empty text
                conf = int(ocr_data['conf'][i]) if ocr_data['conf'][i] != -1 else 0
                structured_data["blocks"].append({
                    "text": text,
                    "bbox": {
                        "x": ocr_data['left'][i],
                        "y": ocr_data['top'][i],
                        "width": ocr_data['width'][i],
                        "height": ocr_data['height'][i]
                    },
                    "confidence": conf / 100.0  # Convert to 0-1 range
                })

        processing_time = time.time() - start_time

        return {
            "full_text": full_text.strip(),
            "structured_data": structured_data,
            "language_detected": "en",
            "confidence_score": self._calculate_confidence(structured_data),
            "processing_time_seconds": processing_time,
            "attempt_number": attempt,
            "success": True
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
            images = convert_from_path(pdf_path, dpi=200)

            all_text = ""
            all_blocks = []
            total_confidence = 0.0
            languages = set()

            # Process each page
            for i, image in enumerate(images):
                logger.info(f"Processing page {i+1}/{len(images)}")

                # Save temporary image
                temp_image_path = f"/tmp/page_{i}_{os.getpid()}.jpg"
                image.save(temp_image_path, "JPEG")

                # Extract text from page
                page_result = self.extract_text_from_image(temp_image_path, attempt)

                if page_result["success"]:
                    all_text += f"\n--- Page {i+1} ---\n" + page_result["full_text"]
                    if page_result["structured_data"] and page_result["structured_data"].get("blocks"):
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
            import traceback
            traceback.print_exc()
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
