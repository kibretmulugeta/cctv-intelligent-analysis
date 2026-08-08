"""
Analytics service - computes statistics from database records.
Returns real data only - no fabricated metrics.
"""
from __future__ import annotations
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, text

from app.models.detection import Detection, TrackedObject
from app.models.event import Event
from app.models.video import Video, VideoStatus

logger = logging.getLogger(__name__)

VEHICLE_CLASSES = {"car", "bus", "truck", "motorcycle"}


async def get_dashboard_stats(db: AsyncSession) -> Dict[str, Any]:
    """Get high-level statistics for the dashboard."""
    # Total videos
    total_videos_result = await db.execute(select(func.count()).select_from(Video))
    total_videos = total_videos_result.scalar() or 0

    # Completed videos
    completed_result = await db.execute(
        select(func.count()).select_from(Video).where(Video.status == VideoStatus.COMPLETED)
    )
    completed_videos = completed_result.scalar() or 0

    # Total detections
    total_detections_result = await db.execute(select(func.count()).select_from(Detection))
    total_detections = total_detections_result.scalar() or 0

    # Total events
    total_events_result = await db.execute(select(func.count()).select_from(Event))
    total_events = total_events_result.scalar() or 0

    # Person count
    persons_result = await db.execute(
        select(func.count()).select_from(Detection).where(Detection.class_name == "person")
    )
    persons = persons_result.scalar() or 0

    # Vehicle count
    vehicles_result = await db.execute(
        select(func.count()).select_from(Detection).where(
            Detection.class_name.in_(list(VEHICLE_CLASSES))
        )
    )
    vehicles = vehicles_result.scalar() or 0

    # Bicycles
    bicycles_result = await db.execute(
        select(func.count()).select_from(Detection).where(Detection.class_name == "bicycle")
    )
    bicycles = bicycles_result.scalar() or 0

    # Face detections
    faces_result = await db.execute(
        select(func.count()).select_from(Event).where(
            Event.event_type == "FACE_DETECTED"
        )
    )
    faces = faces_result.scalar() or 0

    return {
        "total_videos": total_videos,
        "completed_videos": completed_videos,
        "total_detections": total_detections,
        "total_events": total_events,
        "persons": persons,
        "vehicles": vehicles,
        "bicycles": bicycles,
        "faces_detected": faces,
    }


async def get_detections_over_time(db: AsyncSession, video_id: Optional[str] = None, bins: int = 20) -> List[Dict]:
    """Return detection counts grouped by time buckets."""
    query = select(Detection.frame_number, Detection.class_name, Detection.timestamp_sec)
    if video_id:
        query = query.where(Detection.video_id == video_id)

    result = await db.execute(query)
    rows = result.fetchall()

    if not rows:
        return []

    # Group by timestamp bucket (every ~5 seconds)
    from collections import defaultdict
    buckets: Dict[int, Dict[str, int]] = defaultdict(lambda: {"person": 0, "vehicle": 0, "other": 0, "total": 0})

    for frame_num, cls_name, ts in rows:
        bucket = int((ts or 0) // 5)  # 5-second bins
        if cls_name == "person":
            buckets[bucket]["person"] += 1
        elif cls_name in VEHICLE_CLASSES:
            buckets[bucket]["vehicle"] += 1
        else:
            buckets[bucket]["other"] += 1
        buckets[bucket]["total"] += 1
        buckets[bucket]["time"] = bucket * 5

    return [{"time": v["time"], **{k: v[k] for k in ["person", "vehicle", "other", "total"]}}
            for v in sorted(buckets.values(), key=lambda x: x["time"])]


async def get_events_over_time(db: AsyncSession, video_id: Optional[str] = None) -> List[Dict]:
    """Return event counts by type."""
    from sqlalchemy import case
    query = select(Event.event_type, func.count().label("count")).group_by(Event.event_type)
    if video_id:
        query = query.where(Event.video_id == video_id)

    result = await db.execute(query)
    rows = result.fetchall()
    return [{"event_type": row[0], "count": row[1]} for row in rows]


async def get_class_distribution(db: AsyncSession, video_id: Optional[str] = None) -> List[Dict]:
    """Return detection count per class."""
    query = select(Detection.class_name, func.count().label("count")).group_by(Detection.class_name)
    if video_id:
        query = query.where(Detection.video_id == video_id)
    result = await db.execute(query.order_by(text("count DESC")))
    return [{"class_name": row[0], "count": row[1]} for row in result.fetchall()]


async def get_recent_events(db: AsyncSession, limit: int = 20) -> List[Dict]:
    """Get the most recent events."""
    result = await db.execute(
        select(Event).order_by(Event.created_at.desc()).limit(limit)
    )
    events = result.scalars().all()
    return [
        {
            "id": e.id,
            "event_type": e.event_type,
            "severity": e.severity,
            "description": e.description,
            "object_type": e.object_type,
            "object_id": e.object_id,
            "confidence": e.confidence,
            "timestamp_sec": e.timestamp_sec,
            "created_at": e.created_at.isoformat() if e.created_at else None,
        }
        for e in events
    ]
