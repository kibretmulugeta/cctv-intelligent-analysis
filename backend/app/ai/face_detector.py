"""
Face detector using OpenCV DNN or InsightFace.
Falls back gracefully if dependencies are unavailable.
"""
from __future__ import annotations
import logging
import numpy as np
from typing import List, Dict, Any, Tuple, Optional

logger = logging.getLogger(__name__)


class FaceDetector:
    """
    Detects faces in frames using OpenCV or InsightFace.
    Provides clean fallback if neither is available.
    """

    def __init__(self):
        self.backend = None
        self.is_available = False
        self._load()

    def _load(self) -> None:
        """Try to load face detection backend."""
        # Try InsightFace first
        try:
            import insightface
            from insightface.app import FaceAnalysis
            self._app = FaceAnalysis(
                name="buffalo_sc",
                providers=["CPUExecutionProvider"],
            )
            self._app.prepare(ctx_id=-1, det_size=(640, 640))
            self.backend = "insightface"
            self.is_available = True
            logger.info("Face detector: InsightFace loaded (buffalo_sc)")
            return
        except Exception as e:
            logger.debug(f"InsightFace not available: {e}")

        # Try OpenCV DNN (Haar Cascade as final fallback)
        try:
            import cv2
            cascade_path = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
            self._cascade = cv2.CascadeClassifier(cascade_path)
            if not self._cascade.empty():
                self.backend = "opencv_haar"
                self.is_available = True
                logger.info("Face detector: OpenCV Haar Cascade loaded")
                return
        except Exception as e:
            logger.debug(f"OpenCV Haar cascade not available: {e}")

        logger.warning("No face detector backend available. Face detection disabled.")
        self.is_available = False

    def detect(self, frame: np.ndarray) -> List[Dict[str, Any]]:
        """
        Detect faces in a frame.

        Returns list of:
            {bbox: [x1,y1,x2,y2], confidence, embedding (if available)}
        """
        if not self.is_available:
            return []

        h, w = frame.shape[:2]

        if self.backend == "insightface":
            return self._detect_insightface(frame, h, w)
        elif self.backend == "opencv_haar":
            return self._detect_haar(frame, h, w)
        return []

    def _detect_insightface(self, frame: np.ndarray, h: int, w: int) -> List[Dict[str, Any]]:
        try:
            import cv2
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            faces = self._app.get(rgb)
            results = []
            for face in faces:
                bbox = face.bbox.astype(int).tolist()
                x1 = max(0, bbox[0]) / w
                y1 = max(0, bbox[1]) / h
                x2 = min(w, bbox[2]) / w
                y2 = min(h, bbox[3]) / h
                embedding = face.embedding if hasattr(face, "embedding") else None
                results.append({
                    "bbox": [x1, y1, x2, y2],
                    "confidence": round(float(face.det_score), 4) if hasattr(face, "det_score") else 0.9,
                    "embedding": embedding,
                    "backend": "insightface",
                })
            return results
        except Exception as e:
            logger.error(f"InsightFace detection error: {e}")
            return []

    def _detect_haar(self, frame: np.ndarray, h: int, w: int) -> List[Dict[str, Any]]:
        try:
            import cv2
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = self._cascade.detectMultiScale(
                gray, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30)
            )
            results = []
            for (fx, fy, fw, fh) in faces:
                x1 = fx / w
                y1 = fy / h
                x2 = (fx + fw) / w
                y2 = (fy + fh) / h
                results.append({
                    "bbox": [x1, y1, x2, y2],
                    "confidence": 0.80,  # Haar does not provide confidence
                    "embedding": None,
                    "backend": "opencv_haar",
                })
            return results
        except Exception as e:
            logger.error(f"Haar cascade detection error: {e}")
            return []
