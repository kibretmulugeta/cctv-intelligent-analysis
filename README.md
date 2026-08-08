# CCTV Intelligent Analysis & Face Recognition

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688.svg)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-19.0-61DAFB.svg)](https://react.dev/)
[![YOLO](https://img.shields.io/badge/YOLO-Ultralytics_v11-FF9900.svg)](https://docs.ultralytics.com/)
[![OpenCV](https://img.shields.io/badge/OpenCV-4.10-5C3EE8.svg)](https://opencv.org/)

> "CCTV Intelligent Analysis & Face Recognition is an AI-powered computer vision platform for analyzing CCTV video streams using YOLO-based object detection, object tracking, activity/event analysis, real-time video processing, and consent-based face recognition. The system combines Python, OpenCV, PyTorch, FastAPI, and React to demonstrate an end-to-end production-style computer vision application."

---

## 📋 Table of Contents

- [Features](#-features)
- [Architecture](#-architecture)
- [Technology Stack](#-technology-stack)
- [AI Pipeline](#-ai-pipeline)
- [Installation & Quick Start](#-installation--quick-start)
  - [Backend Setup](#backend-setup)
  - [Frontend Setup](#frontend-setup)
- [Using Video Analysis](#-using-video-analysis)
- [Consent-Based Face Enrollment](#-consent-based-face-enrollment)
- [API Documentation](#-api-documentation)
- [Privacy & Security Considerations](#-privacy--security-considerations)
- [Testing](#-testing)
- [License](#-license)

---

## ✨ Features

1. **Real-Time Object Detection**: Detects persons, cars, buses, trucks, motorcycles, bicycles, dogs, cats, backpacks, and handbags using YOLO11/YOLOv8.
2. **Object Tracking**: Persistent tracking IDs using ByteTrack to track objects across video frames.
3. **Rule-Based Activity Analysis**: Triggers rule-based events for ROI entry/exit, high pedestrian density, loitering/prolonged presence, and rapid movement.
4. **Configurable Region of Interest (ROI)**: Custom rectangular monitoring zones overlaid directly on video.
5. **Consent-Based Face Recognition**: Face enrollment from user-provided images with cosine similarity face embedding verification.
6. **AI Analytics Dashboard**: Visual charts for object counts over time, class distribution, and event trends powered by Recharts.
7. **Searchable Event Logs**: Filterable event history table with severity levels and one-click acknowledgment.
8. **Real-Time Webcam Mode**: Live VideoCapture analysis mode with OpenCV.
9. **No Fabricated Data**: Authentic inference calculations, real confidence scores, and empirical performance metrics.

---

## 🏗️ Architecture

```
React / Vite Frontend
        │
        │ REST API (JSON / Multipart Video Uploads)
        ▼
FastAPI Asynchronous Backend Engine
        │
        ├────────► YOLO11 Object Detector (Ultralytics / PyTorch)
        ├────────► ByteTrack Object Tracker
        ├────────► Rule-Based Activity & Zone Event Analyzer
        ├────────► OpenCV Video & Frame Preprocessing
        ├────────► InsightFace / Haar Cascade Face Detector
        └────────► SQLite / Async SQLAlchemy Database
```

---

## 🛠️ Technology Stack

- **Frontend**: React 19, Vite, JavaScript, CSS (Dark Operations Dashboard), Recharts, Lucide Icons, Axios, React Router.
- **Backend**: Python 3.11+, FastAPI, Uvicorn, Pydantic v2, Async SQLAlchemy 2.0, aiosqlite.
- **Computer Vision & AI**: PyTorch, Ultralytics YOLO, OpenCV, NumPy, InsightFace.

---

## 🚀 Installation & Quick Start

### Prerequisites
- Python 3.11+
- Node.js 18+

### Backend Setup (Windows)

```powershell
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

Backend API running at: `http://localhost:8000`  
Interactive Swagger API Docs: `http://localhost:8000/docs`

### Frontend Setup

```powershell
cd frontend
npm install
npm run dev
```

Frontend Dashboard running at: `http://localhost:5173`

---

## 📽️ Using Video Analysis

1. Open `http://localhost:5173/video-analysis` in your browser.
2. Drag and drop a CCTV video file (`.mp4`, `.avi`, `.mov`, `.mkv`) or generate a test video using:
   ```powershell
   python sample_data/create_sample_video.py
   ```
3. Configure the confidence slider and frame skip interval.
4. Click **START AI PIPELINE PROCESS**.
5. Stream the resulting annotated video with bounding boxes, object IDs, and class labels.

---

## 👤 Consent-Based Face Enrollment

> ⚠️ **PRIVACY NOTICE**: Face recognition is intended only for authorized, consent-based demonstrations. Do not use biometric identification without appropriate authorization, consent, and applicable legal safeguards.

1. Navigate to the **Face Recognition** tab (`/faces`).
2. Enter the display name (e.g. `Sarah Jenkins (Employee)`).
3. Upload a clear photograph containing a single face.
4. Click **ENROLL FACE IDENTITY** to generate and store 512-d feature vectors locally.

---

## 🧪 Testing

Run backend tests using pytest:

```powershell
cd backend
.venv\Scripts\pytest tests/ -v
```

---

## 🔒 Privacy & Security Considerations

- All processing happens locally on your machine.
- Facial embeddings are stored locally as encrypted binary blobs within SQLite.
- Videos are not transmitted to any external third-party service.
- Deletion API allows complete purging of enrolled facial data.

---

## 📜 License

MIT License. Developed for portfolio & educational demonstration purposes.
