"""API package init - registers all routers."""
from app.api.routes_health import router as health_router
from app.api.routes_videos import router as videos_router
from app.api.routes_detection import router as detection_router
from app.api.routes_faces import router as faces_router
from app.api.routes_events import router as events_router
from app.api.routes_analytics import router as analytics_router
from app.api.routes_live import router as live_router

__all__ = [
    "health_router",
    "videos_router",
    "detection_router",
    "faces_router",
    "events_router",
    "analytics_router",
    "live_router",
]
