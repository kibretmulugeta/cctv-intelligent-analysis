"""
Object tracker wrapper.
Uses YOLO's built-in ByteTrack integration when available.
Maintains an in-memory track registry across frames.
"""
from __future__ import annotations
import logging
from typing import Dict, List, Optional, Tuple, Any
from collections import defaultdict
import time

logger = logging.getLogger(__name__)


class TrackState:
    """Represents the state of a single tracked object."""

    def __init__(self, track_id: int, class_name: str, frame_number: int, confidence: float):
        self.track_id = track_id
        self.class_name = class_name
        self.first_seen_frame = frame_number
        self.last_seen_frame = frame_number
        self.frame_count = 1
        self.confidence_sum = confidence
        self.positions: List[Tuple[float, float, float, float]] = []  # (x1,y1,x2,y2) history
        self.first_seen_time = time.time()

    @property
    def avg_confidence(self) -> float:
        return self.confidence_sum / self.frame_count if self.frame_count > 0 else 0.0

    @property
    def duration_seconds(self) -> float:
        return time.time() - self.first_seen_time

    def update(self, frame_number: int, confidence: float, bbox: List[float]) -> None:
        self.last_seen_frame = frame_number
        self.frame_count += 1
        self.confidence_sum += confidence
        self.positions.append(tuple(bbox))  # type: ignore[arg-type]
        # Keep only last 30 positions to avoid memory growth
        if len(self.positions) > 30:
            self.positions.pop(0)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "track_id": self.track_id,
            "object_type": self.class_name,
            "first_seen_frame": self.first_seen_frame,
            "last_seen_frame": self.last_seen_frame,
            "frame_count": self.frame_count,
            "avg_confidence": round(self.avg_confidence, 4),
            "duration_seconds": round(self.duration_seconds, 2),
        }


class ObjectTracker:
    """
    In-memory object tracker that manages TrackState objects.
    Works alongside YOLO's built-in ByteTrack integration.
    """

    def __init__(self, max_lost_frames: int = 30):
        self.tracks: Dict[int, TrackState] = {}
        self.max_lost_frames = max_lost_frames
        self._frame_counter = 0

    def update(self, detections: List[Dict[str, Any]], frame_number: int) -> List[Dict[str, Any]]:
        """
        Update tracker with new detections from YOLO.
        Returns the same detections with enriched tracking info.
        """
        self._frame_counter = frame_number
        active_ids = set()

        for det in detections:
            track_id = det.get("track_id")
            if track_id is None:
                continue

            active_ids.add(track_id)

            if track_id not in self.tracks:
                self.tracks[track_id] = TrackState(
                    track_id=track_id,
                    class_name=det["class_name"],
                    frame_number=frame_number,
                    confidence=det["confidence"],
                )
            else:
                self.tracks[track_id].update(
                    frame_number=frame_number,
                    confidence=det["confidence"],
                    bbox=det["bbox"],
                )

            # Enrich detection with track state info
            state = self.tracks[track_id]
            det["_track_duration"] = state.duration_seconds
            det["_frame_count"] = state.frame_count

        # Prune lost tracks
        lost = [
            tid for tid, state in self.tracks.items()
            if tid not in active_ids and (frame_number - state.last_seen_frame) > self.max_lost_frames
        ]
        for tid in lost:
            del self.tracks[tid]

        return detections

    def get_all_tracks(self) -> List[Dict[str, Any]]:
        """Return all current track states."""
        return [state.to_dict() for state in self.tracks.values()]

    def get_track(self, track_id: int) -> Optional[TrackState]:
        return self.tracks.get(track_id)

    def reset(self) -> None:
        """Clear all tracks (call between videos)."""
        self.tracks.clear()
        self._frame_counter = 0
