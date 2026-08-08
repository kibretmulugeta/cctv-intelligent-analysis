"""Pydantic schemas for Event endpoints."""
from pydantic import BaseModel
from typing import Optional, List, Any, Dict
from datetime import datetime
from app.models.event import EventType, EventSeverity


class EventResponse(BaseModel):
    id: str
    video_id: Optional[str] = None
    event_type: EventType
    severity: EventSeverity
    description: Optional[str] = None
    object_type: Optional[str] = None
    object_id: Optional[int] = None
    confidence: Optional[float] = None
    frame_number: Optional[int] = None
    timestamp_sec: Optional[float] = None
    zone_name: Optional[str] = None
    extra_data: Optional[Dict[str, Any]] = None
    is_acknowledged: bool
    source: str
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class EventFilter(BaseModel):
    event_type: Optional[EventType] = None
    severity: Optional[EventSeverity] = None
    video_id: Optional[str] = None
    object_type: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    is_acknowledged: Optional[bool] = None


class EventListResponse(BaseModel):
    items: List[EventResponse]
    total: int
    page: int
    page_size: int
