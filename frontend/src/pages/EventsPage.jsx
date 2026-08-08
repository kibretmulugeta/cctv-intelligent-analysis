import React, { useState, useEffect } from "react";
import { Bell, Filter, Search, RefreshCw } from "lucide-react";
import EventTable from "../components/EventTable";
import { eventsApi } from "../services/api";

export default function EventsPage() {
  const [events, setEvents] = useState([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(false);
  const [filterType, setFilterType] = useState("");
  const [filterSeverity, setFilterSeverity] = useState("");

  useEffect(() => {
    loadEvents();
  }, [filterType, filterSeverity]);

  const loadEvents = async () => {
    setLoading(true);
    try {
      const params = {};
      if (filterType) params.event_type = filterType;
      if (filterSeverity) params.severity = filterSeverity;
      const res = await eventsApi.listEvents(params);
      setEvents(res.data.items);
      setTotal(res.data.total);
    } catch (err) {
      console.error("Failed to load events:", err);
    } finally {
      setLoading(false);
    }
  };

  const handleAcknowledge = async (id) => {
    try {
      await eventsApi.acknowledgeEvent(id);
      loadEvents();
    } catch (err) {
      console.error("Failed to acknowledge event:", err);
    }
  };

  return (
    <div>
      <div className="panel" style={{ marginBottom: "1.5rem" }}>
        <div className="panel-header">
          <div className="panel-title">
            <Bell size={18} color="#ef4444" />
            Searchable CCTV Event Logs ({total})
          </div>

          <div style={{ display: "flex", gap: "1rem" }}>
            <select
              value={filterType}
              onChange={(e) => setFilterType(e.target.value)}
              className="form-select"
              style={{ width: "200px" }}
            >
              <option value="">All Event Types</option>
              <option value="PERSON_ENTERED_ZONE">Person Entered Zone</option>
              <option value="VEHICLE_ENTERED_ZONE">Vehicle Entered Zone</option>
              <option value="HIGH_PERSON_DENSITY">High Person Density</option>
              <option value="PROLONGED_PRESENCE">Prolonged Presence</option>
              <option value="RAPID_MOVEMENT">Rapid Movement</option>
              <option value="FACE_DETECTED">Face Detected</option>
              <option value="FACE_RECOGNIZED">Face Recognized</option>
            </select>

            <select
              value={filterSeverity}
              onChange={(e) => setFilterSeverity(e.target.value)}
              className="form-select"
              style={{ width: "160px" }}
            >
              <option value="">All Severities</option>
              <option value="info">Info</option>
              <option value="warning">Warning</option>
              <option value="alert">Alert</option>
            </select>

            <button className="btn btn-secondary" onClick={loadEvents}>
              <RefreshCw size={14} className={loading ? "spin" : ""} /> Refresh
            </button>
          </div>
        </div>

        <div className="panel-body" style={{ padding: 0 }}>
          <EventTable events={events} onAcknowledge={handleAcknowledge} />
        </div>
      </div>
    </div>
  );
}
