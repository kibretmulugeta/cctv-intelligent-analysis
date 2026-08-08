import React, { useState, useEffect } from "react";
import { Upload, Play, CheckCircle, AlertTriangle, FileVideo, Cpu, Eye } from "lucide-react";
import VideoPlayer from "../components/VideoPlayer";
import { videosApi } from "../services/api";

export default function VideoAnalysis() {
  const [videos, setVideos] = useState([]);
  const [selectedVideo, setSelectedVideo] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [processing, setProcessing] = useState(false);
  const [processStatus, setProcessStatus] = useState(null);
  const [results, setResults] = useState(null);
  const [error, setError] = useState(null);

  // Configuration options
  const [config, setConfig] = useState({
    confidence_threshold: 0.45,
    frame_skip: 1,
    enable_tracking: true,
    enable_face_detection: true,
    enable_face_recognition: false,
  });

  useEffect(() => {
    loadVideos();
  }, []);

  const loadVideos = async () => {
    try {
      const res = await videosApi.listVideos();
      setVideos(res.data);
      if (res.data.length > 0 && !selectedVideo) {
        setSelectedVideo(res.data[0]);
        if (res.data[0].status === "completed") {
          loadResults(res.data[0].id);
        }
      }
    } catch (err) {
      console.error("Failed to load videos:", err);
    }
  };

  const loadResults = async (videoId) => {
    try {
      const res = await videosApi.getResults(videoId);
      setResults(res.data);
    } catch (err) {
      console.error("Failed to load video results:", err);
    }
  };

  const handleFileUpload = async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    setUploading(true);
    setUploadProgress(0);
    setError(null);

    const formData = new FormData();
    formData.append("file", file);

    try {
      const res = await videosApi.uploadVideo(formData, (percent) => setUploadProgress(percent));
      setSelectedVideo(res.data);
      loadVideos();
    } catch (err) {
      setError(err.response?.data?.detail || "Upload failed. Check file format.");
    } finally {
      setUploading(false);
    }
  };

  const handleStartProcess = async () => {
    if (!selectedVideo) return;
    setProcessing(true);
    setError(null);
    try {
      await videosApi.processVideo(selectedVideo.id, config);
      pollStatus(selectedVideo.id);
    } catch (err) {
      setError(err.response?.data?.detail || "Failed to start processing.");
      setProcessing(false);
    }
  };

  const pollStatus = (videoId) => {
    const interval = setInterval(async () => {
      try {
        const res = await videosApi.getStatus(videoId);
        setProcessStatus(res.data);
        if (res.data.status === "completed") {
          clearInterval(interval);
          setProcessing(false);
          loadVideos();
          loadResults(videoId);
        } else if (res.data.status === "failed") {
          clearInterval(interval);
          setProcessing(false);
          setError(res.data.error_message || "Video processing failed.");
        }
      } catch (err) {
        clearInterval(interval);
        setProcessing(false);
      }
    }, 1500);
  };

  return (
    <div>
      <div className="grid-2">
        {/* Upload & Options Panel */}
        <div className="panel">
          <div className="panel-header">
            <div className="panel-title">
              <Upload size={18} color="#10b981" />
              CCTV Video Upload & Pipeline Options
            </div>
          </div>

          <div className="panel-body">
            {error && (
              <div style={{ padding: "0.75rem", background: "rgba(239, 68, 68, 0.15)", border: "1px solid #ef4444", borderRadius: "0.4rem", color: "#f87171", fontSize: "0.85rem", marginBottom: "1rem" }}>
                <AlertTriangle size={16} inline /> {error}
              </div>
            )}

            {/* Dropzone */}
            <label
              style={{
                display: "flex",
                flexDirection: "column",
                alignItems: "center",
                justifyContent: "center",
                border: "2px dashed var(--border-light)",
                borderRadius: "0.5rem",
                padding: "2rem",
                cursor: "pointer",
                backgroundColor: "rgba(255, 255, 255, 0.02)",
                marginBottom: "1.25rem",
                transition: "border-color 0.2s",
              }}
            >
              <FileVideo size={36} color="#06b6d4" style={{ marginBottom: "0.5rem" }} />
              <div style={{ fontWeight: 600, color: "#fff" }}>Drop CCTV Video File Here</div>
              <div style={{ fontSize: "0.78rem", color: "#9ca3af", marginTop: "0.25rem" }}>
                Supports MP4, AVI, MOV, MKV (Max 500MB)
              </div>
              <input type="file" accept="video/*" onChange={handleFileUpload} style={{ display: "none" }} />
            </label>

            {uploading && (
              <div style={{ marginBottom: "1.25rem" }}>
                <div style={{ fontSize: "0.8rem", color: "#9ca3af", marginBottom: "0.25rem" }}>
                  Uploading: {uploadProgress}%
                </div>
                <div style={{ height: "6px", width: "100%", background: "var(--bg-input)", borderRadius: "3px", overflow: "hidden" }}>
                  <div style={{ height: "100%", width: `${uploadProgress}%`, background: "var(--primary)" }}></div>
                </div>
              </div>
            )}

            {/* Pipeline Configurations */}
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "1rem", marginBottom: "1.25rem" }}>
              <div className="form-group">
                <label className="form-label">Confidence Threshold ({config.confidence_threshold})</label>
                <input
                  type="range"
                  min="0.1"
                  max="0.9"
                  step="0.05"
                  value={config.confidence_threshold}
                  onChange={(e) => setConfig({ ...config, confidence_threshold: parseFloat(e.target.value) })}
                  className="form-input"
                />
              </div>

              <div className="form-group">
                <label className="form-label">Frame Skip Interval ({config.frame_skip})</label>
                <input
                  type="number"
                  min="1"
                  max="10"
                  value={config.frame_skip}
                  onChange={(e) => setConfig({ ...config, frame_skip: parseInt(e.target.value) })}
                  className="form-input"
                />
              </div>
            </div>

            <div style={{ display: "flex", gap: "1rem", marginBottom: "1.25rem" }}>
              <label style={{ display: "flex", alignItems: "center", gap: "0.4rem", fontSize: "0.85rem" }}>
                <input
                  type="checkbox"
                  checked={config.enable_tracking}
                  onChange={(e) => setConfig({ ...config, enable_tracking: e.target.checked })}
                />
                Object Tracking (ByteTrack)
              </label>

              <label style={{ display: "flex", alignItems: "center", gap: "0.4rem", fontSize: "0.85rem" }}>
                <input
                  type="checkbox"
                  checked={config.enable_face_detection}
                  onChange={(e) => setConfig({ ...config, enable_face_detection: e.target.checked })}
                />
                Face Detection
              </label>
            </div>

            {selectedVideo && (
              <div>
                <div style={{ fontSize: "0.85rem", color: "#9ca3af", marginBottom: "0.75rem", padding: "0.5rem", background: "var(--bg-input)", borderRadius: "0.4rem" }}>
                  Selected: <strong>{selectedVideo.original_filename}</strong> ({selectedVideo.status})
                </div>

                <button
                  className="btn btn-primary"
                  style={{ width: "100%", justifyContent: "center" }}
                  disabled={processing || selectedVideo.status === "processing"}
                  onClick={handleStartProcess}
                >
                  <Play size={16} />
                  {processing ? `PROCESSING (${processStatus?.progress?.toFixed(0) || 0}%)` : "START AI PIPELINE PROCESS"}
                </button>

                {processing && (
                  <div style={{ marginTop: "1rem" }}>
                    <div style={{ height: "8px", width: "100%", background: "var(--bg-input)", borderRadius: "4px", overflow: "hidden" }}>
                      <div style={{ height: "100%", width: `${processStatus?.progress || 0}%`, background: "var(--primary)" }}></div>
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>

        {/* Video Player & Results Summary */}
        <div style={{ display: "flex", flexDirection: "column", gap: "1rem" }}>
          <VideoPlayer
            title={`ANALYZED CCTV FEED — ${selectedVideo ? selectedVideo.original_filename : ""}`}
            streamUrl={selectedVideo ? videosApi.getStreamUrl(selectedVideo.id) : null}
            metadata={selectedVideo}
          />

          {results && (
            <div className="panel">
              <div className="panel-header">
                <div className="panel-title">Detection Summary Results</div>
              </div>
              <div className="panel-body">
                <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: "1rem", textAlign: "center" }}>
                  <div style={{ padding: "0.75rem", background: "var(--bg-input)", borderRadius: "0.4rem" }}>
                    <div style={{ fontSize: "0.75rem", color: "#9ca3af" }}>TOTAL DETECTIONS</div>
                    <div style={{ fontSize: "1.25rem", fontWeight: 700, color: "#10b981" }}>{results.summary.total_detections}</div>
                  </div>
                  <div style={{ padding: "0.75rem", background: "var(--bg-input)", borderRadius: "0.4rem" }}>
                    <div style={{ fontSize: "0.75rem", color: "#9ca3af" }}>PERSONS</div>
                    <div style={{ fontSize: "1.25rem", fontWeight: 700, color: "#06b6d4" }}>{results.summary.persons}</div>
                  </div>
                  <div style={{ padding: "0.75rem", background: "var(--bg-input)", borderRadius: "0.4rem" }}>
                    <div style={{ fontSize: "0.75rem", color: "#9ca3af" }}>VEHICLES</div>
                    <div style={{ fontSize: "1.25rem", fontWeight: 700, color: "#3b82f6" }}>{results.summary.vehicles}</div>
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
