#!/usr/bin/env python3
"""
Automated Environment Testing Script
Tests conda environment installation and package functionality
"""

import sys
import importlib
from typing import List, Tuple, Optional


class Color:
    """ANSI color codes"""
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    BOLD = '\033[1m'
    END = '\033[0m'


def print_header(text: str):
    """Print formatted header"""
    print(f"\n{Color.BOLD}{Color.BLUE}{'=' * 60}{Color.END}")
    print(f"{Color.BOLD}{Color.BLUE}{text}{Color.END}")
    print(f"{Color.BOLD}{Color.BLUE}{'=' * 60}{Color.END}\n")


def print_success(text: str):
    """Print success message"""
    print(f"{Color.GREEN}✓{Color.END} {text}")


def print_error(text: str):
    """Print error message"""
    print(f"{Color.RED}✗{Color.END} {text}")


def print_warning(text: str):
    """Print warning message"""
    print(f"{Color.YELLOW}⚠{Color.END} {text}")


def test_import(module_name: str, package_name: Optional[str] = None) -> Tuple[bool, str, str]:
    """
    Test if a module can be imported

    Args:
        module_name: Name of the module to import
        package_name: Display name (defaults to module_name)

    Returns:
        Tuple of (success, version, error_message)
    """
    package_name = package_name or module_name

    try:
        module = importlib.import_module(module_name)
        version = getattr(module, '__version__', 'unknown')

        # Special version handling
        if module_name == 'cv2':
            version = module.__version__
        elif module_name == 'elasticsearch':
            version = str(module.__version__)

        return True, version, ""
    except ImportError as e:
        return False, "", str(e)
    except Exception as e:
        return False, "", f"Unexpected error: {str(e)}"


def test_core_packages() -> int:
    """Test core package imports"""
    print_header("Testing Core Packages")

    packages = [
        ('fastapi', 'FastAPI'),
        ('torch', 'PyTorch'),
        ('cv2', 'OpenCV'),
        ('PIL', 'Pillow'),
        ('numpy', 'NumPy'),
        ('sqlalchemy', 'SQLAlchemy'),
        ('celery', 'Celery'),
        ('redis', 'Redis'),
        ('elasticsearch', 'Elasticsearch'),
        ('insightface', 'InsightFace'),
        ('mrz', 'MRZ'),
        ('pydantic', 'Pydantic'),
        ('onnxruntime', 'ONNX Runtime'),
    ]

    failed = 0
    for module_name, package_name in packages:
        success, version, error = test_import(module_name, package_name)

        if success:
            print_success(f"{package_name:<20} v{version}")
        else:
            print_error(f"{package_name:<20} FAILED: {error}")
            failed += 1

    return failed


def test_application_modules() -> int:
    """Test application module imports"""
    print_header("Testing Application Modules")

    # Add backend to path
    sys.path.insert(0, '/home/user/facetodockfetch/backend')

    modules = [
        ('app.config', 'Configuration'),
        ('app.database', 'Database Models'),
        ('app.services.face_recognition', 'Face Recognition Service'),
        ('app.services.ocr_service', 'OCR Service'),
        ('app.services.elasticsearch_service', 'Elasticsearch Service'),
    ]

    failed = 0
    for module_name, display_name in modules:
        success, _, error = test_import(module_name, display_name)

        if success:
            print_success(f"{display_name}")
        else:
            print_error(f"{display_name}: {error}")
            failed += 1

    return failed


def test_fastapi_app() -> int:
    """Test FastAPI application initialization"""
    print_header("Testing FastAPI Application")

    try:
        sys.path.insert(0, '/home/user/facetodockfetch/backend')
        from app.main import app

        print_success(f"App initialized: {app.title}")
        print_success(f"Version: {app.version}")

        # Count routes
        routes = [r for r in app.routes if hasattr(r, 'path')]
        api_routes = [r for r in routes if r.path.startswith('/api')]

        print_success(f"Total routes: {len(routes)}")
        print_success(f"API routes: {len(api_routes)}")

        return 0
    except Exception as e:
        print_error(f"FastAPI app failed to initialize: {e}")
        return 1


def test_insightface_model() -> int:
    """Test InsightFace model loading"""
    print_header("Testing InsightFace Model")

    try:
        from insightface.app import FaceAnalysis

        print("Loading buffalo_l model (this may take a minute)...")
        app = FaceAnalysis(name='buffalo_l', providers=['CPUExecutionProvider'])
        app.prepare(ctx_id=0, det_size=(640, 640))

        print_success("InsightFace buffalo_l model loaded successfully")
        print_success(f"Detection size: {app.det_size}")

        return 0
    except Exception as e:
        print_error(f"InsightFace model loading failed: {e}")
        return 1


def test_opencv() -> int:
    """Test OpenCV functionality"""
    print_header("Testing OpenCV")

    try:
        import cv2
        import numpy as np

        # Create a test image
        img = np.zeros((100, 100, 3), dtype=np.uint8)

        # Test basic operations
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        resized = cv2.resize(img, (50, 50))

        print_success(f"OpenCV version: {cv2.__version__}")
        print_success("Basic image operations working")

        return 0
    except Exception as e:
        print_error(f"OpenCV test failed: {e}")
        return 1


def test_gpu_availability() -> int:
    """Test GPU/CUDA availability"""
    print_header("Testing GPU Availability")

    try:
        import torch

        if torch.cuda.is_available():
            device_count = torch.cuda.device_count()
            device_name = torch.cuda.get_device_name(0) if device_count > 0 else "N/A"

            print_success(f"CUDA is available: {torch.version.cuda}")
            print_success(f"GPU device count: {device_count}")
            print_success(f"Primary GPU: {device_name}")
        else:
            print_warning("CUDA not available (CPU mode)")

        return 0
    except Exception as e:
        print_error(f"GPU test failed: {e}")
        return 1


def run_all_tests():
    """Run all tests and report results"""
    print(f"\n{Color.BOLD}Face Recognition & OCR System - Environment Test{Color.END}")
    print(f"{Color.BOLD}{'=' * 60}{Color.END}")

    total_failed = 0

    # Run all test suites
    total_failed += test_core_packages()
    total_failed += test_opencv()
    total_failed += test_application_modules()
    total_failed += test_fastapi_app()
    total_failed += test_gpu_availability()

    # InsightFace model test (optional, can be slow)
    if '--skip-model' not in sys.argv:
        total_failed += test_insightface_model()
    else:
        print_warning("\nSkipping InsightFace model loading test (--skip-model)")

    # Final report
    print_header("Test Results Summary")

    if total_failed == 0:
        print_success(f"{Color.BOLD}All tests passed!{Color.END}")
        print("\n✅ Environment is ready for development and deployment\n")
        return 0
    else:
        print_error(f"{Color.BOLD}{total_failed} test(s) failed{Color.END}")
        print("\n❌ Please fix the errors above before proceeding\n")
        return 1


if __name__ == "__main__":
    sys.exit(run_all_tests())
