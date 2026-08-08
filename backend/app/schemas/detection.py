"""Pydantic schemas for Detection and TrackedObject endpoints."""
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class BoundingBox(BaseModel):
    x1: float
    y1: float
    x2: float
    y2: float


class DetectionResponse(BaseModel):
    id: str
    video_id: str
    frame_number: int
    timestamp_sec: Optional[float] = None
    class_name: str
    confidence: float
    bbox: BoundingBox
    track_id: Optional[int] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class TrackedObjectResponse(BaseModel):
    id: str
    video_id: str
    track_id: int
    object_type: str
    first_seen_frame: int
    last_seen_frame: int
    frame_count: int
    avg_confidence: Optional[float] = None

    class Config:
        from_attributes = True


class DetectionSummary(BaseModel):
    """Summary statistics for a video's detections."""
    total_detections: int
    persons: int
    vehicles: int
    bicycles: int
    other: int
    unique_tracks: int
    faces_detected: int
