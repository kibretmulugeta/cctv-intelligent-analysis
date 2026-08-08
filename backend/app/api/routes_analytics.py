"""Analytics routes returning real database-derived statistics."""
from fastapi import APIRouter, Depends, Query
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.services import analytics_service

router = APIRouter(prefix="/api/analytics", tags=["analytics"])


@router.get("/dashboard")
async def dashboard_stats(db: AsyncSession = Depends(get_db)):
    """High-level dashboard statistics."""
    return await analytics_service.get_dashboard_stats(db)


@router.get("/detections-over-time")
async def detections_over_time(
    video_id: Optional[str] = Query(default=None),
    db: AsyncSession = Depends(get_db),
):
    """Detection counts grouped in 5-second time bins."""
    return await analytics_service.get_detections_over_time(db, video_id)


@router.get("/events-by-type")
async def events_by_type(
    video_id: Optional[str] = Query(default=None),
    db: AsyncSession = Depends(get_db),
):
    """Event count per event type."""
    return await analytics_service.get_events_over_time(db, video_id)


@router.get("/class-distribution")
async def class_distribution(
    video_id: Optional[str] = Query(default=None),
    db: AsyncSession = Depends(get_db),
):
    """Detection count per object class."""
    return await analytics_service.get_class_distribution(db, video_id)


@router.get("/recent-events")
async def recent_events(
    limit: int = Query(default=20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """Most recent events."""
    return await analytics_service.get_recent_events(db, limit)
