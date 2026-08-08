"""
Video processing service.
Orchestrates the full AI pipeline: YOLO → tracking → activity → face detection.
Runs in a background thread to avoid blocking the API.
"""
from __future__ import annotations
import asyncio
import logging
import time
import os
from pathlib import Path
from typing import Optional, Dict, Any, Tuple
from datetime import datetime, timezone

import numpy as np

from app.config import settings
from app.utils.video_utils import get_video_metadata, frame_generator, draw_detections, validate_video_file
from app.utils.image_utils import generate_unique_filename
from app.ai.yolo_detector import YOLODetector
from app.ai.object_tracker import ObjectTracker
from app.ai.activity_analyzer import ActivityAnalyzer, AnalyzerConfig
from app.ai.face_detector import FaceDetector
from app.ai.face_recognizer import FaceRecognizer

logger = logging.getLogger(__name__)

# Global singleton AI components (initialized once)
_yolo: Optional[YOLODetector] = None
_face_detector: Optional[FaceDetector] = None
_face_recognizer: Optional[FaceRecognizer] = None


def get_yolo() -> YOLODetector:
    global _yolo
    if _yolo is None:
        device = settings.resolve_device()
        _yolo = YOLODetector(
            model_path=settings.YOLO_MODEL,
            device=device,
            confidence=settings.CONFIDENCE_THRESHOLD,
        )
        logger.info(f"YOLO initialized. Mode: {_yolo.mode}, Device: {device}")
    return _yolo


def get_face_detector() -> FaceDetector:
    global _face_detector
    if _face_detector is None:
        _face_detector = FaceDetector()
        logger.info(f"Face detector initialized. Backend: {_face_detector.backend}")
    return _face_detector


def get_face_recognizer() -> FaceRecognizer:
    global _face_recognizer
    if _face_recognizer is None:
        _face_recognizer = FaceRecognizer(threshold=settings.FACE_MATCH_THRESHOLD)
    return _face_recognizer


class VideoProcessingJob:
    """Manages the state of a single video processing job."""

    def __init__(self, video_id: str, filepath: str):
        self.video_id = video_id
        self.filepath = filepath
        self.status = "pending"
        self.progress = 0.0
        self.processed_frames = 0
        self.total_frames = 0
        self.error_message: Optional[str] = None
        self.output_filepath: Optional[str] = None
        self.all_detections: list = []
        self.all_events: list = []
        self.all_tracked_objects: list = []
        self.face_detections: list = []
        self.processing_time: Optional[float] = None
        self.inference_times: list = []


async def process_video_async(
    job: VideoProcessingJob,
    process_request: Dict[str, Any],
    on_progress=None,
) -> VideoProcessingJob:
    """
    Run the full video AI pipeline asynchronously.
    Offloads heavy CPU work to a thread pool.
    """
    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(
        None,
        lambda: _process_video_sync(job, process_request, on_progress),
    )
    return result


