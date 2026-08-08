import React, { useRef, useState } from "react";
import { Play, Pause, Volume2, VolumeX, Maximize } from "lucide-react";

export default function VideoPlayer({ streamUrl, title = "CCTV Video Feed", metadata }) {
  const videoRef = useRef(null);
  const [isPlaying, setIsPlaying] = useState(false);
  const [isMuted, setIsMuted] = useState(true);

  const togglePlay = () => {
    if (videoRef.current) {
      if (isPlaying) {
        videoRef.current.pause();
      } else {
        videoRef.current.play();
      }
      setIsPlaying(!isPlaying);
    }
  };

  const toggleMute = () => {
    if (videoRef.current) {
      videoRef.current.muted = !isMuted;
      setIsMuted(!isMuted);
    }
  };

  const toggleFullscreen = () => {
    if (videoRef.current) {
      if (document.fullscreenElement) {
        document.exitFullscreen();
      } else {
        videoRef.current.requestFullscreen();
      }
    }
  };

  return (
    <div className="panel">
      <div className="panel-header">
        <div className="panel-title">
          <span className="status-dot" style={{ backgroundColor: isPlaying ? "#10b981" : "#f59e0b" }}></span>
          {title}
        </div>
        {metadata && (
          <div style={{ fontSize: "0.78rem", color: "#9ca3af", fontFamily: "monospace" }}>
            {metadata.resolution_width}x{metadata.resolution_height} | {metadata.fps} FPS | {metadata.duration}s
          </div>
        )}
      </div>

      <div className="panel-body" style={{ padding: 0 }}>
        <div className="video-wrapper">
          {streamUrl ? (
            <video
              ref={videoRef}
              className="video-element"
              src={streamUrl}
              muted={isMuted}
              controls
              onPlay={() => setIsPlaying(true)}
              onPause={() => setIsPlaying(false)}
            />
          ) : (
            <div style={{ color: "#6b7280", textAlign: "center", padding: "3rem" }}>
              No video stream selected. Upload a video or select an existing one.
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
