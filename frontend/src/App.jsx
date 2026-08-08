import React from "react";
import { BrowserRouter as Router, Routes, Route } from "react-router-dom";
import Navbar from "./components/Navbar";
import Sidebar from "./components/Sidebar";
import Dashboard from "./pages/Dashboard";
import LiveAnalysis from "./pages/LiveAnalysis";
import VideoAnalysis from "./pages/VideoAnalysis";
import FaceRecognition from "./pages/FaceRecognition";
import EventsPage from "./pages/EventsPage";
import AnalyticsPage from "./pages/AnalyticsPage";
import SettingsPage from "./pages/SettingsPage";
import AboutPage from "./pages/AboutPage";

export default function App() {
  return (
    <Router>
      <div className="app-container">
        <Sidebar />
        <div className="main-content">
          <Navbar />
          <main className="content-body">
            <Routes>
              <Route path="/" element={<Dashboard />} />
              <Route path="/live" element={<LiveAnalysis />} />
              <Route path="/video-analysis" element={<VideoAnalysis />} />
              <Route path="/faces" element={<FaceRecognition />} />
              <Route path="/events" element={<EventsPage />} />
              <Route path="/analytics" element={<AnalyticsPage />} />
              <Route path="/settings" element={<SettingsPage />} />
              <Route path="/about" element={<AboutPage />} />
            </Routes>
          </main>
        </div>
      </div>
    </Router>
  );
}
