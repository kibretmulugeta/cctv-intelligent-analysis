"""
Video utility functions using OpenCV.
"""
from __future__ import annotations
import logging
from typing import Optional, Dict, Any, Generator, Tuple
from pathlib import Path
import numpy as np

logger = logging.getLogger(__name__)


def get_video_metadata(filepath: str) -> Dict[str, Any]:
    """Extract metadata from a video file using OpenCV."""
    try:
        import cv2
        cap = cv2.VideoCapture(filepath)
        if not cap.isOpened():
            return {"error": "Cannot open video file"}

        fps = cap.get(cv2.CAP_PROP_FPS)
        frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        duration = frame_count / fps if fps > 0 else 0

        cap.release()

        return {
            "resolution_width": width,
            "resolution_height": height,
            "fps": round(fps, 2),
            "total_frames": frame_count,
            "duration": round(duration, 2),
        }
    except Exception as e:
        logger.error(f"Error reading video metadata: {e}")
        return {"error": str(e)}


def frame_generator(
    filepath: str,
    frame_skip: int = 1,
) -> Generator[Tuple[int, np.ndarray], None, None]:
    """
    Generator that yields (frame_number, frame) tuples from a video file.
    Skips frames according to frame_skip parameter.
    """
    import cv2
    cap = cv2.VideoCapture(filepath)
    if not cap.isOpened():
        logger.error(f"Cannot open video: {filepath}")
        return

    frame_number = 0
    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                break

            if frame_number % frame_skip == 0:
                yield frame_number, frame

            frame_number += 1
    finally:
        cap.release()


def draw_detections(
    frame: np.ndarray,
    detections: list,
    face_detections: Optional[list] = None,
    roi: Optional[Tuple[float, float, float, float]] = None,
) -> np.ndarray:
    """
    Draw bounding boxes and labels on a frame.
    Returns a copy of the frame with annotations.
    """
    import cv2

    output = frame.copy()
    h, w = output.shape[:2]

    # Color map for object classes
    CLASS_COLORS = {
        "person": (0, 255, 100),
        "car": (0, 180, 255),
        "truck": (0, 140, 255),
        "bus": (0, 100, 255),
        "motorcycle": (0, 200, 200),
        "bicycle": (200, 255, 0),
        "dog": (255, 200, 0),
        "cat": (255, 150, 0),
        "default": (200, 200, 200),
    }

    # Draw ROI if configured
    if roi is not None:
        rx1 = int(roi[0] * w)
        ry1 = int(roi[1] * h)
        rx2 = int(roi[2] * w)
        ry2 = int(roi[3] * h)
        cv2.rectangle(output, (rx1, ry1), (rx2, ry2), (255, 255, 0), 2)
        cv2.putText(output, "MONITORING ZONE", (rx1, max(0, ry1 - 8)),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 0), 1)

    # Draw object detections
    for det in detections:
        bbox = det["bbox"]
        x1 = int(bbox[0] * w)
        y1 = int(bbox[1] * h)
        x2 = int(bbox[2] * w)
        y2 = int(bbox[3] * h)

        cls_name = det["class_name"]
        confidence = det["confidence"]
        track_id = det.get("track_id")
        is_demo = det.get("_demo", False)

        color = CLASS_COLORS.get(cls_name, CLASS_COLORS["default"])

        # Dim color for demo mode
        if is_demo:
            color = tuple(int(c * 0.6) for c in color)

        cv2.rectangle(output, (x1, y1), (x2, y2), color, 2)

        # Label
        label = f"{cls_name.upper()}"
        if track_id is not None:
            label += f" #{track_id}"
        label += f" {confidence:.2f}"
        if is_demo:
            label += " [DEMO]"

        label_y = max(y1 - 8, 12)
        (lw, lh), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)
        cv2.rectangle(output, (x1, label_y - lh - 4), (x1 + lw + 4, label_y + 2), color, -1)
        cv2.putText(output, label, (x1 + 2, label_y),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 1)

    # Draw face detections
    if face_detections:
        for face in face_detections:
            bbox = face["bbox"]
            x1 = int(bbox[0] * w)
            y1 = int(bbox[1] * h)
            x2 = int(bbox[2] * w)
            y2 = int(bbox[3] * h)
            name = face.get("name", "Unknown")
            conf = face.get("recognition_confidence") or face.get("confidence", 0)

            if name.lower() == "admin":
                face_color = (0, 255, 0)  # Bright Green for Admin
                label = f"★ ADMIN ★ ({conf:.2f})"
            elif name != "Unknown":
                face_color = (255, 200, 0)  # Cyan/Gold for registered Persons
                label = f"FACE: {name} ({conf:.2f})"
            else:
                face_color = (0, 100, 255)  # Orange for Unknown
                label = f"FACE: Detecting..."

            # Draw outer rectangle and filled label background
            cv2.rectangle(output, (x1, y1), (x2, y2), face_color, 2)
            label_y = max(y1 - 10, 15)
            (lw, lh), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.55, 2)
            cv2.rectangle(output, (x1, label_y - lh - 4), (x1 + lw + 6, label_y + 4), face_color, -1)
            cv2.putText(output, label, (x1 + 3, label_y),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 0, 0), 2)

    return output



def encode_frame_to_jpeg(frame: np.ndarray, quality: int = 85) -> bytes:
    """Encode a frame to JPEG bytes."""
    import cv2
    _, buffer = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, quality])
    return buffer.tobytes()


def validate_video_file(filepath: str, allowed_extensions: list) -> Tuple[bool, str]:
    """Validate a video file by extension and attempting to open it."""
    path = Path(filepath)
    if path.suffix.lower().lstrip(".") not in allowed_extensions:
        return False, f"Unsupported format: {path.suffix}"

    try:
        import cv2
        cap = cv2.VideoCapture(filepath)
        if not cap.isOpened():
            cap.release()
            return False, "Cannot open video file"
        ret, _ = cap.read()
        cap.release()
        if not ret:
            return False, "Video file appears to be empty or corrupted"
        return True, "OK"
    except Exception as e:
        return False, str(e)
