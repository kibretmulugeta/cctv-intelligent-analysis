"""Image utility functions."""
from __future__ import annotations
import logging
import re
import uuid
from pathlib import Path
from typing import Optional, Tuple
import numpy as np

logger = logging.getLogger(__name__)


def sanitize_filename(filename: str) -> str:
    """Sanitize a filename to prevent path traversal and invalid characters."""
    # Remove path separators
    name = Path(filename).name
    # Replace dangerous characters
    name = re.sub(r"[^\w\-_\. ]", "_", name)
    # Limit length
    if len(name) > 200:
        ext = Path(name).suffix
        name = name[:200 - len(ext)] + ext
    return name


def generate_unique_filename(original: str, prefix: str = "") -> str:
    """Generate a unique filename based on UUID."""
    ext = Path(original).suffix.lower()
    uid = str(uuid.uuid4())[:8]
    prefix_str = f"{prefix}_" if prefix else ""
    return f"{prefix_str}{uid}{ext}"


def load_image_from_bytes(data: bytes) -> Optional[np.ndarray]:
    """Load an image from raw bytes using OpenCV."""
    try:
        import cv2
        arr = np.frombuffer(data, dtype=np.uint8)
        img = cv2.imdecode(arr, cv2.IMREAD_COLOR)
        return img
    except Exception as e:
        logger.error(f"Failed to decode image: {e}")
        return None


def resize_frame(frame: np.ndarray, max_dim: int = 1280) -> np.ndarray:
    """Resize frame while maintaining aspect ratio."""
    import cv2
    h, w = frame.shape[:2]
    if max(h, w) <= max_dim:
        return frame
    scale = max_dim / max(h, w)
    new_w = int(w * scale)
    new_h = int(h * scale)
    return cv2.resize(frame, (new_w, new_h))


def crop_bbox(frame: np.ndarray, bbox: list, padding: float = 0.1) -> Optional[np.ndarray]:
    """Crop a region from frame given normalized [x1,y1,x2,y2] bbox."""
    h, w = frame.shape[:2]
    x1 = int(max(0, bbox[0] - padding) * w)
    y1 = int(max(0, bbox[1] - padding) * h)
    x2 = int(min(1.0, bbox[2] + padding) * w)
    y2 = int(min(1.0, bbox[3] + padding) * h)
    if x2 <= x1 or y2 <= y1:
        return None
    return frame[y1:y2, x1:x2]
