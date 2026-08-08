"""
Celery Task Definitions for Video Pipeline Processing.
Executes frame-by-frame object detection, tracking, activity rules, and face recognition.
"""
import logging
from app.tasks.celery_app import celery_app, IS_CELERY_AVAILABLE
from app.metrics import ACTIVE_JOBS, TOTAL_FRAMES_PROCESSED

logger = logging.getLogger(__name__)

if IS_CELERY_AVAILABLE and celery_app:
    @celery_app.task(bind=True, name="process_video_task")
    def process_video_task(self, video_id: str, config_dict: dict):
        """Celery background task for asynchronous video pipeline execution."""
        logger.info(f"Starting Celery processing job for video_id={video_id}")
        ACTIVE_JOBS.inc()

        try:
            # Synchronous execution inside Celery worker
            import asyncio
            from app.database import async_session
            from app.services.video_service import VideoProcessingJob

            async def _run():
                async with async_session() as db:
                    job = VideoProcessingJob(
                        video_id=video_id,
                        db=db,
                        confidence_threshold=config_dict.get("confidence_threshold", 0.45),
                        frame_skip=config_dict.get("frame_skip", 1),
                        enable_tracking=config_dict.get("enable_tracking", True),
                        enable_face_detection=config_dict.get("enable_face_detection", True),
                        enable_face_recognition=config_dict.get("enable_face_recognition", False),
                    )
                    await job.run()

            asyncio.run(_run())
            logger.info(f"Celery processing job completed for video_id={video_id}")
            return {"status": "completed", "video_id": video_id}

        except Exception as e:
            logger.error(f"Celery processing failed for video_id={video_id}: {str(e)}", exc_info=True)
            raise e

        finally:
            ACTIVE_JOBS.dec()
