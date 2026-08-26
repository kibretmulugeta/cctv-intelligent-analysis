import React, { useState, useEffect } from "react";
import { Camera, StopCircle, AlertCircle, ShieldCheck, UserCheck, RefreshCw } from "lucide-react";
import PrivacyNotice from "../components/PrivacyNotice";
import { liveApi, facesApi } from "../services/api";

export default function LiveAnalysis() {
  const [isStreaming, setIsStreaming] = useState(false);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);
  const [capturingAdmin, setCapturingAdmin] = useState(false);
  const [enrolledFaces, setEnrolledFaces] = useState([]);

  const streamUrl = liveApi.startStreamUrl(0);

  useEffect(() => {
    loadEnrolledFaces();
    const interval = setInterval(loadEnrolledFaces, 5000);
    return () => clearInterval(interval);
  }, []);

  const loadEnrolledFaces = async () => {
    try {
      const res = await facesApi.listFaces();
      setEnrolledFaces(res.data);
    } catch (err) {
      console.error("Failed to load enrolled faces:", err);
    }
  };

  const startCamera = () => {
    setIsStreaming(true);
    setError(null);
  };

  const stopCamera = async () => {
    setIsStreaming(false);
    try {
      await liveApi.stopStream();
    } catch (err) {
      console.error("Failed to stop live camera:", err);
    }
  };

  const captureAdmin = async () => {
    setCapturingAdmin(true);
    setError(null);
    setSuccess(null);
    try {
      const res = await liveApi.captureAdmin(0);
      setSuccess("Successfully captured face and registered as Admin!");
      loadEnrolledFaces();
    } catch (err) {
      setError(err.response?.data?.detail || "Failed to capture Admin face. Ensure your camera is clear and a single face is visible.");
    } finally {
      setCapturingAdmin(false);
    }
  };

  return (
    <div>
      <PrivacyNotice />

      <div style={{ display: "grid", gridTemplateColumns: "3fr 1fr", gap: "1.5rem" }}>
        {/* Main Stream Viewport */}
        <div className="panel">
          <div className="panel-header">
            <div className="panel-title">
              <Camera size={20} color="#10b981" />
              Laptop Camera AI Stream (Admin & Automatic Person ID Recognition)
            </div>
            <div style={{ display: "flex", gap: "0.5rem" }}>
              <button
                className="btn"
                style={{ background: "#f59e0b", color: "#000", fontWeight: 700 }}
                onClick={captureAdmin}
                disabled={capturingAdmin}
              >
                <UserCheck size={16} />
                {capturingAdmin ? "CAPTURING..." : "📸 CAPTURE ME AS ADMIN"}
              </button>

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
                <AlertCircle size={16} style={{ display: "inline", marginRight: "0.4rem" }} /> {error}
              </div>
            )}
            {success && (
              <div style={{ padding: "0.75rem", background: "rgba(16, 185, 129, 0.15)", border: "1px solid #10b981", borderRadius: "0.4rem", color: "#10b981", fontSize: "0.85rem", marginBottom: "1rem" }}>
                <ShieldCheck size={16} style={{ display: "inline", marginRight: "0.4rem" }} /> {success}
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
                    Click <strong>"START CAMERA"</strong> to launch live recognition or <strong>"CAPTURE ME AS ADMIN"</strong> to register your face as Admin.
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Registered Identities Sidebar */}
        <div className="panel">
          <div className="panel-header">
            <div className="panel-title" style={{ fontSize: "0.95rem" }}>
              <UserCheck size={16} color="#3b82f6" /> Identified Persons ({enrolledFaces.length})
            </div>
            <button className="btn" style={{ padding: "0.2rem 0.4rem", fontSize: "0.75rem" }} onClick={loadEnrolledFaces}>
              <RefreshCw size={12} />
            </button>
          </div>
          <div className="panel-body" style={{ padding: "0.5rem" }}>
            {enrolledFaces.length === 0 ? (
              <div style={{ padding: "1.5rem 0.5rem", textAlign: "center", color: "#6b7280", fontSize: "0.85rem" }}>
                No identities registered yet.
                <br /><br />
                1. Click <strong>Capture Me as Admin</strong> to register yourself.
                <br />
                2. Start the camera and any other detected face will automatically be assigned a Person ID!
              </div>
            ) : (
              <div style={{ display: "flex", flexDirection: "column", gap: "0.5rem" }}>
                {enrolledFaces.map((f) => {
                  const isAdmin = f.name.toLowerCase() === "admin";
                  return (
                    <div
                      key={f.id}
                      style={{
                        padding: "0.6rem 0.8rem",
                        borderRadius: "0.4rem",
                        background: isAdmin ? "rgba(16, 185, 129, 0.15)" : "rgba(255, 255, 255, 0.05)",
                        border: isAdmin ? "1px solid #10b981" : "1px solid rgba(255, 255, 255, 0.1)",
                        display: "flex",
                        justifyContent: "space-between",
                        alignItems: "center",
                      }}
                    >
                      <div>
                        <div style={{ fontWeight: 700, fontSize: "0.9rem", color: isAdmin ? "#10b981" : "#f3f4f6" }}>
                          {isAdmin ? "★ Admin" : f.name}
                        </div>
                        <div style={{ fontSize: "0.75rem", color: "#9ca3af" }}>
                          {isAdmin ? "Primary System User" : "Auto-Registered Identity"}
                        </div>
                      </div>
                      <span className={`badge ${isAdmin ? "badge-success" : "badge-info"}`} style={{ fontSize: "0.7rem" }}>
                        {isAdmin ? "ADMIN" : "REGISTERED"}
                      </span>
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

