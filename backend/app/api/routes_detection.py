"""Detection query routes."""
from fastapi import APIRouter, Depends, Query
from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.models.detection import Detection
from app.schemas.detection import DetectionResponse

router = APIRouter(prefix="/api/detections", tags=["detections"])


@router.get("", response_model=List[DetectionResponse])
async def list_detections(
    video_id: Optional[str] = Query(default=None),
    class_name: Optional[str] = Query(default=None),
    limit: int = Query(default=100, ge=1, le=1000),
    db: AsyncSession = Depends(get_db),
):
    query = select(Detection)
    if video_id:
        query = query.where(Detection.video_id == video_id)
    if class_name:
        query = query.where(Detection.class_name == class_name)
    query = query.order_by(Detection.frame_number).limit(limit)
    result = await db.execute(query)
    detections = result.scalars().all()

    # Map to response schema
    return [
        DetectionResponse(
            id=d.id,
            video_id=d.video_id,
            frame_number=d.frame_number,
            timestamp_sec=d.timestamp_sec,
            class_name=d.class_name,
            confidence=d.confidence,
            bbox={"x1": d.bbox_x1, "y1": d.bbox_y1, "x2": d.bbox_x2, "y2": d.bbox_y2},
            track_id=d.track_id,
            created_at=d.created_at,
        )
        for d in detections
    ]
