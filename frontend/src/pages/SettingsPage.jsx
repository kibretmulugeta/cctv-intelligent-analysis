import React, { useState } from "react";
import { Settings, Save, RefreshCw } from "lucide-react";

export default function SettingsPage() {
  const [settings, setSettings] = useState({
    model_name: "yolo11n.pt",
    confidence_threshold: 0.45,
    iou_threshold: 0.45,
    device: "auto",
    frame_skip: 1,
    face_interval: 5,
    face_match_threshold: 0.50,
    roi_x1: 0.1,
    roi_y1: 0.1,
    roi_x2: 0.9,
    roi_y2: 0.9,
  });

  const [saved, setSaved] = useState(false);

  const handleSave = (e) => {
    e.preventDefault();
    setSaved(true);
    setTimeout(() => setSaved(false), 3000);
  };

  return (
    <div style={{ maxWidth: "800px" }}>
      <div className="panel">
        <div className="panel-header">
          <div className="panel-title">
            <Settings size={18} color="#10b981" />
            AI Computer Vision Model & System Settings
          </div>
        </div>

        <div className="panel-body">
          {saved && (
            <div style={{ padding: "0.75rem", background: "rgba(16, 185, 129, 0.15)", border: "1px solid #10b981", borderRadius: "0.4rem", color: "#10b981", fontSize: "0.85rem", marginBottom: "1rem" }}>
              Configuration updated successfully!
            </div>
          )}

          <form onSubmit={handleSave}>
            <h4 style={{ color: "#fff", marginBottom: "1rem", fontSize: "0.9rem", borderBottom: "1px solid var(--border-color)", paddingBottom: "0.5rem" }}>
              YOLO Object Detector
            </h4>

            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "1rem", marginBottom: "1.25rem" }}>
              <div className="form-group">
                <label className="form-label">YOLO Model Weight</label>
                <select
                  value={settings.model_name}
                  onChange={(e) => setSettings({ ...settings, model_name: e.target.value })}
                  className="form-select"
                >
                  <option value="yolo11n.pt">YOLO11 Nano (yolo11n.pt - Fast)</option>
                  <option value="yolo11s.pt">YOLO11 Small (yolo11s.pt - Balanced)</option>
                  <option value="yolov8n.pt">YOLOv8 Nano (yolov8n.pt)</option>
                </select>
              </div>

              <div className="form-group">
                <label className="form-label">Execution Device</label>
                <select
                  value={settings.device}
                  onChange={(e) => setSettings({ ...settings, device: e.target.value })}
                  className="form-select"
                >
                  <option value="auto">Auto (Detect CUDA GPU or CPU)</option>
                  <option value="cpu">CPU Only</option>
                  <option value="cuda">CUDA GPU</option>
                </select>
              </div>

              <div className="form-group">
                <label className="form-label">Detection Confidence Threshold ({settings.confidence_threshold})</label>
                <input
                  type="range"
                  min="0.1"
                  max="0.9"
                  step="0.05"
                  value={settings.confidence_threshold}
                  onChange={(e) => setSettings({ ...settings, confidence_threshold: parseFloat(e.target.value) })}
                  className="form-input"
                />
              </div>

              <div className="form-group">
                <label className="form-label">IOU Threshold ({settings.iou_threshold})</label>
                <input
                  type="range"
                  min="0.1"
                  max="0.9"
                  step="0.05"
                  value={settings.iou_threshold}
                  onChange={(e) => setSettings({ ...settings, iou_threshold: parseFloat(e.target.value) })}
                  className="form-input"
                />
              </div>
            </div>

            <h4 style={{ color: "#fff", marginBottom: "1rem", fontSize: "0.9rem", borderBottom: "1px solid var(--border-color)", paddingBottom: "0.5rem" }}>
              Performance & Face Intervals
            </h4>

            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "1rem", marginBottom: "1.25rem" }}>
              <div className="form-group">
                <label className="form-label">Object Detection Frame Skip (frames)</label>
                <input
                  type="number"
                  min="1"
                  max="10"
                  value={settings.frame_skip}
                  onChange={(e) => setSettings({ ...settings, frame_skip: parseInt(e.target.value) })}
                  className="form-input"
                />
              </div>

              <div className="form-group">
                <label className="form-label">Face Recognition Interval (frames)</label>
                <input
                  type="number"
                  min="1"
                  max="30"
                  value={settings.face_interval}
                  onChange={(e) => setSettings({ ...settings, face_interval: parseInt(e.target.value) })}
                  className="form-input"
                />
              </div>
            </div>

            <button type="submit" className="btn btn-primary">
              <Save size={16} /> SAVE CONFIGURATION
            </button>
          </form>
        </div>
      </div>
    </div>
  );
}
