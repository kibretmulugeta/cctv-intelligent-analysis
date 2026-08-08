"""Events management routes with filtering and pagination."""
from __future__ import annotations
from typing import List, Optional
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.database import get_db
from app.models.event import Event, EventType, EventSeverity
from app.schemas.event import EventResponse, EventListResponse

router = APIRouter(prefix="/api/events", tags=["events"])


@router.get("", response_model=EventListResponse)
async def list_events(
    event_type: Optional[str] = Query(default=None),
    severity: Optional[str] = Query(default=None),
    video_id: Optional[str] = Query(default=None),
    object_type: Optional[str] = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
):
    """List events with optional filters."""
    query = select(Event)
    count_query = select(func.count()).select_from(Event)

    if event_type:
        query = query.where(Event.event_type == event_type)
        count_query = count_query.where(Event.event_type == event_type)
    if severity:
        query = query.where(Event.severity == severity)
        count_query = count_query.where(Event.severity == severity)
    if video_id:
        query = query.where(Event.video_id == video_id)
        count_query = count_query.where(Event.video_id == video_id)
    if object_type:
        query = query.where(Event.object_type == object_type)
        count_query = count_query.where(Event.object_type == object_type)

    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    offset = (page - 1) * page_size
    query = query.order_by(Event.created_at.desc()).offset(offset).limit(page_size)

    result = await db.execute(query)
    events = result.scalars().all()

    return EventListResponse(
        items=events,
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/{event_id}", response_model=EventResponse)
async def get_event(event_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Event).where(Event.id == event_id))
    event = result.scalar_one_or_none()
    if not event:
        raise HTTPException(404, "Event not found")
    return event


@router.patch("/{event_id}/acknowledge")
async def acknowledge_event(event_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Event).where(Event.id == event_id))
    event = result.scalar_one_or_none()
    if not event:
        raise HTTPException(404, "Event not found")
    event.is_acknowledged = True
    await db.commit()
    return {"message": "Event acknowledged"}
