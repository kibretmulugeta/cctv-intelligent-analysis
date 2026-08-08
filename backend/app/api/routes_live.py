"""
Real-Time Laptop Webcam / RTSP Stream API routes.
Streams annotated live frames directly to the browser dashboard using MJPEG format.
"""
from __future__ import annotations
import logging
import time
from typing import Generator
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse

from app.services.video_service import get_yolo, get_face_detector, get_face_recognizer
from app.ai.object_tracker import ObjectTracker
from app.ai.activity_analyzer import ActivityAnalyzer
from app.utils.video_utils import draw_detections, encode_frame_to_jpeg

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/live", tags=["live"])

_is_camera_active = False


def live_webcam_generator(camera_id: int = 0) -> Generator[bytes, None, None]:
    """
    Generator that opens laptop webcam (VideoCapture(0)), runs YOLO + Face detection,
    annotates bounding boxes in real time, and yields MJPEG frame bytes.
    """
    global _is_camera_active
    import cv2

    cap = cv2.VideoCapture(camera_id)
    if not cap.isOpened():
        logger.error(f"Cannot open webcam camera index: {camera_id}")
        return

    _is_camera_active = True
    yolo = get_yolo()
    tracker = ObjectTracker()
    analyzer = ActivityAnalyzer()
    face_detector = get_face_detector()
    face_recognizer = get_face_recognizer()

    frame_count = 0
    try:
        while _is_camera_active:
            ret, frame = cap.read()
            if not ret:
                logger.warning("Failed to grab webcam frame")
                time.sleep(0.05)
                continue

            frame_count += 1

            # Run YOLO detection & tracking
            detections = yolo.detect_and_track(frame, confidence=0.45)
            tracker.update(detections, frame_count)

            # Face detection every 5 frames
            current_faces = []
            if frame_count % 5 == 0 and face_detector.is_available:
                detected_faces = face_detector.detect(frame)
                for face in detected_faces:
                    rec = {"name": "Unknown", "confidence": 0.0}
                    if face.get("embedding") is not None and face_recognizer.has_enrolled():
                        rec = face_recognizer.recognize(face["embedding"])
                    current_faces.append({
                        **face,
                        "name": rec["name"],
                        "recognition_confidence": rec["confidence"],
                    })

            # Draw annotations
            annotated = draw_detections(frame, detections, current_faces)

            # Add Live Watermark
            cv2.putText(
                annotated,
                f"LIVE WEBCAM | FPS: 30 | DETECTIONS: {len(detections)}",
                (15, 25),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                (0, 255, 100),
                1,
            )

            # Encode frame to JPEG
            jpeg_bytes = encode_frame_to_jpeg(annotated, quality=80)

            yield (
                b"--frame\r\n"
                b"Content-Type: image/jpeg\r\n\r\n" + jpeg_bytes + b"\r\n"
            )

            # Target ~25-30 FPS
            time.sleep(0.03)

    finally:
        cap.release()
        _is_camera_active = False
        logger.info("Webcam stream stopped and hardware released")


@router.get("/stream")
async def live_stream(camera_id: int = Query(default=0)):
    """Stream live laptop webcam feed with YOLO & Face recognition overlays."""
    try:
        import cv2
        test_cap = cv2.VideoCapture(camera_id)
        if not test_cap.isOpened():
            test_cap.release()
            raise HTTPException(400, f"Cannot open webcam at index {camera_id}. Make sure camera permissions are enabled.")
        test_cap.release()
    except Exception as e:
        raise HTTPException(400, f"Webcam error: {str(e)}")

    return StreamingResponse(
        live_webcam_generator(camera_id),
        media_type="multipart/x-mixed-replace; boundary=frame",
    )


@router.post("/stop")
async def stop_live_stream():
    """Stop active webcam stream."""
    global _is_camera_active
    _is_camera_active = False
    return {"message": "Webcam stream stopped"}
