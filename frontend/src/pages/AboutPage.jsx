import React from "react";
import { Cpu, Shield, Database, Video, ArrowRight, Code } from "lucide-react";

export default function AboutPage() {
  return (
    <div style={{ maxWidth: "900px" }}>
      <div className="panel" style={{ marginBottom: "1.5rem" }}>
        <div className="panel-header">
          <div className="panel-title">
            <Shield size={20} color="#10b981" />
            CCTV Intelligent Analysis & Face Recognition
          </div>
        </div>

        <div className="panel-body">
          <p style={{ fontSize: "0.95rem", lineHeight: 1.6, color: "#d1d5db", marginBottom: "1.5rem" }}>
            "CCTV Intelligent Analysis & Face Recognition is an AI-powered computer vision platform for analyzing CCTV video streams using YOLO-based object detection, object tracking, activity/event analysis, real-time video processing, and consent-based face recognition. The system combines Python, OpenCV, PyTorch, FastAPI, and React to demonstrate an end-to-end production-style computer vision application."
          </p>

          <h3 style={{ fontSize: "1rem", color: "#fff", marginBottom: "1rem" }}>Technology Tags</h3>
          <div style={{ display: "flex", gap: "0.5rem", flexWrap: "wrap", marginBottom: "2rem" }}>
            {[
              "Python",
              "PyTorch",
              "YOLO11",
              "OpenCV",
              "Computer Vision",
              "Deep Learning",
              "FastAPI",
              "React",
              "JavaScript",
              "SQLite",
            ].map((tag) => (
              <span
                key={tag}
                style={{
                  background: "rgba(16, 185, 129, 0.15)",
                  border: "1px solid rgba(16, 185, 129, 0.3)",
                  color: "#10b981",
                  padding: "0.3rem 0.75rem",
                  borderRadius: "9999px",
                  fontSize: "0.8rem",
                  fontWeight: 600,
                  fontFamily: "var(--font-mono)",
                }}
              >
                {tag}
              </span>
            ))}
          </div>

          <h3 style={{ fontSize: "1rem", color: "#fff", marginBottom: "1rem" }}>System Architecture Pipeline</h3>
          <div
            style={{
              background: "var(--bg-input)",
              padding: "1.5rem",
              borderRadius: "0.5rem",
              fontFamily: "var(--font-mono)",
              fontSize: "0.85rem",
              lineHeight: 1.8,
              color: "#06b6d4",
              border: "1px solid var(--border-color)",
            }}
          >
            Video Input / Live Webcam
            <br />
            ↓<br />
            OpenCV Frame Extraction & Preprocessing
            <br />
            ↓<br />
            YOLO Object Detection (Person, Vehicles, Bicycles)
            <br />
            ↓<br />
            Object Tracking (ByteTrack / TrackState History)
            <br />
            ↓<br />
            Rule-Based Activity Analysis (Crowd, Prolonged Presence, ROI Entry/Exit)
            <br />
            ↓<br />
            Face Detection & Consent-Based Face Recognition
            <br />
            ↓<br />
            FastAPI Asynchronous Backend Engine
            <br />
            ↓<br />
            React Modern Operations Dashboard
          </div>
        </div>
      </div>
    </div>
  );
}
