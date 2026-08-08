"""
Face service - handles enrollment and recognition database operations.
"""
from __future__ import annotations
import logging
from typing import List, Optional, Dict, Any
import numpy as np
import io

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.face import Face, FaceEmbedding
from app.ai.face_detector import FaceDetector
from app.ai.face_recognizer import FaceRecognizer

logger = logging.getLogger(__name__)


async def enroll_face(
    db: AsyncSession,
    name: str,
    image_data: bytes,
    image_filename: str,
    face_detector: FaceDetector,
    face_recognizer: FaceRecognizer,
    description: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Enroll a face from an image.
    Returns result dict with success status.
    """
    import cv2
    # Load image
    arr = np.frombuffer(image_data, dtype=np.uint8)
    img = cv2.imdecode(arr, cv2.IMREAD_COLOR)
    if img is None:
        return {"success": False, "error": "Cannot decode image"}

    if not face_detector.is_available:
        return {"success": False, "error": "Face detection backend unavailable"}

    # Detect faces
    faces = face_detector.detect(img)
    if not faces:
        return {"success": False, "error": "No face detected in image"}
    if len(faces) > 1:
        return {"success": False, "error": f"Multiple faces detected ({len(faces)}). Please use an image with a single face."}

    face = faces[0]
    embedding = face.get("embedding")
    if embedding is None:
        return {"success": False, "error": "Face detected but embedding extraction failed (backend may not support it)"}

    # Find or create face record
    result = await db.execute(select(Face).where(Face.name == name))
    face_record = result.scalar_one_or_none()

    if not face_record:
        face_record = Face(name=name, description=description)
        db.add(face_record)
        await db.flush()

    # Serialize embedding
    embedding_bytes = face_recognizer.embedding_to_bytes(embedding)

    # Save embedding
    emb_record = FaceEmbedding(
        face_id=face_record.id,
        embedding_blob=embedding_bytes,
        embedding_size=len(embedding),
        image_filename=image_filename,
    )
    db.add(emb_record)

    # Update image count
    face_record.image_count = (face_record.image_count or 0) + 1

    await db.commit()
    await db.refresh(face_record)

    logger.info(f"Enrolled face for '{name}' (id: {face_record.id})")
    return {"success": True, "face_id": face_record.id, "name": name}


async def get_enrolled_faces_for_recognizer(db: AsyncSession) -> List[Dict[str, Any]]:
    """Load all enrolled face embeddings for the recognizer."""
    result = await db.execute(
        select(Face).where(Face.is_active == True)  # noqa: E712
    )
    faces = result.scalars().all()

    output = []
    for face in faces:
        emb_result = await db.execute(
            select(FaceEmbedding).where(FaceEmbedding.face_id == face.id)
        )
        embeddings = emb_result.scalars().all()
        output.append({
            "face_id": face.id,
            "name": face.name,
            "embeddings": [e.embedding_blob for e in embeddings],
        })

    return output
