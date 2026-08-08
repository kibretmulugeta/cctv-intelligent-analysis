"""
Application configuration management.
All settings are loaded from environment variables or .env file.
"""
from pydantic_settings import BaseSettings
from pydantic import Field
from pathlib import Path
from typing import List
import os


class Settings(BaseSettings):
    # App
    APP_NAME: str = "CCTV Intelligent Analysis"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False

    # Database
    DATABASE_URL: str = "sqlite+aiosqlite:///./cctv.db"

    # YOLO Model
    YOLO_MODEL: str = "yolo11n.pt"
    CONFIDENCE_THRESHOLD: float = 0.45
    IOU_THRESHOLD: float = 0.45
    DEVICE: str = "auto"  # auto, cpu, cuda

    # Frame Processing
    FRAME_SKIP: int = 1
    FACE_FRAME_INTERVAL: int = 5
    OBJECT_DETECTION_INTERVAL: int = 1

    # Face Recognition
    FACE_MATCH_THRESHOLD: float = 0.50

    # Upload Settings
    MAX_UPLOAD_SIZE_MB: int = 500
    ALLOWED_VIDEO_EXTENSIONS: str = "mp4,avi,mov,mkv"

    # Directories (relative to backend root)
    UPLOAD_DIR: str = "uploads"
    OUTPUT_DIR: str = "outputs"
    FACES_DIR: str = "faces"

    # CORS
    ALLOWED_ORIGINS: str = "http://localhost:5173,http://localhost:3000,http://127.0.0.1:5173"

    class Config:
        env_file = ".env"
        extra = "ignore"

    @property
    def allowed_origins_list(self) -> List[str]:
        return [o.strip() for o in self.ALLOWED_ORIGINS.split(",")]

    @property
    def allowed_extensions_list(self) -> List[str]:
        return [e.strip().lower() for e in self.ALLOWED_VIDEO_EXTENSIONS.split(",")]

    @property
    def max_upload_bytes(self) -> int:
        return self.MAX_UPLOAD_SIZE_MB * 1024 * 1024

    def get_upload_path(self) -> Path:
        p = Path(self.UPLOAD_DIR)
        p.mkdir(parents=True, exist_ok=True)
        return p

    def get_output_path(self) -> Path:
        p = Path(self.OUTPUT_DIR)
        p.mkdir(parents=True, exist_ok=True)
        return p

    def get_faces_path(self) -> Path:
        p = Path(self.FACES_DIR)
        p.mkdir(parents=True, exist_ok=True)
        return p

    def resolve_device(self) -> str:
        """Resolve 'auto' to actual device string."""
        if self.DEVICE == "auto":
            try:
                import torch
                return "cuda" if torch.cuda.is_available() else "cpu"
            except ImportError:
                return "cpu"
        return self.DEVICE


settings = Settings()
