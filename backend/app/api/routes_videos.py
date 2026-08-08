"""
Video upload and management routes.
Handles upload, metadata, processing trigger, status polling, and streaming.
"""
from __future__ import annotations
import asyncio
import logging
import os
from pathlib import Path
from typing import List, Optional

from fastapi import APIRouter, Depends, File, UploadFile, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse, StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.config import settings
from app.models.video import Video, VideoStatus
from app.models.detection import Detection, TrackedObject
from app.models.event import Event
from app.schemas.video import VideoResponse, VideoProcessRequest, VideoStatusResponse
from app.schemas.detection import DetectionSummary
from app.services.video_service import VideoProcessingJob, process_video_async
from app.utils.image_utils import sanitize_filename, generate_unique_filename
from app.utils.video_utils import get_video_metadata

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/videos", tags=["videos"])

# In-memory job registry (for single-server use)
_jobs: dict = {}


@router.get("", response_model=List[VideoResponse])
async def list_videos(db: AsyncSession = Depends(get_db)):
    """List all uploaded videos."""
    result = await db.execute(select(Video).order_by(Video.created_at.desc()))
    return result.scalars().all()


@router.post("/upload", response_model=VideoResponse)
async def upload_video(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
):
    """Upload a video file and store it."""
    # Validate extension
    if not file.filename:
        raise HTTPException(400, "No filename provided")

    ext = Path(file.filename).suffix.lower().lstrip(".")
    if ext not in settings.allowed_extensions_list:
        raise HTTPException(400, f"Unsupported format: .{ext}. Allowed: {settings.allowed_extensions_list}")

    # Read file
    content = await file.read()
    if len(content) > settings.max_upload_bytes:
        raise HTTPException(413, f"File too large. Maximum: {settings.MAX_UPLOAD_SIZE_MB}MB")

    # Save file
    safe_name = sanitize_filename(file.filename)
    unique_name = generate_unique_filename(safe_name, prefix="upload")
    upload_dir = settings.get_upload_path()
    filepath = str(upload_dir / unique_name)

    with open(filepath, "wb") as f:
        f.write(content)

    # Get metadata
    meta = get_video_metadata(filepath)

    # Create DB record
    video = Video(
        filename=unique_name,
        original_filename=safe_name,
        filepath=filepath,
        file_size=len(content),
        status=VideoStatus.UPLOADED,
        **{k: v for k, v in meta.items() if k != "error"},
    )
    db.add(video)
    await db.commit()
    await db.refresh(video)

    logger.info(f"Video uploaded: {safe_name} -> {unique_name} ({len(content)} bytes)")
    return video


@router.get("/{video_id}", response_model=VideoResponse)
async def get_video(video_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Video).where(Video.id == video_id))
    video = result.scalar_one_or_none()
    if not video:
        raise HTTPException(404, "Video not found")
    return video