def _process_video_sync(
    job: VideoProcessingJob,
    process_request: Dict[str, Any],
    on_progress=None,
) -> VideoProcessingJob:
    """Synchronous video processing pipeline."""
    start_time = time.time()
    job.status = "processing"

    try:
        # Validate video
        allowed_exts = settings.allowed_extensions_list
        valid, msg = validate_video_file(job.filepath, allowed_exts)
        if not valid:
            raise ValueError(f"Invalid video: {msg}")

        # Get metadata
        meta = get_video_metadata(job.filepath)
        if "error" in meta:
            raise ValueError(f"Cannot read video: {meta['error']}")

        fps = meta.get("fps", 30.0) or 30.0
        total_frames = meta.get("total_frames", 0)
        job.total_frames = total_frames
        width = meta.get("resolution_width", 640)
        height = meta.get("resolution_height", 480)

        logger.info(f"[Job {job.video_id}] Starting processing: {total_frames} frames @ {fps:.1f}fps")

        # Initialize AI components
        yolo = get_yolo()
        tracker = ObjectTracker()
        analyzer = ActivityAnalyzer()

        # Parse ROI from request
        roi = None
        if all(process_request.get(k) is not None for k in ["roi_x1", "roi_y1", "roi_x2", "roi_y2"]):
            roi = (
                process_request["roi_x1"], process_request["roi_y1"],
                process_request["roi_x2"], process_request["roi_y2"],
            )
            analyzer.set_roi(roi)

        enable_tracking = process_request.get("enable_tracking", True)
        enable_face = process_request.get("enable_face_detection", True)
        enable_recognition = process_request.get("enable_face_recognition", False)
        conf_threshold = process_request.get("confidence_threshold", settings.CONFIDENCE_THRESHOLD)
        frame_skip = process_request.get("frame_skip", settings.FRAME_SKIP)
        face_interval = settings.FACE_FRAME_INTERVAL

        # Load face enrollments if recognition is enabled
        face_detector = get_face_detector()
        face_recognizer = get_face_recognizer()

        # Setup video writer for annotated output
        import cv2
        output_filename = generate_unique_filename(job.filepath, prefix="output")
        output_path = str(settings.get_output_path() / output_filename)

        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
        out_writer = cv2.VideoWriter(output_path, fourcc, fps, (width, height))

        frame_detections_buffer = []  # batch for DB write
        frame_events_buffer = []
        tracked_ids: Dict[int, Dict] = {}

        for frame_number, frame in frame_generator(job.filepath, frame_skip=1):
            t0 = time.time()

            current_detections = []
            current_faces = []

            # --- YOLO Detection / Tracking ---
            if frame_number % max(frame_skip, 1) == 0:
                if enable_tracking:
                    raw = yolo.detect_and_track(frame, confidence=conf_threshold)
                else:
                    raw = yolo.detect(frame, confidence=conf_threshold)

                tracker.update(raw, frame_number)
                current_detections = raw

                # Save to buffer for DB
                for det in raw:
                    frame_detections_buffer.append({
                        "frame_number": frame_number,
                        "timestamp_sec": frame_number / fps,
                        "class_name": det["class_name"],
                        "class_id": det.get("class_id"),
                        "confidence": det["confidence"],
                        "bbox_x1": det["bbox"][0],
                        "bbox_y1": det["bbox"][1],
                        "bbox_x2": det["bbox"][2],
                        "bbox_y2": det["bbox"][3],
                        "track_id": det.get("track_id"),
                    })

            # --- Face Detection ---
            if enable_face and frame_number % face_interval == 0:
                if face_detector.is_available:
                    detected_faces = face_detector.detect(frame)
                    for face in detected_faces:
                        recognition_result = {"name": "Unknown", "confidence": 0.0, "matched": False}
                        if enable_recognition and face.get("embedding") is not None:
                            recognition_result = face_recognizer.recognize(face["embedding"])
                        current_faces.append({
                            **face,
                            "name": recognition_result["name"],
                            "recognition_confidence": recognition_result["confidence"],
                        })

                    if detected_faces:
                        frame_events_buffer.append({
                            "event_type": "FACE_DETECTED",
                            "severity": "info",
                            "description": f"{len(detected_faces)} face(s) detected",
                            "frame_number": frame_number,
                            "timestamp_sec": frame_number / fps,
                            "source": "ai",
                        })
                        for face in current_faces:
                            if face["name"] != "Unknown":
                                frame_events_buffer.append({
                                    "event_type": "FACE_RECOGNIZED",
                                    "severity": "info",
                                    "description": f"Identity recognized: {face['name']}",
                                    "frame_number": frame_number,
                                    "timestamp_sec": frame_number / fps,
                                    "source": "ai",
                                    "extra_data": {"name": face["name"], "confidence": face.get("recognition_confidence")},
                                })

            # --- Activity Analysis ---
            if current_detections:
                activity_events = analyzer.analyze(current_detections, frame_number, fps)
                for ev in activity_events:
                    frame_events_buffer.append({
                        "event_type": ev.event_type,
                        "severity": ev.severity,
                        "description": ev.description,
                        "object_type": ev.object_type,
                        "object_id": ev.object_id,
                        "confidence": ev.confidence,
                        "frame_number": ev.frame_number,
                        "timestamp_sec": ev.timestamp_sec,
                        "zone_name": ev.zone_name,
                        "extra_data": ev.extra_data,
                        "source": ev.source,
                    })

            # --- Draw Annotations ---
            annotated = draw_detections(frame, current_detections, current_faces, roi)
            out_writer.write(annotated)

            # --- Progress ---
            job.processed_frames = frame_number + 1
            if total_frames > 0:
                job.progress = min(99.0, (frame_number + 1) / total_frames * 100)

            elapsed = time.time() - t0
            job.inference_times.append(elapsed)

        out_writer.release()

        # Collect final track states
        job.all_tracked_objects = tracker.get_all_tracks()
        job.all_detections = frame_detections_buffer
        job.all_events = frame_events_buffer
        job.output_filepath = output_path
        job.status = "completed"
        job.progress = 100.0
        job.processing_time = time.time() - start_time

        logger.info(
            f"[Job {job.video_id}] Completed. "
            f"Frames: {job.processed_frames}, "
            f"Detections: {len(job.all_detections)}, "
            f"Events: {len(job.all_events)}, "
            f"Time: {job.processing_time:.1f}s"
        )

    except Exception as e:
        logger.error(f"[Job {job.video_id}] Processing failed: {e}", exc_info=True)
        job.status = "failed"
        job.error_message = str(e)
        job.processing_time = time.time() - start_time

    return job
