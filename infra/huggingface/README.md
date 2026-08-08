---
title: CCTV Intelligent Analysis & Face Recognition API
emoji: 🎥
colorFrom: blue
colorTo: green
sdk: docker
app_port: 7860
pinned: false
---

# CCTV Intelligent Analysis & Face Recognition (24/7 CPU Backend API)

FastAPI computer vision backend for real-time video object detection (YOLO11), tracking (ByteTrack), rule-based security activity analysis, consent-based face recognition, and Prometheus MLOps observability.

## How to Deploy to Hugging Face Spaces

1. Create a new Space on [Hugging Face Spaces](https://huggingface.co/new-space).
2. Enter Space Name: `cctv-ai-backend` (or your preferred name).
3. Select SDK: **Docker**.
4. Run the following Git commands locally to push the backend:

```bash
# Add Hugging Face Space Git Remote
git remote add hf https://huggingface.co/spaces/YOUR_USERNAME/cctv-ai-backend

# Push to Hugging Face Spaces
git push hf main
```
