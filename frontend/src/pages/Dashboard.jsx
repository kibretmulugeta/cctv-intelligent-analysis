import React, { useState, useEffect } from "react";
import { Users, Car, Bike, UserCheck, Bell, Activity, Eye, Zap } from "lucide-react";
import StatCard from "../components/StatCard";
import EventTable from "../components/EventTable";
import VideoPlayer from "../components/VideoPlayer";
import PrivacyNotice from "../components/PrivacyNotice";
import { analyticsApi, videosApi, eventsApi } from "../services/api";

export default function Dashboard() {
  const [stats, setStats] = useState({
    total_videos: 0,
    total_detections: 0,
    total_events: 0,
    persons: 0,
    vehicles: 0,
    bicycles: 0,
    faces_detected: 0,
  });
  const [recentEvents, setRecentEvents] = useState([]);
  const [activeVideo, setActiveVideo] = useState(null);
  const [videos, setVideos] = useState([]);

  useEffect(() => {
    loadData();
    const interval = setInterval(loadData, 5000);
    return () => clearInterval(interval);
  }, []);

  const loadData = async () => {
    try {
      const [statsRes, eventsRes, videosRes] = await Promise.all([
        analyticsApi.getDashboardStats(),
        analyticsApi.getRecentEvents(10),
        videosApi.listVideos(),
      ]);
      setStats(statsRes.data);
      setRecentEvents(eventsRes.data);
      setVideos(videosRes.data);

      // Auto select first completed video for live panel if none selected
      if (!activeVideo && videosRes.data.length > 0) {
        const completed = videosRes.data.find((v) => v.status === "completed") || videosRes.data[0];
        setActiveVideo(completed);
      }
    } catch (err) {
      console.error("Failed to load dashboard data:", err);
    }
  };

  const handleAcknowledge = async (eventId) => {
    try {
      await eventsApi.acknowledgeEvent(eventId);
      setRecentEvents((prev) =>
        prev.map((e) => (e.id === eventId ? { ...e, is_acknowledged: true } : e))
      );
    } catch (err) {
      console.error("Failed to acknowledge event:", err);
    }
  };

  return (
    <div>
      <PrivacyNotice />

      {/* System Status Metrics */}
      <div className="card-grid">
        <StatCard title="Persons Detected" value={stats.persons} icon={Users} color="#10b981" />
        <StatCard title="Vehicles Detected" value={stats.vehicles} icon={Car} color="#06b6d4" />
        <StatCard title="Bicycles Detected" value={stats.bicycles} icon={Bike} color="#3b82f6" />
        <StatCard title="Faces Detected" value={stats.faces_detected} icon={UserCheck} color="#f59e0b" />
        <StatCard title="Total Events" value={stats.total_events} icon={Bell} color="#ef4444" />
      </div>

      {/* Live CCTV Video Feed + Recent Events Grid */}
      <div className="grid-2">
        <div style={{ display: "flex", flexDirection: "column", gap: "1rem" }}>
          <VideoPlayer
            title={`CCTV FEED — ${activeVideo ? activeVideo.original_filename : "NO VIDEO LOADED"}`}
            streamUrl={activeVideo ? videosApi.getStreamUrl(activeVideo.id) : null}
            metadata={activeVideo}
          />

          {/* Video Selector Pills */}
          {videos.length > 0 && (
            <div className="panel" style={{ padding: "0.85rem 1.25rem" }}>
              <div style={{ fontSize: "0.8rem", color: "#9ca3af", marginBottom: "0.5rem", fontWeight: 600 }}>
                SELECT VIDEO FEED:
              </div>
              <div style={{ display: "flex", gap: "0.5rem", flexWrap: "wrap" }}>
                {videos.map((v) => (
                  <button
                    key={v.id}
                    className={`btn ${activeVideo?.id === v.id ? "btn-primary" : "btn-secondary"}`}
                    style={{ padding: "0.35rem 0.75rem", fontSize: "0.78rem" }}
                    onClick={() => setActiveVideo(v)}
                  >
                    <Eye size={12} />
                    {v.original_filename} ({v.status})
                  </button>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Live Event Stream Panel */}
        <div className="panel">
          <div className="panel-header">
            <div className="panel-title">
              <Zap size={18} color="#ef4444" />
              Live Detection Stream
            </div>
            <span style={{ fontSize: "0.75rem", color: "#9ca3af" }}>{recentEvents.length} events</span>
          </div>
          <div className="panel-body" style={{ padding: 0 }}>
            <EventTable events={recentEvents} onAcknowledge={handleAcknowledge} />
          </div>
        </div>
      </div>
    </div>
  );
}
