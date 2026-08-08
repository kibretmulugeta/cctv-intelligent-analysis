"""
Celery Application Config.
Connects to Redis broker for distributed background task queueing.
"""
import os
import logging

logger = logging.getLogger(__name__)

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

try:
    from celery import Celery
    celery_app = Celery(
        "cctv_tasks",
        broker=REDIS_URL,
        backend=REDIS_URL,
        include=["app.tasks.video_tasks"],
    )
    celery_app.conf.update(
        task_serializer="json",
        accept_content=["json"],
        result_serializer="json",
        timezone="UTC",
        enable_utc=True,
        task_track_started=True,
    )
    IS_CELERY_AVAILABLE = True
except ImportError:
    logger.warning("Celery/Redis not installed. Asynchronous tasks will run using FastAPI background tasks fallback.")
    celery_app = None
    IS_CELERY_AVAILABLE = False
