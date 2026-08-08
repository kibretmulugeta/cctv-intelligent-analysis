"""
Sample Video Generator for CCTV Intelligent Analysis testing.
Generates a 5-second 30fps MP4 video with moving shapes and simulated subjects.
Usage: python sample_data/create_sample_video.py
"""
import os
from pathlib import Path

def create_sample_video():
    try:
        import cv2
        import numpy as np
    except ImportError:
        print("OpenCV and numpy required to generate sample video.")
        return

    out_dir = Path(__file__).parent
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = str(out_dir / "sample_cctv.mp4")

    width, height = 640, 480
    fps = 30
    duration_sec = 5
    total_frames = fps * duration_sec

    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    out = cv2.VideoWriter(out_path, fourcc, fps, (width, height))

    print(f"Generating sample CCTV video: {out_path} ({total_frames} frames)...")

    for frame_idx in range(total_frames):
        # Dark CCTV background
        frame = np.full((height, width, 3), (20, 25, 35), dtype=np.uint8)

        # Draw CCTV grid overlay
        for y in range(0, height, 80):
            cv2.line(frame, (0, y), (width, y), (30, 35, 45), 1)
        for x in range(0, width, 80):
            cv2.line(frame, (x, 0), (x, height), (30, 35, 45), 1)

        # Timecode & Camera Name
        timestamp = f"2026-08-08 15:42:{10 + frame_idx // fps:02d} CAM_01 [EAST ENTRANCE]"
        cv2.putText(frame, timestamp, (15, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 180), 1)

        # Moving Subject 1 (Person simulation - rectangle/ellipse)
        p1_x = int(50 + (frame_idx / total_frames) * 450)
        p1_y = 200
        cv2.rectangle(frame, (p1_x, p1_y), (p1_x + 40, p1_y + 90), (100, 200, 100), -1)
        cv2.circle(frame, (p1_x + 20, p1_y - 15), 15, (120, 220, 120), -1)

        # Moving Subject 2 (Vehicle simulation)
        v_x = int(550 - (frame_idx / total_frames) * 400)
        v_y = 350
        cv2.rectangle(frame, (v_x, v_y), (v_x + 120, v_y + 50), (200, 150, 50), -1)

        # Draw ROI Monitoring Zone Box
        cv2.rectangle(frame, (100, 100), (540, 420), (255, 255, 0), 1)
        cv2.putText(frame, "MONITORING ZONE ROI", (105, 120), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 0), 1)

        out.write(frame)

    out.release()
    print(f"Sample video created successfully: {out_path}")

if __name__ == "__main__":
    create_sample_video()
