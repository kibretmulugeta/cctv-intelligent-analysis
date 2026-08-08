"""
Backend tests for Phase 1 - basic health and structure tests.
Run with: pytest tests/ -v
"""
import pytest
import asyncio
from httpx import AsyncClient, ASGITransport


# =========================================================
# Fixtures
# =========================================================

@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
async def app():
    """Create test FastAPI app with in-memory SQLite."""
    import os
    os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///./test_cctv.db"
    os.environ["YOLO_MODEL"] = "yolo11n.pt"  # Will use demo mode in tests
    os.environ["DEVICE"] = "cpu"

    from app.main import app as fastapi_app
    from app.database import init_db
    await init_db()
    return fastapi_app


@pytest.fixture
async def client(app):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac


# =========================================================
# Health Tests
# =========================================================

@pytest.mark.asyncio
async def test_health_endpoint(client):
    """Test health endpoint returns status online."""
    response = await client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "online"
    assert "yolo_mode" in data
    assert "device" in data
    print(f"\n  Health check: {data}")


@pytest.mark.asyncio
async def test_root_endpoint(client):
    """Test root endpoint returns app info."""
    response = await client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "name" in data
    assert "privacy_notice" in data


# =========================================================
# Video Tests
# =========================================================

@pytest.mark.asyncio
async def test_list_videos_empty(client):
    """Test listing videos when none exist."""
    response = await client.get("/api/videos")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


@pytest.mark.asyncio
async def test_upload_invalid_format(client):
    """Test that invalid file formats are rejected."""
    response = await client.post(
        "/api/videos/upload",
        files={"file": ("test.txt", b"not a video", "text/plain")},
    )
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_video_not_found(client):
    """Test 404 for non-existent video."""
    response = await client.get("/api/videos/nonexistent-id")
    assert response.status_code == 404


# =========================================================
# Events Tests
# =========================================================

@pytest.mark.asyncio
async def test_list_events_empty(client):
    """Test listing events when none exist."""
    response = await client.get("/api/events")
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "total" in data
    assert data["total"] == 0


# =========================================================
# Face Tests
# =========================================================

@pytest.mark.asyncio
async def test_list_faces_empty(client):
    """Test listing faces when none are enrolled."""
    response = await client.get("/api/faces")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


@pytest.mark.asyncio
async def test_enroll_invalid_file(client):
    """Test that non-image files are rejected for enrollment."""
    response = await client.post(
        "/api/faces/enroll",
        data={"name": "Test Person"},
        files={"image": ("test.txt", b"not an image", "text/plain")},
    )
    assert response.status_code == 400


# =========================================================
# Analytics Tests
# =========================================================

@pytest.mark.asyncio
async def test_dashboard_stats(client):
    """Test analytics dashboard returns valid structure."""
    response = await client.get("/api/analytics/dashboard")
    assert response.status_code == 200
    data = response.json()
    assert "total_videos" in data
    assert "total_detections" in data
    assert "total_events" in data


@pytest.mark.asyncio
async def test_class_distribution_empty(client):
    """Test class distribution returns empty list when no data."""
    response = await client.get("/api/analytics/class-distribution")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


# =========================================================
# AI Component Tests (no GPU required)
# =========================================================

def test_yolo_detector_init():
    """Test YOLO detector initializes without crashing."""
    from app.ai.yolo_detector import YOLODetector
    det = YOLODetector(model_path="yolo11n.pt", device="cpu")
    assert det.mode in ("inference", "demo")
    print(f"\n  YOLO mode: {det.mode}")


def test_yolo_demo_detections():
    """Test demo detections are returned when model unavailable."""
    import numpy as np
    from app.ai.yolo_detector import YOLODetector
    det = YOLODetector.__new__(YOLODetector)
    det.is_available = False
    det.model = None

    frame = np.zeros((480, 640, 3), dtype=np.uint8)
    results = det._demo_detections(frame)
    assert len(results) > 0
    for r in results:
        assert "class_name" in r
        assert "confidence" in r
        assert "bbox" in r
        assert r["_demo"] is True


def test_object_tracker():
    """Test object tracker state management."""
    from app.ai.object_tracker import ObjectTracker
    tracker = ObjectTracker()

    detections = [
        {"class_name": "person", "confidence": 0.9, "bbox": [0.1, 0.1, 0.3, 0.5], "track_id": 1},
        {"class_name": "car", "confidence": 0.85, "bbox": [0.5, 0.1, 0.8, 0.4], "track_id": 2},
    ]
    tracker.update(detections, frame_number=0)
    assert len(tracker.tracks) == 2

    tracker.update(detections, frame_number=1)
    assert tracker.tracks[1].frame_count == 2
    assert tracker.tracks[2].frame_count == 2

    all_tracks = tracker.get_all_tracks()
    assert len(all_tracks) == 2


def test_activity_analyzer():
    """Test rule-based activity analyzer generates events."""
    from app.ai.activity_analyzer import ActivityAnalyzer, AnalyzerConfig

    config = AnalyzerConfig(high_person_density_threshold=3)
    analyzer = ActivityAnalyzer(config)

    # Simulate 5 people in frame
    detections = [
        {"class_name": "person", "confidence": 0.9, "bbox": [0.1*i, 0.1, 0.2*i, 0.5], "track_id": i}
        for i in range(1, 6)
    ]
    events = analyzer.analyze(detections, frame_number=0, fps=30.0)
    event_types = [e.event_type for e in events]
    assert "HIGH_PERSON_DENSITY" in event_types


def test_face_recognizer_cosine():
    """Test cosine similarity calculation."""
    from app.ai.face_recognizer import _cosine_similarity
    import numpy as np

    a = np.array([1.0, 0.0, 0.0])
    b = np.array([1.0, 0.0, 0.0])
    assert abs(_cosine_similarity(a, b) - 1.0) < 1e-6

    c = np.array([0.0, 1.0, 0.0])
    assert abs(_cosine_similarity(a, c)) < 1e-6


def test_face_recognizer_no_enrolled():
    """Test recognizer returns Unknown when no faces enrolled."""
    import numpy as np
    from app.ai.face_recognizer import FaceRecognizer
    recognizer = FaceRecognizer(threshold=0.5)
    embedding = np.random.randn(512).astype(np.float32)
    result = recognizer.recognize(embedding)
    assert result["name"] == "Unknown"
    assert result["matched"] is False
