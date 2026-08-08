"""Pydantic schemas for Video endpoints."""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from app.models.video import VideoStatus


class VideoBase(BaseModel):
    original_filename: str


class VideoCreate(VideoBase):
    pass


class VideoMetadata(BaseModel):
    resolution_width: Optional[int] = None
    resolution_height: Optional[int] = None
    fps: Optional[float] = None
    duration: Optional[float] = None
    total_frames: Optional[int] = None


class VideoResponse(BaseModel):
    id: str
    filename: str
    original_filename: str
    file_size: Optional[int] = None
    resolution_width: Optional[int] = None
    resolution_height: Optional[int] = None
    fps: Optional[float] = None
    duration: Optional[float] = None
    total_frames: Optional[int] = None
    status: VideoStatus
    progress: float
    error_message: Optional[str] = None
    processed_frames: int
    processing_time: Optional[float] = None
    created_at: Optional[datetime] = None
    processed_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class VideoProcessRequest(BaseModel):
    confidence_threshold: float = Field(default=0.45, ge=0.1, le=1.0)
    frame_skip: int = Field(default=1, ge=1, le=10)
    enable_tracking: bool = True
    enable_face_detection: bool = True
    enable_face_recognition: bool = False
    roi_x1: Optional[float] = None
    roi_y1: Optional[float] = None
    roi_x2: Optional[float] = None
    roi_y2: Optional[float] = None


class VideoStatusResponse(BaseModel):
    id: str
    status: VideoStatus
    progress: float
    processed_frames: int
    total_frames: Optional[int] = None
    error_message: Optional[str] = None
