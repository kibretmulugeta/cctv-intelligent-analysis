"""Face enrollment and recognition routes."""
from __future__ import annotations
import logging
from typing import List

from fastapi import APIRouter, Depends, File, UploadFile, Form, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.models.face import Face, FaceEmbedding
from app.schemas.face import FaceResponse, FaceEnrollRequest
from app.services.face_service import enroll_face, get_enrolled_faces_for_recognizer
from app.services.video_service import get_face_detector, get_face_recognizer

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/faces", tags=["faces"])


@router.get("", response_model=List[FaceResponse])
async def list_faces(db: AsyncSession = Depends(get_db)):
    """List all enrolled identities."""
    result = await db.execute(select(Face).order_by(Face.created_at.desc()))
    return result.scalars().all()


@router.post("/enroll")
async def enroll_face_endpoint(
    name: str = Form(...),
    description: str = Form(default=""),
    image: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
):
    """
    Enroll a new face identity from an uploaded image.
    
    PRIVACY NOTICE: Face recognition is intended only for authorized,
    consent-based demonstrations. Do not use biometric identification
    without appropriate authorization, consent, and applicable legal safeguards.
    """
    if not image.content_type or not image.content_type.startswith("image/"):
        raise HTTPException(400, "File must be an image (JPEG, PNG, etc.)")

    content = await image.read()
    if len(content) > 10 * 1024 * 1024:  # 10MB limit for images
        raise HTTPException(413, "Image too large. Maximum 10MB.")

    face_detector = get_face_detector()
    face_recognizer = get_face_recognizer()

    result = await enroll_face(
        db=db,
        name=name,
        image_data=content,
        image_filename=image.filename or "image.jpg",
        face_detector=face_detector,
        face_recognizer=face_recognizer,
        description=description or None,
    )

    if not result["success"]:
        raise HTTPException(400, result["error"])

    return result


@router.delete("/{face_id}")
async def delete_face(face_id: str, db: AsyncSession = Depends(get_db)):
    """Delete an enrolled face identity and all its embeddings."""
    result = await db.execute(select(Face).where(Face.id == face_id))
    face = result.scalar_one_or_none()
    if not face:
        raise HTTPException(404, "Face not found")

    await db.delete(face)
    await db.commit()

    logger.info(f"Deleted face: {face.name} ({face_id})")
    return {"message": f"Face '{face.name}' deleted successfully"}


@router.get("/{face_id}", response_model=FaceResponse)
async def get_face(face_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Face).where(Face.id == face_id))
    face = result.scalar_one_or_none()
    if not face:
        raise HTTPException(404, "Face not found")
    return face


@router.post("/recognize")
async def recognize_face(
    image: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
):
    """Run face recognition on an uploaded image against enrolled identities."""
    content = await image.read()
    import numpy as np
    import cv2

    arr = np.frombuffer(content, dtype=np.uint8)
    img = cv2.imdecode(arr, cv2.IMREAD_COLOR)
    if img is None:
        raise HTTPException(400, "Cannot decode image")

    face_detector = get_face_detector()
    face_recognizer = get_face_recognizer()

    if not face_detector.is_available:
        raise HTTPException(503, "Face detection unavailable")

    # Load enrolled faces into recognizer
    enrolled = await get_enrolled_faces_for_recognizer(db)
    face_recognizer.load_enrolled(enrolled)

    faces = face_detector.detect(img)
    if not faces:
        raise HTTPException(400, "No face detected in image")

    results = []
    for face in faces:
        embedding = face.get("embedding")
        recognition = face_recognizer.recognize(embedding)
        results.append({
            "bbox": face["bbox"],
            "detection_confidence": face["confidence"],
            "recognition": recognition,
        })

    return {"faces": results, "total": len(results)}
