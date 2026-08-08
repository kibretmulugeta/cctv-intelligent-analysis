"""Pydantic schemas for Face endpoints."""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class FaceEnrollRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    consent_given: bool = True


class FaceResponse(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    is_active: bool
    image_count: int
    consent_given: bool
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class FaceRecognizeResponse(BaseModel):
    """Result of a face recognition check."""
    face_id: Optional[str] = None
    name: str  # "Unknown" if no match
    confidence: float  # similarity score
    matched: bool


class FaceEmbeddingResponse(BaseModel):
    id: str
    face_id: str
    embedding_size: Optional[int] = None
    image_filename: Optional[str] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True
