"""
Rule-based activity analyzer.
Generates events from frame-level detections using configurable thresholds.
All events are clearly labeled as rule-based (not AI action recognition).
"""
from __future__ import annotations
import logging
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field
from collections import defaultdict
import time

logger = logging.getLogger(__name__)

VEHICLE_CLASSES = {"car", "bus", "truck", "motorcycle"}


@dataclass
class AnalyzerConfig:
    """Configuration thresholds for activity analysis."""
    high_person_density_threshold: int = 5
    prolonged_presence_frames: int = 150    # ~5s at 30fps
    rapid_movement_threshold: float = 0.08  # normalized bbox movement per frame
    crowd_threshold: int = 8
    # ROI (normalized 0-1, None = whole frame)
    roi: Optional[Tuple[float, float, float, float]] = None  # x1,y1,x2,y2


@dataclass
class ActivityEvent:
    """A single rule-triggered activity event."""
    event_type: str
    severity: str
    description: str
    object_type: Optional[str] = None
    object_id: Optional[int] = None
    confidence: Optional[float] = None
    frame_number: Optional[int] = None
    timestamp_sec: Optional[float] = None
    zone_name: Optional[str] = None
    extra_data: Dict[str, Any] = field(default_factory=dict)
    source: str = "rule_based"


class ActivityAnalyzer:
    """
    Analyzes detections frame-by-frame to generate rule-based activity events.
    """

    def __init__(self, config: Optional[AnalyzerConfig] = None):
        self.config = config or AnalyzerConfig()
        self._track_entry: Dict[int, int] = {}    # track_id -> first_seen_frame inside ROI
        self._track_positions: Dict[int, List[Tuple[float, float]]] = defaultdict(list)
        self._fired_events: Dict[str, int] = {}   # event_key -> frame_number (cooldown)
        self._cooldown_frames = 90  # Minimum frames between same event type

    def set_roi(self, roi: Optional[Tuple[float, float, float, float]]) -> None:
        self.config.roi = roi

    def analyze(
        self,
        detections: List[Dict[str, Any]],
        frame_number: int,
        fps: float = 30.0,
    ) -> List[ActivityEvent]:
        """
        Analyze detections for a single frame and return triggered events.
        """
        events: List[ActivityEvent] = []
        timestamp_sec = frame_number / fps if fps > 0 else 0

        persons = [d for d in detections if d["class_name"] == "person"]
        vehicles = [d for d in detections if d["class_name"] in VEHICLE_CLASSES]
        all_objects = detections

        # --- Rule 1: Multiple people / high density ---
        person_count = len(persons)
        if person_count >= self.config.high_person_density_threshold:
            key = "HIGH_PERSON_DENSITY"
            if self._can_fire(key, frame_number):
                events.append(ActivityEvent(
                    event_type="HIGH_PERSON_DENSITY",
                    severity="warning",
                    description=f"High pedestrian density: {person_count} persons detected",
                    object_type="person",
                    confidence=None,
                    frame_number=frame_number,
                    timestamp_sec=timestamp_sec,
                    extra_data={"person_count": person_count},
                ))

        # --- Rule 2: Crowd ---
        if person_count >= self.config.crowd_threshold:
            key = "CROWD_DETECTED"
            if self._can_fire(key, frame_number):
                events.append(ActivityEvent(
                    event_type="CROWD_DETECTED",
                    severity="alert",
                    description=f"Crowd detected: {person_count} persons in frame",
                    object_type="person",
                    frame_number=frame_number,
                    timestamp_sec=timestamp_sec,
                    extra_data={"person_count": person_count},
                ))

        # --- Rule 3: ROI entry/exit ---
        if self.config.roi is not None:
            roi_events = self._check_roi(all_objects, frame_number, timestamp_sec)
            events.extend(roi_events)

        # --- Rule 4: Prolonged presence ---
        prolonged_events = self._check_prolonged(detections, frame_number, timestamp_sec, fps)
        events.extend(prolonged_events)

        # --- Rule 5: Rapid movement ---
        rapid_events = self._check_rapid_movement(detections, frame_number, timestamp_sec)
        events.extend(rapid_events)

        # --- Rule 6: Multiple people entering (generic) ---
        if person_count > 1 and person_count < self.config.high_person_density_threshold:
            key = f"MULTIPLE_PEOPLE_{person_count}"
            if self._can_fire(key, frame_number):
                events.append(ActivityEvent(
                    event_type="MULTIPLE_PEOPLE",
                    severity="info",
                    description=f"{person_count} people detected in frame",
                    object_type="person",
                    frame_number=frame_number,
                    timestamp_sec=timestamp_sec,
                    extra_data={"person_count": person_count},
                ))

        return events

    def _can_fire(self, key: str, frame_number: int) -> bool:
        """Check cooldown before firing same event repeatedly."""
        if key in self._fired_events:
            if frame_number - self._fired_events[key] < self._cooldown_frames:
                return False
        self._fired_events[key] = frame_number
        return True

    def _is_in_roi(self, bbox: List[float]) -> bool:
        """Check if a bounding box center is inside the configured ROI."""
        if self.config.roi is None:
            return True
        rx1, ry1, rx2, ry2 = self.config.roi
        cx = (bbox[0] + bbox[2]) / 2
        cy = (bbox[1] + bbox[3]) / 2
        return rx1 <= cx <= rx2 and ry1 <= cy <= ry2

    def _check_roi(
        self,
        detections: List[Dict[str, Any]],
        frame_number: int,
        timestamp_sec: float,
    ) -> List[ActivityEvent]:
        events = []
        active_ids = set()

        for det in detections:
            track_id = det.get("track_id")
            if track_id is None:
                continue

            in_roi = self._is_in_roi(det["bbox"])
            active_ids.add(track_id)

            if in_roi and track_id not in self._track_entry:
                self._track_entry[track_id] = frame_number
                is_vehicle = det["class_name"] in VEHICLE_CLASSES
                event_type = "VEHICLE_ENTERED_ZONE" if is_vehicle else "PERSON_ENTERED_ZONE"
                key = f"{event_type}_{track_id}"
                if self._can_fire(key, frame_number):
                    events.append(ActivityEvent(
                        event_type=event_type,
                        severity="info",
                        description=f"{det['class_name'].title()} #{track_id} entered monitoring zone",
                        object_type=det["class_name"],
                        object_id=track_id,
                        confidence=det.get("confidence"),
                        frame_number=frame_number,
                        timestamp_sec=timestamp_sec,
                        zone_name="Monitoring Zone",
                    ))
            elif not in_roi and track_id in self._track_entry:
                del self._track_entry[track_id]
                is_vehicle = det["class_name"] in VEHICLE_CLASSES
                event_type = "VEHICLE_LEFT_ZONE" if is_vehicle else "PERSON_LEFT_ZONE"
                key = f"{event_type}_{track_id}"
                if self._can_fire(key, frame_number):
                    events.append(ActivityEvent(
                        event_type=event_type,
                        severity="info",
                        description=f"{det['class_name'].title()} #{track_id} left monitoring zone",
                        object_type=det["class_name"],
                        object_id=track_id,
                        frame_number=frame_number,
                        timestamp_sec=timestamp_sec,
                        zone_name="Monitoring Zone",
                    ))

        return events

    def _check_prolonged(
        self,
        detections: List[Dict[str, Any]],
        frame_number: int,
        timestamp_sec: float,
        fps: float,
    ) -> List[ActivityEvent]:
        events = []
        threshold = self.config.prolonged_presence_frames

        for det in detections:
            track_id = det.get("track_id")
            if track_id is None:
                continue
            frame_count = det.get("_frame_count", 0)
            if frame_count >= threshold and frame_count % (threshold // 2) == 0:
                key = f"PROLONGED_{track_id}"
                if self._can_fire(key, frame_number):
                    duration = frame_count / fps if fps > 0 else 0
                    events.append(ActivityEvent(
                        event_type="PROLONGED_PRESENCE",
                        severity="warning",
                        description=f"{det['class_name'].title()} #{track_id} in zone for {duration:.1f}s",
                        object_type=det["class_name"],
                        object_id=track_id,
                        confidence=det.get("confidence"),
                        frame_number=frame_number,
                        timestamp_sec=timestamp_sec,
                        extra_data={"duration_seconds": round(duration, 1), "frame_count": frame_count},
                    ))
        return events

    def _check_rapid_movement(
        self,
        detections: List[Dict[str, Any]],
        frame_number: int,
        timestamp_sec: float,
    ) -> List[ActivityEvent]:
        events = []

        for det in detections:
            track_id = det.get("track_id")
            if track_id is None:
                continue

            bbox = det["bbox"]
            cx = (bbox[0] + bbox[2]) / 2
            cy = (bbox[1] + bbox[3]) / 2

            positions = self._track_positions[track_id]
            positions.append((cx, cy))
            if len(positions) > 10:
                positions.pop(0)

            if len(positions) >= 3:
                # Calculate movement over last 3 frames
                dx = positions[-1][0] - positions[-3][0]
                dy = positions[-1][1] - positions[-3][1]
                dist = (dx ** 2 + dy ** 2) ** 0.5

                if dist > self.config.rapid_movement_threshold:
                    key = f"RAPID_{track_id}"
                    if self._can_fire(key, frame_number):
                        events.append(ActivityEvent(
                            event_type="RAPID_MOVEMENT",
                            severity="warning",
                            description=f"Rapid movement detected: {det['class_name'].title()} #{track_id}",
                            object_type=det["class_name"],
                            object_id=track_id,
                            confidence=det.get("confidence"),
                            frame_number=frame_number,
                            timestamp_sec=timestamp_sec,
                            extra_data={"movement_dist": round(dist, 4)},
                        ))

        return events

    def reset(self) -> None:
        """Reset analyzer state (call between videos)."""
        self._track_entry.clear()
        self._track_positions.clear()
        self._fired_events.clear()
