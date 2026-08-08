import React from "react";
import { CheckCircle } from "lucide-react";

export default function EventTable({ events, onAcknowledge }) {
  if (!events || events.length === 0) {
    return (
      <div style={{ padding: "2rem", textAlign: "center", color: "#6b7280" }}>
        No events recorded yet.
      </div>
    );
  }

  const getSeverityBadge = (severity) => {
    switch (severity?.toLowerCase()) {
      case "critical":
        return "badge badge-critical";
      case "alert":
        return "badge badge-alert";
      case "warning":
        return "badge badge-warning";
      default:
        return "badge badge-info";
    }
  };

  const formatTimestamp = (ts, createdAt) => {
    if (ts !== undefined && ts !== null) {
      const min = Math.floor(ts / 60);
      const sec = Math.floor(ts % 60);
      return `${min.toString().padStart(2, "0")}:${sec.toString().padStart(2, "0")}`;
    }
    if (createdAt) {
      return new Date(createdAt).toLocaleTimeString();
    }
    return "N/A";
  };

  return (
    <div style={{ overflowX: "auto" }}>
      <table className="custom-table">
        <thead>
          <tr>
            <th>Time</th>
            <th>Event Type</th>
            <th>Severity</th>
            <th>Description</th>
            <th>Object</th>
            <th>Status</th>
          </tr>
        </thead>
        <tbody>
          {events.map((ev) => (
            <tr key={ev.id}>
              <td style={{ fontFamily: "monospace", color: "#06b6d4" }}>
                {formatTimestamp(ev.timestamp_sec, ev.created_at)}
              </td>
              <td style={{ fontWeight: 600 }}>{ev.event_type}</td>
              <td>
                <span className={getSeverityBadge(ev.severity)}>{ev.severity}</span>
              </td>
              <td style={{ color: "#d1d5db" }}>{ev.description}</td>
              <td>
                {ev.object_type ? (
                  <span style={{ color: "#10b981", fontFamily: "monospace" }}>
                    {ev.object_type.toUpperCase()} {ev.object_id ? `#${ev.object_id}` : ""}
                  </span>
                ) : (
                  "-"
                )}
              </td>
              <td>
                {ev.is_acknowledged ? (
                  <span style={{ color: "#10b981", fontSize: "0.75rem", display: "flex", alignItems: "center", gap: "0.25rem" }}>
                    <CheckCircle size={14} /> Acked
                  </span>
                ) : (
                  onAcknowledge && (
                    <button
                      className="btn btn-secondary"
                      style={{ padding: "0.25rem 0.5rem", fontSize: "0.75rem" }}
                      onClick={() => onAcknowledge(ev.id)}
                    >
                      Ack
                    </button>
                  )
                )}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
