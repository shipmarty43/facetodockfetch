"""Face recognition service using InsightFace (AdaFace/ArcFace)."""
import logging
import numpy as np
from typing import List, Dict, Any, Optional, Tuple
from PIL import Image
import cv2
from pathlib import Path

logger = logging.getLogger(__name__)


class FaceRecognitionService:
    """Service for face detection and recognition using InsightFace."""

    def __init__(self, model_name: str = "buffalo_l"):
        """
        Initialize face recognition service.

        Args:
            model_name: InsightFace model name (buffalo_l for high accuracy)
        """
        self.model = None
        self.model_name = model_name
        self.opencv_cascade = None  # Initialize OpenCV cascade attribute
        self._load_model()

    def _load_model(self):
        """Load InsightFace model with GPU support if available, or use OpenCV fallback."""
        try:
            import insightface
            from insightface.app import FaceAnalysis
            import os

            logger.info(f"Loading InsightFace model: {self.model_name}")

            # Check if GPU should be used
            use_gpu = os.getenv('USE_GPU', 'false').lower() == 'true'

            # Configure providers (GPU first, then CPU fallback)
            if use_gpu:
                try:
                    import onnxruntime as ort
                    available_providers = ort.get_available_providers()

                    if 'CUDAExecutionProvider' in available_providers:
                        providers = ['CUDAExecutionProvider', 'CPUExecutionProvider']
                        logger.info("CUDA is available - using GPU for face recognition")
                    else:
                        providers = ['CPUExecutionProvider']
                        logger.warning("CUDA requested but not available - falling back to CPU")
                except:
                    providers = ['CPUExecutionProvider']
                    logger.warning("Could not check CUDA availability - using CPU")
            else:
                providers = ['CPUExecutionProvider']
                logger.info("Using CPU for face recognition")

            self.model = FaceAnalysis(name=self.model_name, providers=providers)
            self.model.prepare(ctx_id=0, det_size=(640, 640))
            logger.info(f"InsightFace model loaded successfully with providers: {providers}")
        except Exception as e:
            logger.warning(f"InsightFace not available: {e}")
            logger.info("Falling back to OpenCV Haar Cascade for face detection")
            self.model = None
            self._init_opencv_cascade()

    def _init_opencv_cascade(self):
        """Initialize OpenCV Haar Cascade for fallback face detection."""
        try:
            # Load pre-trained Haar Cascade classifier
            cascade_path = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
            self.opencv_cascade = cv2.CascadeClassifier(cascade_path)

            if self.opencv_cascade.empty():
                raise Exception("Failed to load Haar Cascade")

            logger.info("✓ OpenCV Haar Cascade loaded successfully")
            logger.warning("⚠ Using basic face detection - no face embeddings will be generated")
            logger.warning("⚠ Face search functionality will be limited without embeddings")
        except Exception as e:
            logger.error(f"Failed to load OpenCV Haar Cascade: {e}")
            self.opencv_cascade = None

    def detect_faces(
        self,
        image_path: str,
        min_confidence: float = 0.5
    ) -> List[Dict[str, Any]]:
        """
        Detect faces in an image using InsightFace or OpenCV fallback.

        Args:
            image_path: Path to the image
            min_confidence: Minimum detection confidence (0-1)

        Returns:
            List of detected faces with embeddings and metadata
        """
        try:
            # Try InsightFace if available
            if self.model is not None:
                return self._detect_with_insightface(image_path, min_confidence)
            # Fallback to OpenCV Haar Cascade
            elif hasattr(self, 'opencv_cascade') and self.opencv_cascade is not None:
                return self._detect_with_opencv(image_path, min_confidence)
            else:
                logger.error("No face detection method available")
                return []

        except Exception as e:
            logger.error(f"Face detection failed: {e}")
            import traceback
            traceback.print_exc()
            return []

    def _detect_with_insightface(self, image_path: str, min_confidence: float) -> List[Dict[str, Any]]:
        """Detect faces using InsightFace."""
        # Read image
        img = cv2.imread(image_path)
        if img is None:
            raise Exception(f"Failed to read image: {image_path}")

        # Detect faces
        faces = self.model.get(img)

        results = []
        for idx, face in enumerate(faces):
            # Filter by confidence
            if face.det_score < min_confidence:
                continue

            # Extract face embedding (512D vector for buffalo_l)
            embedding = face.embedding

            # Calculate quality score
            quality = self._calculate_face_quality(face)

            # Get bounding box
            bbox = face.bbox.astype(int)

            results.append({
                "face_index": idx,
                "embedding": embedding.tolist(),
                "bbox": {
                    "x": int(bbox[0]),
                    "y": int(bbox[1]),
                    "width": int(bbox[2] - bbox[0]),
                    "height": int(bbox[3] - bbox[1])
                },
                "confidence": float(face.det_score),
                "quality_score": quality,
                "landmarks": face.kps.tolist() if hasattr(face, 'kps') else None,
                "age": int(face.age) if hasattr(face, 'age') else None,
                "gender": face.gender if hasattr(face, 'gender') else None
            })

        logger.info(f"Detected {len(results)} faces with InsightFace in {image_path}")
        return results

    def _detect_with_opencv(self, image_path: str, min_confidence: float) -> List[Dict[str, Any]]:
        """Detect faces using OpenCV Haar Cascade (fallback - no embeddings)."""
        # Read image
        img = cv2.imread(image_path)
        if img is None:
            raise Exception(f"Failed to read image: {image_path}")

        # Convert to grayscale for Haar Cascade
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        # Detect faces
        faces = self.opencv_cascade.detectMultiScale(
            gray,
            scaleFactor=1.1,
            minNeighbors=5,
            minSize=(30, 30)
        )

        results = []
        for idx, (x, y, w, h) in enumerate(faces):
            # Generate a dummy embedding (zeros) since we can't extract real embeddings
            # This allows the system to work but face search won't be accurate
            dummy_embedding = [0.0] * 512

            # Estimate quality based on size (larger faces = better quality)
            img_height, img_width = img.shape[:2]
            face_area = w * h
            image_area = img_width * img_height
            quality = min(face_area / (300 * 300), 1.0)  # Normalize to 300x300 reference

            results.append({
                "face_index": idx,
                "embedding": dummy_embedding,  # Dummy embedding
                "bbox": {
                    "x": int(x),
                    "y": int(y),
                    "width": int(w),
                    "height": int(h)
                },
                "confidence": 0.8,  # Haar Cascade doesn't provide confidence, use default
                "quality_score": float(quality),
                "landmarks": None,
                "age": None,
                "gender": None
            })

        logger.info(f"Detected {len(results)} faces with OpenCV in {image_path}")
        logger.warning(f"⚠ Face embeddings are dummy values - search will not work accurately")
        return results

    def _calculate_face_quality(self, face) -> float:
        """
        Calculate face quality score based on multiple factors.

        Args:
            face: InsightFace face object

        Returns:
            Quality score (0-1)
        """
        quality = 0.0

        # Detection confidence (40% weight)
        quality += face.det_score * 0.4

        # Face size (30% weight) - larger faces are generally better
        bbox = face.bbox
        face_size = (bbox[2] - bbox[0]) * (bbox[3] - bbox[1])
        size_score = min(face_size / (300 * 300), 1.0)  # Normalize to 300x300
        quality += size_score * 0.3

        # Pose estimation (30% weight) - frontal faces are better
        if hasattr(face, 'pose'):
            # Lower pose values indicate more frontal face
            pose_score = max(0, 1.0 - (abs(face.pose[0]) + abs(face.pose[1]) + abs(face.pose[2])) / 90)
            quality += pose_score * 0.3
        else:
            quality += 0.15  # Default medium score if pose not available

        return min(max(quality, 0.0), 1.0)

    def extract_face_crop(
        self,
        image_path: str,
        bbox: Dict[str, int],
        output_path: str,
        margin: float = 0.2
    ) -> bool:
        """
        Extract and save a cropped face image.

        Args:
            image_path: Path to original image
            bbox: Bounding box dict with x, y, width, height
            output_path: Path to save cropped face
            margin: Margin around face (0.2 = 20% padding)

        Returns:
            True if successful
        """
        try:
            img = cv2.imread(image_path)
            if img is None:
                return False

            h, w = img.shape[:2]

            # Add margin
            x = max(0, int(bbox["x"] - bbox["width"] * margin))
            y = max(0, int(bbox["y"] - bbox["height"] * margin))
            width = min(w - x, int(bbox["width"] * (1 + 2 * margin)))
            height = min(h - y, int(bbox["height"] * (1 + 2 * margin)))

            # Crop face
            face_crop = img[y:y+height, x:x+width]

            # Save
            Path(output_path).parent.mkdir(parents=True, exist_ok=True)
            cv2.imwrite(output_path, face_crop)

            return True

        except Exception as e:
            logger.error(f"Failed to extract face crop: {e}")
            return False

    def compare_faces(
        self,
        embedding1: List[float],
        embedding2: List[float]
    ) -> float:
        """
        Compare two face embeddings using cosine similarity.

        Args:
            embedding1: First face embedding
            embedding2: Second face embedding

        Returns:
            Similarity score (0-1, higher is more similar)
        """
        try:
            # Convert to numpy arrays
            emb1 = np.array(embedding1)
            emb2 = np.array(embedding2)

            # Normalize embeddings
            emb1 = emb1 / np.linalg.norm(emb1)
            emb2 = emb2 / np.linalg.norm(emb2)

            # Calculate cosine similarity
            similarity = np.dot(emb1, emb2)

            # Convert to 0-1 range (cosine similarity is -1 to 1)
            similarity = (similarity + 1) / 2

            return float(similarity)

        except Exception as e:
            logger.error(f"Face comparison failed: {e}")
            return 0.0

    def get_embedding_from_image(
        self,
        image_path: str
    ) -> Optional[List[float]]:
        """
        Get face embedding from an image (assumes single face).

        Args:
            image_path: Path to image

        Returns:
            Face embedding or None if no face detected
        """
        faces = self.detect_faces(image_path)

        if not faces:
            return None

        # Return embedding of the first/best face
        best_face = max(faces, key=lambda f: f["quality_score"])
        return best_face["embedding"]

    def batch_detect_faces(
        self,
        image_paths: List[str],
        min_confidence: float = 0.5
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Detect faces in multiple images (batch processing).

        Args:
            image_paths: List of image paths
            min_confidence: Minimum detection confidence

        Returns:
            Dict mapping image path to list of detected faces
        """
        results = {}

        for image_path in image_paths:
            results[image_path] = self.detect_faces(image_path, min_confidence)

        return results


# Global face recognition service instance
face_recognition_service = FaceRecognitionService()
