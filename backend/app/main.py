"""
CCTV Intelligent Analysis & Face Recognition
FastAPI Application Entry Point

This system is designed for authorized, consent-based demonstrations only.
Do not use for covert surveillance.
"""
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pathlib import Path

from app.config import settings
from app.database import init_db
from app.utils.logging_config import setup_logging
from app.api import (
    health_router,
    videos_router,
    detection_router,
    faces_router,
    events_router,
    analytics_router,
    live_router,
)

# Setup logging before anything else
setup_logging("DEBUG" if settings.DEBUG else "INFO")
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan - startup and shutdown."""
    logger.info(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}")

    # Initialize database
    await init_db()
    logger.info("Database initialized")

    # Ensure storage directories exist
    settings.get_upload_path()
    settings.get_output_path()
    settings.get_faces_path()
    logger.info("Storage directories ready")

    # Eagerly initialize AI components (optional - they lazy-load on first use)
    device = settings.resolve_device()
    logger.info(f"Compute device: {device.upper()}")

    # Pre-load YOLO (triggers model download if needed)
    from app.services.video_service import get_yolo, get_face_detector
    yolo = get_yolo()
    logger.info(f"YOLO detector: mode={yolo.mode}")

    face_det = get_face_detector()
    logger.info(f"Face detector: backend={face_det.backend or 'none'}")

    logger.info("=" * 60)
    logger.info(f"  {settings.APP_NAME}")
    logger.info(f"  API:  http://localhost:8000")
    logger.info(f"  Docs: http://localhost:8000/docs")
    logger.info("=" * 60)

    yield

    logger.info("Shutting down...")


# Create FastAPI application
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description=(
        "An AI-powered computer vision platform for analyzing CCTV video streams "
        "using YOLO-based object detection, object tracking, activity/event analysis, "
        "real-time video processing, and consent-based face recognition. "
        "\n\n⚠️ **Privacy Notice**: This system is for authorized, consent-based "
        "demonstrations only. Do not use biometric identification without appropriate "
        "authorization, consent, and applicable legal safeguards."
    ),
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(health_router)
app.include_router(videos_router)
app.include_router(detection_router)
app.include_router(faces_router)
app.include_router(events_router)
app.include_router(analytics_router)
app.include_router(live_router)

# Serve static output files (processed videos, etc.)
output_dir = Path(settings.OUTPUT_DIR)
output_dir.mkdir(parents=True, exist_ok=True)
app.mount("/outputs", StaticFiles(directory=str(output_dir)), name="outputs")

upload_dir = Path(settings.UPLOAD_DIR)
upload_dir.mkdir(parents=True, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=str(upload_dir)), name="uploads")


@app.get("/")
async def root():
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "docs": "/docs",
        "health": "/api/health",
        "privacy_notice": (
            "Face recognition is intended only for authorized, consent-based demonstrations. "
            "Do not use biometric identification without appropriate authorization, consent, "
            "and applicable legal safeguards."
        ),
    }
