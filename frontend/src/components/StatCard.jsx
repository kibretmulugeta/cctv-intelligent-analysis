import React from "react";

export default function StatCard({ title, value, icon: Icon, color = "#10b981", subtitle }) {
  return (
    <div className="stat-card">
      <div className="stat-icon" style={{ backgroundColor: `${color}15`, color }}>
        <Icon size={24} />
      </div>
      <div className="stat-info">
        <h4>{title}</h4>
        <div className="value">{value}</div>
        {subtitle && <div style={{ fontSize: "0.75rem", color: "#6b7280", marginTop: "0.2rem" }}>{subtitle}</div>}
      </div>
    </div>
  );
}
