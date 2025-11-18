#!/usr/bin/env python3
"""Check if all required dependencies are installed and working."""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

def check_dependency(name, import_statement, test_func=None):
    """Check if a dependency is installed and working."""
    try:
        exec(import_statement)
        if test_func:
            test_func()
        print(f"✓ {name}")
        return True
    except Exception as e:
        print(f"✗ {name}: {e}")
        return False

def main():
    """Check all dependencies."""
    print("Checking dependencies...\n")

    all_ok = True

    # Core dependencies
    print("Core dependencies:")
    all_ok &= check_dependency("FastAPI", "import fastapi")
    all_ok &= check_dependency("Uvicorn", "import uvicorn")
    all_ok &= check_dependency("SQLAlchemy", "import sqlalchemy")
    all_ok &= check_dependency("Pydantic", "import pydantic")
    all_ok &= check_dependency("Redis", "import redis")
    all_ok &= check_dependency("Celery", "import celery")
    print()

    # Security dependencies
    print("Security dependencies:")
    all_ok &= check_dependency("Passlib", "import passlib")
    all_ok &= check_dependency("bcrypt", "import bcrypt")
    all_ok &= check_dependency("Cryptography", "import cryptography")
    all_ok &= check_dependency("python-jose", "import jose")
    print()

    # Image processing
    print("Image processing:")
    all_ok &= check_dependency("Pillow", "from PIL import Image")
    all_ok &= check_dependency("OpenCV", "import cv2")
    all_ok &= check_dependency("pdf2image", "import pdf2image")
    print()

    # ML/AI dependencies
    print("ML/AI dependencies:")
    all_ok &= check_dependency("PyTorch", "import torch")
    all_ok &= check_dependency("Torchvision", "import torchvision")
    all_ok &= check_dependency("NumPy", "import numpy")
    print()

    # Face recognition
    print("Face recognition:")
    all_ok &= check_dependency("InsightFace", "import insightface")
    all_ok &= check_dependency("ONNX Runtime", "import onnxruntime")
    print()

    # OCR dependencies
    print("OCR dependencies:")
    surya_ok = check_dependency("Surya OCR", "import surya")

    if surya_ok:
        # Try to import specific predictors
        print("  Checking Surya predictors:")
        try:
            from surya.foundation import FoundationPredictor
            from surya.detection import DetectionPredictor
            from surya.recognition import RecognitionPredictor
            print("    ✓ FoundationPredictor, DetectionPredictor, RecognitionPredictor")

            # Try to instantiate (may take time)
            try:
                print("    Testing predictor initialization (may download models)...")
                foundation = FoundationPredictor()
                print("    ✓ FoundationPredictor instantiated")
                det = DetectionPredictor()
                print("    ✓ DetectionPredictor instantiated")
                rec = RecognitionPredictor(foundation)
                print("    ✓ RecognitionPredictor instantiated")
            except Exception as e:
                print(f"    ⚠ Predictor initialization: {e}")
                print("    (This may be due to missing models - they will be downloaded on first use)")
        except ImportError as e:
            print(f"    ✗ Predictor imports failed: {e}")
            all_ok = False
    else:
        all_ok = False

    all_ok &= check_dependency("pytesseract", "import pytesseract")
    all_ok &= check_dependency("MRZ", "import mrz")
    print()

    # Search
    print("Search dependencies:")
    all_ok &= check_dependency("Elasticsearch", "import elasticsearch")
    print()

    # Check if app config loads
    print("Application configuration:")
    try:
        from app.config import settings
        print(f"✓ Config loaded")
        print(f"  Mode: {settings.MODE}")
        print(f"  Database: {settings.DATABASE_URL}")
        print(f"  USE_GPU: {settings.USE_GPU}")

        # Check Surya OCR settings
        print(f"\n  Surya OCR configuration:")
        print(f"    DETECTOR_TEXT_THRESHOLD: {settings.DETECTOR_TEXT_THRESHOLD}")
        print(f"    DETECTOR_BATCH_SIZE: {settings.DETECTOR_BATCH_SIZE}")
        print(f"    RECOGNITION_BATCH_SIZE: {settings.RECOGNITION_BATCH_SIZE}")
        print(f"    LAYOUT_BATCH_SIZE: {settings.LAYOUT_BATCH_SIZE}")
        if settings.USE_GPU:
            print(f"    CUDA_VISIBLE_DEVICES: {settings.CUDA_VISIBLE_DEVICES}")
            print(f"    PYTORCH_CUDA_ALLOC_CONF: {settings.PYTORCH_CUDA_ALLOC_CONF}")
    except Exception as e:
        print(f"✗ Config failed: {e}")
        all_ok = False
    print()

    # Summary
    if all_ok:
        print("=" * 50)
        print("✓ All dependencies are installed and working!")
        print("=" * 50)
        return 0
    else:
        print("=" * 50)
        print("✗ Some dependencies are missing or not working")
        print("=" * 50)
        return 1

if __name__ == "__main__":
    sys.exit(main())
