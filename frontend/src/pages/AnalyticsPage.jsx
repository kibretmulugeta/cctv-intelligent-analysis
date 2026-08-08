import React, { useState, useEffect } from "react";
import { BarChart3, TrendingUp, PieChart, Clock } from "lucide-react";
import {
  AreaChart,
  Area,
  BarChart,
  Bar,
  PieChart as RePieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from "recharts";
import { analyticsApi } from "../services/api";

export default function AnalyticsPage() {
  const [detectionsTime, setDetectionsTime] = useState([]);
  const [classDist, setClassDist] = useState([]);
  const [eventsType, setEventsType] = useState([]);

  useEffect(() => {
    loadAnalytics();
  }, []);

  const loadAnalytics = async () => {
    try {
      const [detRes, classRes, eventRes] = await Promise.all([
        analyticsApi.getDetectionsOverTime(),
        analyticsApi.getClassDistribution(),
        analyticsApi.getEventsByType(),
      ]);
      setDetectionsTime(detRes.data);
      setClassDist(classRes.data);
      setEventsType(eventRes.data);
    } catch (err) {
      console.error("Failed to load analytics data:", err);
    }
  };

  const COLORS = ["#10b981", "#06b6d4", "#3b82f6", "#f59e0b", "#ef4444", "#8b5cf6"];

  return (
    <div>
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "1.5rem", marginBottom: "1.5rem" }}>
        {/* Detections Over Time Chart */}
        <div className="panel">
          <div className="panel-header">
            <div className="panel-title">
              <TrendingUp size={18} color="#10b981" />
              Detections Over Time (5-Second Bins)
            </div>
          </div>
          <div className="panel-body">
            {detectionsTime.length === 0 ? (
              <div style={{ padding: "3rem", textAlign: "center", color: "#6b7280" }}>
                No analysis data available yet. Upload and process a video to populate charts.
              </div>
            ) : (
              <ResponsiveContainer width="100%" height={280}>
                <AreaChart data={detectionsTime}>
                  <defs>
                    <linearGradient id="colorPerson" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#10b981" stopOpacity={0.8} />
                      <stop offset="95%" stopColor="#10b981" stopOpacity={0} />
                    </linearGradient>
                    <linearGradient id="colorVehicle" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#06b6d4" stopOpacity={0.8} />
                      <stop offset="95%" stopColor="#06b6d4" stopOpacity={0} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke="#1f293d" />
                  <XAxis dataKey="time" stroke="#9ca3af" unit="s" />
                  <YAxis stroke="#9ca3af" />
                  <Tooltip contentStyle={{ backgroundColor: "#111827", borderColor: "#1f293d", color: "#fff" }} />
                  <Legend />
                  <Area type="monotone" dataKey="person" stroke="#10b981" fillOpacity={1} fill="url(#colorPerson)" name="Persons" />
                  <Area type="monotone" dataKey="vehicle" stroke="#06b6d4" fillOpacity={1} fill="url(#colorVehicle)" name="Vehicles" />
                </AreaChart>
              </ResponsiveContainer>
            )}
          </div>
        </div>

        {/* Object Class Breakdown Chart */}
        <div className="panel">
          <div className="panel-header">
            <div className="panel-title">
              <PieChart size={18} color="#06b6d4" />
              Object Class Distribution
            </div>
          </div>
          <div className="panel-body">
            {classDist.length === 0 ? (
              <div style={{ padding: "3rem", textAlign: "center", color: "#6b7280" }}>
                No object breakdown available yet.
              </div>
            ) : (
              <ResponsiveContainer width="100%" height={280}>
                <BarChart data={classDist}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#1f293d" />
                  <XAxis dataKey="class_name" stroke="#9ca3af" />
                  <YAxis stroke="#9ca3af" />
                  <Tooltip contentStyle={{ backgroundColor: "#111827", borderColor: "#1f293d", color: "#fff" }} />
                  <Bar dataKey="count" fill="#10b981">
                    {classDist.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
