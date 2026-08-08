"""
YOLO-based object detector.
Uses Ultralytics YOLO for real inference.
Falls back to a demo mode if the model cannot be loaded.
"""
from __future__ import annotations
import logging
from typing import List, Dict, Any, Optional, Tuple
import numpy as np

logger = logging.getLogger(__name__)

# Classes of interest for CCTV analysis
CCTV_CLASSES = {
    "person", "car", "bus", "truck", "motorcycle",
    "bicycle", "dog", "cat", "backpack", "handbag",
    "suitcase", "umbrella", "traffic light", "stop sign",
}

VEHICLE_CLASSES = {"car", "bus", "truck", "motorcycle"}
PERSON_CLASSES = {"person"}


class YOLODetector:
    """
    Wraps Ultralytics YOLO for object detection.
    Provides graceful fallback if the model cannot load.
    """

    def __init__(self, model_path: str = "yolo11n.pt", device: str = "cpu", confidence: float = 0.45):
        self.model_path = model_path
        self.device = device
        self.confidence = confidence
        self.model = None
        self.is_available = False
        self._load_model()

    def _load_model(self) -> None:
        """Attempt to load the YOLO model."""
        try:
            from ultralytics import YOLO
            logger.info(f"Loading YOLO model: {self.model_path} on device: {self.device}")
            self.model = YOLO(self.model_path)
            # Warmup inference
            dummy = np.zeros((640, 640, 3), dtype=np.uint8)
            self.model(dummy, verbose=False, device=self.device)
            self.is_available = True
            logger.info(f"YOLO model loaded successfully. Device: {self.device}")
        except Exception as e:
            logger.warning(f"YOLO model could not be loaded: {e}. Running in demo mode.")
            self.is_available = False

    def detect(
        self,
        frame: np.ndarray,
        confidence: Optional[float] = None,
        iou: float = 0.45,
    ) -> List[Dict[str, Any]]:
        """
        Run detection on a single frame.

        Returns list of detections:
            [{class_name, class_id, confidence, bbox: [x1,y1,x2,y2], track_id}]
        """
        conf = confidence or self.confidence

        if not self.is_available or self.model is None:
            return self._demo_detections(frame)

        try:
            results = self.model(
                frame,
                conf=conf,
                iou=iou,
                device=self.device,
                verbose=False,
            )
            return self._parse_results(results, frame.shape)
        except Exception as e:
            logger.error(f"Detection error: {e}")
            return []

    def detect_and_track(
        self,
        frame: np.ndarray,
        confidence: Optional[float] = None,
        iou: float = 0.45,
        tracker: str = "bytetrack.yaml",
    ) -> List[Dict[str, Any]]:
        """Run detection with object tracking (ByteTrack)."""
        conf = confidence or self.confidence

        if not self.is_available or self.model is None:
            return self._demo_detections(frame, with_track_ids=True)

        try:
            results = self.model.track(
                frame,
                conf=conf,
                iou=iou,
                device=self.device,
                tracker=tracker,
                persist=True,
                verbose=False,
            )
            return self._parse_results(results, frame.shape)
        except Exception as e:
            logger.error(f"Tracking error: {e}. Falling back to detect-only.")
            return self.detect(frame, confidence, iou)

    def _parse_results(self, results, frame_shape: Tuple[int, int, int]) -> List[Dict[str, Any]]:
        """Parse Ultralytics result objects into our standardized format."""
        detections = []
        h, w = frame_shape[:2]

        for result in results:
            boxes = result.boxes
            if boxes is None:
                continue

            for box in boxes:
                try:
                    cls_id = int(box.cls[0])
                    cls_name = result.names[cls_id]
                    conf = float(box.conf[0])
                    xyxy = box.xyxy[0].tolist()

                    # Normalize bounding box to 0-1
                    x1 = max(0.0, xyxy[0] / w)
                    y1 = max(0.0, xyxy[1] / h)
                    x2 = min(1.0, xyxy[2] / w)
                    y2 = min(1.0, xyxy[3] / h)

                    # Track ID (may be None for detect-only)
                    track_id = None
                    if boxes.id is not None:
                        try:
                            track_id = int(box.id[0])
                        except Exception:
                            pass

                    detections.append({
                        "class_name": cls_name,
                        "class_id": cls_id,
                        "confidence": round(conf, 4),
                        "bbox": [x1, y1, x2, y2],
                        "track_id": track_id,
                    })
                except Exception as e:
                    logger.debug(f"Failed to parse detection box: {e}")
                    continue

        return detections

    def _demo_detections(
        self,
        frame: np.ndarray,
        with_track_ids: bool = False,
    ) -> List[Dict[str, Any]]:
        """
        DEMO MODE: Returns clearly-marked simulated detections.
        Used when YOLO is unavailable. Simulated results are NOT real inference.
        """
        import random
        rng = random.Random(hash(frame.tobytes()[:100]))

        demo_objects = [
            ("person", 0, 0.82),
            ("person", 0, 0.75),
            ("car", 2, 0.91),
        ]

        results = []
        for i, (cls, cls_id, base_conf) in enumerate(demo_objects):
            conf = base_conf + rng.uniform(-0.05, 0.05)
            x1 = rng.uniform(0.05, 0.4)
            y1 = rng.uniform(0.05, 0.4)
            x2 = x1 + rng.uniform(0.1, 0.25)
            y2 = y1 + rng.uniform(0.15, 0.35)
            results.append({
                "class_name": cls,
                "class_id": cls_id,
                "confidence": round(min(conf, 0.99), 4),
                "bbox": [
                    round(x1, 4), round(y1, 4),
                    round(min(x2, 0.99), 4), round(min(y2, 0.99), 4)
                ],
                "track_id": i + 1 if with_track_ids else None,
                "_demo": True,  # Mark as demo data
            })

        return results

    @property
    def mode(self) -> str:
        return "inference" if self.is_available else "demo"
