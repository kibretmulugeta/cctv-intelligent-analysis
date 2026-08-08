import React, { useState, useEffect } from "react";
import { Shield, Activity, Cpu, Server } from "lucide-react";
import { healthApi } from "../services/api";

export default function Navbar() {
  const [health, setHealth] = useState(null);

  useEffect(() => {
    const fetchHealth = async () => {
      try {
        const res = await healthApi.getHealth();
        setHealth(res.data);
      } catch (err) {
        console.error("Health check failed:", err);
      }
    };
    fetchHealth();
    const interval = setInterval(fetchHealth, 10000);
    return () => clearInterval(interval);
  }, []);

  return (
    <header className="navbar">
      <div className="nav-brand">
        <Shield size={24} />
        <span>CCTV Intelligent Analysis & Face Recognition</span>
      </div>

      <div className="nav-status-group">
        <div className="status-pill">
          <div className="status-dot"></div>
          <span>SYSTEM ONLINE</span>
        </div>

        <div style={{ display: "flex", gap: "1rem", fontSize: "0.8rem", color: "#9ca3af" }}>
          <span style={{ display: "flex", alignItems: "center", gap: "0.3rem" }}>
            <Cpu size={14} color="#10b981" />
            Device: <strong style={{ color: "#fff" }}>{health?.device?.toUpperCase() || "CPU"}</strong>
          </span>
          <span style={{ display: "flex", alignItems: "center", gap: "0.3rem" }}>
            <Activity size={14} color="#06b6d4" />
            Model: <strong style={{ color: "#fff" }}>{health?.yolo_model || "YOLO11n"} ({health?.yolo_mode || "inference"})</strong>
          </span>
          <span style={{ display: "flex", alignItems: "center", gap: "0.3rem" }}>
            <Server size={14} color="#3b82f6" />
            Face AI: <strong style={{ color: "#fff" }}>{health?.face_backend || "Active"}</strong>
          </span>
        </div>
      </div>
    </header>
  );
}