@router.post("/{video_id}/process")
async def process_video(
    video_id: str,
    request: VideoProcessRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    """Start video processing pipeline."""
    result = await db.execute(select(Video).where(Video.id == video_id))
    video = result.scalar_one_or_none()
    if not video:
        raise HTTPException(404, "Video not found")

    if video.status == VideoStatus.PROCESSING:
        raise HTTPException(409, "Video is already being processed")

    # Update status
    video.status = VideoStatus.PROCESSING
    video.progress = 0.0
    await db.commit()

    # Start background job
    job = VideoProcessingJob(video_id=video_id, filepath=video.filepath)
    _jobs[video_id] = job

    background_tasks.add_task(
        _run_processing_job,
        job=job,
        video_id=video_id,
        total_frames=video.total_frames,
        fps=video.fps,
        request_dict=request.model_dump(),
    )

    return {"message": "Processing started", "video_id": video_id}


async def _run_processing_job(
    job: VideoProcessingJob,
    video_id: str,
    total_frames: Optional[int],
    fps: Optional[float],
    request_dict: dict,
):
    """Background task that runs the processing and saves results to DB."""
    from app.database import AsyncSessionLocal
    from datetime import datetime, timezone

    try:
        await process_video_async(job, request_dict)
    except Exception as e:
        logger.error(f"Job failed: {e}", exc_info=True)
        job.status = "failed"
        job.error_message = str(e)

    # Save results to database
    async with AsyncSessionLocal() as db:
        try:
            result = await db.execute(select(Video).where(Video.id == video_id))
            video = result.scalar_one_or_none()
            if not video:
                return

            if job.status == "completed":
                video.status = VideoStatus.COMPLETED
                video.output_filepath = job.output_filepath
                video.processed_at = datetime.now(timezone.utc)
            else:
                video.status = VideoStatus.FAILED
                video.error_message = job.error_message

            video.progress = job.progress
            video.processed_frames = job.processed_frames
            video.processing_time = job.processing_time

            # Save detections in batches
            BATCH_SIZE = 500
            for i in range(0, len(job.all_detections), BATCH_SIZE):
                batch = job.all_detections[i:i + BATCH_SIZE]
                for det in batch:
                    db.add(Detection(video_id=video_id, **det))

            # Save tracked objects
            for track in job.all_tracked_objects:
                db.add(TrackedObject(
                    video_id=video_id,
                    track_id=track["track_id"],
                    object_type=track["object_type"],
                    first_seen_frame=track["first_seen_frame"],
                    last_seen_frame=track["last_seen_frame"],
                    frame_count=track["frame_count"],
                    avg_confidence=track["avg_confidence"],
                ))

            # Save events
            for ev in job.all_events:
                db.add(Event(video_id=video_id, **ev))

            await db.commit()
            logger.info(f"Results saved for video {video_id}")

        except Exception as e:
            await db.rollback()
            logger.error(f"Failed to save results: {e}", exc_info=True)


@router.get("/{video_id}/status", response_model=VideoStatusResponse)
async def get_video_status(video_id: str, db: AsyncSession = Depends(get_db)):
    """Get processing status - check in-memory job first for live progress."""
    job = _jobs.get(video_id)
    if job:
        return VideoStatusResponse(
            id=video_id,
            status=VideoStatus(job.status) if job.status in [s.value for s in VideoStatus] else VideoStatus.PROCESSING,
            progress=job.progress,
            processed_frames=job.processed_frames,
            total_frames=job.total_frames or None,
            error_message=job.error_message,
        )

    result = await db.execute(select(Video).where(Video.id == video_id))
    video = result.scalar_one_or_none()
    if not video:
        raise HTTPException(404, "Video not found")

    return VideoStatusResponse(
        id=video.id,
        status=video.status,
        progress=video.progress,
        processed_frames=video.processed_frames,
        total_frames=video.total_frames,
        error_message=video.error_message,
    )


@router.get("/{video_id}/results")
async def get_video_results(video_id: str, db: AsyncSession = Depends(get_db)):
    """Get detection results and summary for a processed video."""
    result = await db.execute(select(Video).where(Video.id == video_id))
    video = result.scalar_one_or_none()
    if not video:
        raise HTTPException(404, "Video not found")

    from sqlalchemy import func
    # Get class distribution
    from app.models.detection import Detection as Det

    class_result = await db.execute(
        select(Det.class_name, func.count().label("count"))
        .where(Det.video_id == video_id)
        .group_by(Det.class_name)
    )
    class_dist = {row[0]: row[1] for row in class_result.fetchall()}

    total = sum(class_dist.values())
    persons = class_dist.get("person", 0)
    vehicles = sum(class_dist.get(c, 0) for c in ["car", "bus", "truck", "motorcycle"])
    bicycles = class_dist.get("bicycle", 0)
    other = total - persons - vehicles - bicycles

    # Get unique tracks
    from app.models.detection import TrackedObject as TO
    tracks_result = await db.execute(
        select(func.count()).select_from(TO).where(TO.video_id == video_id)
    )
    unique_tracks = tracks_result.scalar() or 0

    # Get events
    events_result = await db.execute(
        select(Event).where(Event.video_id == video_id).order_by(Event.created_at.desc()).limit(50)
    )
    events = events_result.scalars().all()

    return {
        "video_id": video_id,
        "summary": DetectionSummary(
            total_detections=total,
            persons=persons,
            vehicles=vehicles,
            bicycles=bicycles,
            other=other,
            unique_tracks=unique_tracks,
            faces_detected=class_dist.get("face", 0),
        ),
        "class_distribution": class_dist,
        "events": [
            {
                "id": e.id,
                "event_type": e.event_type,
                "severity": e.severity,
                "description": e.description,
                "timestamp_sec": e.timestamp_sec,
                "created_at": e.created_at.isoformat() if e.created_at else None,
            }
            for e in events
        ],
        "has_output": bool(video.output_filepath and os.path.exists(video.output_filepath)),
    }


@router.get("/{video_id}/stream")
async def stream_video(video_id: str, db: AsyncSession = Depends(get_db)):
    """Serve the processed (annotated) video file."""
    result = await db.execute(select(Video).where(Video.id == video_id))
    video = result.scalar_one_or_none()
    if not video:
        raise HTTPException(404, "Video not found")

    filepath = video.output_filepath or video.filepath
    if not filepath or not os.path.exists(filepath):
        raise HTTPException(404, "Video file not found")

    return FileResponse(
        filepath,
        media_type="video/mp4",
        headers={"Accept-Ranges": "bytes"},
    )
