# Backend — CCTV Intelligent Analysis

FastAPI backend powering the AI pipeline.

## Quick Start

```powershell
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

## API Documentation

- Swagger UI: http://localhost:8000/docs  
- ReDoc: http://localhost:8000/redoc

## Key Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/health` | System status |
| GET | `/api/videos` | List videos |
| POST | `/api/videos/upload` | Upload video |
| POST | `/api/videos/{id}/process` | Start processing |
| GET | `/api/videos/{id}/status` | Processing progress |
| GET | `/api/videos/{id}/results` | Detection results |
| GET | `/api/videos/{id}/stream` | Stream annotated video |
| GET | `/api/events` | List events (filterable) |
| GET | `/api/analytics/dashboard` | Dashboard stats |
| POST | `/api/faces/enroll` | Enroll face |
| GET | `/api/faces` | List enrolled faces |
| POST | `/api/faces/recognize` | Recognize face |

## Configuration

Copy `.env.example` to `.env` and edit as needed.

Key settings:
- `YOLO_MODEL` — model file (auto-downloaded on first run)
- `DEVICE` — `auto`, `cpu`, or `cuda`
- `CONFIDENCE_THRESHOLD` — detection confidence (0-1)
- `FACE_MATCH_THRESHOLD` — recognition similarity threshold (0-1)

## Testing

```powershell
pytest tests/ -v
```
