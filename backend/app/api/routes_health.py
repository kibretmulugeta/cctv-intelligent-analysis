"""Health check routes."""
from fastapi import APIRouter
from pydantic import BaseModel
from app.config import settings
from app.services.video_service import get_yolo, get_face_detector

router = APIRouter(prefix="/api", tags=["health"])


class HealthResponse(BaseModel):
    status: str
    app_name: str
    version: str
    device: str
    yolo_model: str
    yolo_mode: str
    face_detection: str
    face_backend: str


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """Return system health and AI component status."""
    device = settings.resolve_device()
    yolo = get_yolo()
    face_det = get_face_detector()

    return HealthResponse(
        status="online",
        app_name=settings.APP_NAME,
        version=settings.APP_VERSION,
        device=device,
        yolo_model=settings.YOLO_MODEL,
        yolo_mode=yolo.mode,
        face_detection="available" if face_det.is_available else "unavailable",
        face_backend=face_det.backend or "none",
    )
