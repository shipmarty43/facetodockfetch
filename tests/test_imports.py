"""Test package imports and basic functionality"""

import pytest
import sys
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_path))


class TestCorePackages:
    """Test core package imports"""

    def test_fastapi_import(self):
        """Test FastAPI import"""
        import fastapi
        assert fastapi.__version__

    def test_pytorch_import(self):
        """Test PyTorch import"""
        import torch
        assert torch.__version__

    def test_opencv_import(self):
        """Test OpenCV import"""
        import cv2
        assert cv2.__version__

    def test_numpy_import(self):
        """Test NumPy import"""
        import numpy as np
        assert np.__version__

    def test_pillow_import(self):
        """Test Pillow import"""
        from PIL import Image
        assert Image.__version__

    def test_sqlalchemy_import(self):
        """Test SQLAlchemy import"""
        import sqlalchemy
        assert sqlalchemy.__version__

    def test_celery_import(self):
        """Test Celery import"""
        import celery
        assert celery.__version__

    def test_redis_import(self):
        """Test Redis import"""
        import redis
        assert redis.__version__

    def test_elasticsearch_import(self):
        """Test Elasticsearch import"""
        import elasticsearch
        assert elasticsearch.__version__

    def test_pydantic_import(self):
        """Test Pydantic import"""
        import pydantic
        assert pydantic.__version__

    def test_onnxruntime_import(self):
        """Test ONNX Runtime import"""
        import onnxruntime
        assert onnxruntime.__version__


class TestMLPackages:
    """Test ML/AI package imports"""

    def test_insightface_import(self):
        """Test InsightFace import"""
        import insightface
        assert insightface.__version__

    def test_mrz_import(self):
        """Test MRZ import"""
        import mrz
        assert mrz.__version__

    def test_surya_import(self):
        """Test Surya OCR import"""
        try:
            import surya
            # Surya might not have __version__
            assert True
        except ImportError as e:
            pytest.skip(f"Surya OCR not available: {e}")


class TestApplicationModules:
    """Test application module imports"""

    def test_config_import(self):
        """Test configuration module"""
        from app.config import Settings
        assert Settings

    def test_database_import(self):
        """Test database models"""
        from app.database import User, Document, Face
        assert User
        assert Document
        assert Face

    def test_face_service_import(self):
        """Test face recognition service"""
        from app.services.face_recognition import FaceRecognitionService
        assert FaceRecognitionService

    def test_ocr_service_import(self):
        """Test OCR service"""
        from app.services.ocr_service import OCRService
        assert OCRService

    def test_elasticsearch_service_import(self):
        """Test Elasticsearch service"""
        from app.services.elasticsearch_service import ElasticsearchService
        assert ElasticsearchService


class TestOpenCV:
    """Test OpenCV functionality"""

    def test_opencv_basic_operations(self):
        """Test basic OpenCV operations"""
        import cv2
        import numpy as np

        # Create test image
        img = np.zeros((100, 100, 3), dtype=np.uint8)

        # Test color conversion
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        assert gray.shape == (100, 100)

        # Test resize
        resized = cv2.resize(img, (50, 50))
        assert resized.shape == (50, 50, 3)

    def test_opencv_face_detection(self):
        """Test OpenCV face detection cascade"""
        import cv2

        # Check if cascade file exists
        cascade_file = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
        face_cascade = cv2.CascadeClassifier(cascade_file)

        assert not face_cascade.empty()


class TestPyTorch:
    """Test PyTorch functionality"""

    def test_pytorch_tensor_operations(self):
        """Test basic PyTorch tensor operations"""
        import torch

        # Create tensor
        x = torch.zeros((2, 3))
        assert x.shape == (2, 3)

        # Test operations
        y = torch.ones((2, 3))
        z = x + y
        assert z.sum() == 6.0

    def test_pytorch_gpu_availability(self):
        """Test PyTorch GPU availability"""
        import torch

        # This test passes whether GPU is available or not
        cuda_available = torch.cuda.is_available()
        assert isinstance(cuda_available, bool)

        if cuda_available:
            device_count = torch.cuda.device_count()
            assert device_count > 0


class TestMRZ:
    """Test MRZ package functionality"""

    def test_mrz_td3_parser(self):
        """Test MRZ TD3 (passport) parser"""
        from mrz.checker.td3 import TD3CodeChecker

        # Valid TD3 MRZ example
        mrz_code = (
            "P<UTOERIKSSON<<ANNA<MARIA<<<<<<<<<<<<<<<<<<<\n"
            "L898902C36UTO7408122F1204159ZE184226B<<<<<10"
        )

        result = TD3CodeChecker(mrz_code)
        assert result.valid_score > 0

    def test_mrz_td1_parser(self):
        """Test MRZ TD1 (ID card) parser"""
        from mrz.checker.td1 import TD1CodeChecker

        # Valid TD1 MRZ example
        mrz_code = (
            "I<UTOD231458907<<<<<<<<<<<<<<<\n"
            "7408122F1204159UTO<<<<<<<<<<<6\n"
            "ERIKSSON<<ANNA<MARIA<<<<<<<<<"
        )

        result = TD1CodeChecker(mrz_code)
        assert result.valid_score > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
