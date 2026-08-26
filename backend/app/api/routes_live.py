"""
Real-Time Laptop Webcam / RTSP Stream API routes.
Streams annotated live frames directly to the browser dashboard using MJPEG format.
"""
from __future__ import annotations
import logging
import time
import asyncio
from typing import Generator
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse

from app.database import AsyncSessionLocal
from app.services.video_service import get_yolo, get_face_detector, get_face_recognizer
from app.services.face_service import get_enrolled_faces_for_recognizer, auto_register_person, enroll_face
from app.ai.object_tracker import ObjectTracker
from app.ai.activity_analyzer import ActivityAnalyzer
from app.utils.video_utils import draw_detections, encode_frame_to_jpeg

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/live", tags=["live"])

_is_camera_active = False


def _init_enrolled_faces_sync(face_recognizer):
    """Load enrolled faces from DB into recognizer memory synchronously."""
    async def _async_load():
        async with AsyncSessionLocal() as session:
            enrolled = await get_enrolled_faces_for_recognizer(session)
            face_recognizer.load_enrolled(enrolled)
    try:
        asyncio.run(_async_load())
    except Exception as e:
        logger.error(f"Error loading enrolled faces for stream: {e}")


def _auto_register_sync(embedding, face_recognizer):
    """Auto-register unknown face in DB and update recognizer cache synchronously."""
    async def _async_register():
        async with AsyncSessionLocal() as session:
            return await auto_register_person(session, embedding, face_recognizer)
    try:
        res = asyncio.run(_async_register())
        # Update in-memory recognizer
        face_recognizer._enrolled[res["face_id"]] = {
            "name": res["name"],
            "embeddings": [face_recognizer.bytes_to_embedding(res["embedding_bytes"])]
        }
        return res["name"]
    except Exception as e:
        logger.error(f"Error auto-registering person: {e}")
        return "Unknown"


def live_webcam_generator(camera_id: int = 0) -> Generator[bytes, None, None]:
    """
    Generator that opens laptop webcam, runs YOLO + Face detection,
    annotates bounding boxes in real time, auto-registers unknown people, and yields MJPEG frame bytes.
    """
    global _is_camera_active
    import cv2

    # Try DirectShow first on Windows, fall back to default driver
    cap = cv2.VideoCapture(camera_id, cv2.CAP_DSHOW)
    if not cap.isOpened():
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

    # Pre-load enrolled faces from DB
    _init_enrolled_faces_sync(face_recognizer)

    frame_count = 0
    current_faces = []

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
            if frame_count % 5 == 0 and face_detector.is_available:
                detected_faces = face_detector.detect(frame)
                current_faces = []
                for face in detected_faces:
                    embedding = face.get("embedding")
                    rec = {"name": "Unknown", "confidence": 0.0, "matched": False}

                    if embedding is not None:
                        if face_recognizer.has_enrolled():
                            rec = face_recognizer.recognize(embedding)

                        # If face is NOT matched, auto-register as a new Person ID!
                        if not rec["matched"]:
                            name = _auto_register_sync(embedding, face_recognizer)
                            rec = {"name": name, "confidence": 0.99, "matched": True}

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
    return StreamingResponse(
        live_webcam_generator(camera_id),
        media_type="multipart/x-mixed-replace; boundary=frame",
    )



@router.post("/capture-admin")
async def capture_admin_from_webcam(camera_id: int = Query(default=0)):
    """
    Captures a frame directly from laptop webcam and registers/updates the face as Admin.
    """
    import cv2
    cap = cv2.VideoCapture(camera_id)
    if not cap.isOpened():
        raise HTTPException(400, f"Cannot access webcam at index {camera_id}")

    ret, frame = cap.read()
    cap.release()

    if not ret or frame is None:
        raise HTTPException(400, "Failed to capture frame from webcam")

    face_detector = get_face_detector()
    face_recognizer = get_face_recognizer()

    _, buffer = cv2.imencode(".jpg", frame)
    image_bytes = buffer.tobytes()

    async with AsyncSessionLocal() as session:
        result = await enroll_face(
            db=session,
            name="Admin",
            image_data=image_bytes,
            image_filename="webcam_admin.jpg",
            face_detector=face_detector,
            face_recognizer=face_recognizer,
            description="Laptop Webcam Admin Snapshot",
        )
        if not result["success"]:
            raise HTTPException(400, result["error"])

        # Reload enrolled list
        enrolled = await get_enrolled_faces_for_recognizer(session)
        face_recognizer.load_enrolled(enrolled)

    return {"success": True, "message": "Successfully captured and registered as Admin!", "face_id": result["face_id"]}


@router.post("/stop")
async def stop_live_stream():
    """Stop active webcam stream."""
    global _is_camera_active
    _is_camera_active = False
    return {"message": "Webcam stream stopped"}

