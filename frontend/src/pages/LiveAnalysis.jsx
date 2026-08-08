import React, { useState } from "react";
import { Camera, StopCircle, AlertCircle } from "lucide-react";
import PrivacyNotice from "../components/PrivacyNotice";

export default function LiveAnalysis() {
  const [isStreaming, setIsStreaming] = useState(false);
  const [error, setError] = useState(null);

  const streamUrl = "http://127.0.0.1:8000/api/live/stream?camera_id=0";

  const startCamera = () => {
    setIsStreaming(true);
    setError(null);
  };

  const stopCamera = async () => {
    setIsStreaming(false);
    try {
      await fetch("http://127.0.0.1:8000/api/live/stop", { method: "POST" });
    } catch (err) {
      console.error("Failed to stop live camera:", err);
    }
  };

  return (
    <div>
      <PrivacyNotice />

      <div className="panel" style={{ marginBottom: "1.5rem" }}>
        <div className="panel-header">
          <div className="panel-title">
            <Camera size={20} color="#10b981" />
            Laptop Live Camera AI Feed
          </div>
          <div style={{ display: "flex", gap: "0.5rem" }}>
            {!isStreaming ? (
              <button className="btn btn-primary" onClick={startCamera}>
                <Camera size={16} /> START CAMERA
              </button>
            ) : (
              <button className="btn btn-danger" onClick={stopCamera}>
                <StopCircle size={16} /> STOP CAMERA
              </button>
            )}
          </div>
        </div>

        <div className="panel-body">
          {error && (
            <div style={{ padding: "0.75rem", background: "rgba(239, 68, 68, 0.15)", border: "1px solid #ef4444", borderRadius: "0.4rem", color: "#f87171", fontSize: "0.85rem", marginBottom: "1rem" }}>
              <AlertCircle size={16} inline /> {error}
            </div>
          )}

          <div className="video-wrapper">
            {isStreaming ? (
              <img
                src={streamUrl}
                alt="Laptop Live Camera Feed"
                style={{ width: "100%", height: "100%", objectFit: "contain" }}
                onError={() => {
                  setError("Cannot open laptop camera. Ensure camera permissions are granted and index 0 is available.");
                  setIsStreaming(false);
                }}
              />
            ) : (
              <div style={{ textAlign: "center", color: "#6b7280", padding: "4rem" }}>
                <Camera size={48} style={{ marginBottom: "1rem", opacity: 0.5 }} />
                <div style={{ fontSize: "1.1rem", fontWeight: 600, color: "#fff" }}>Camera Offline</div>
                <div style={{ fontSize: "0.85rem", marginTop: "0.5rem" }}>
                  Click "START CAMERA" to launch live YOLO detection & Face Recognition on your laptop camera.
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
