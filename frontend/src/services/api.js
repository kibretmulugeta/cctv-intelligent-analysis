import axios from "axios";

const API_BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    "Content-Type": "application/json",
  },
});

export const healthApi = {
  getHealth: () => api.get("/api/health"),
};

export const videosApi = {
  listVideos: () => api.get("/api/videos"),
  getVideo: (id) => api.get(`/api/videos/${id}`),
  uploadVideo: (formData, onProgress) =>
    api.post("/api/videos/upload", formData, {
      headers: { "Content-Type": "multipart/form-data" },
      onUploadProgress: (e) => {
        if (onProgress && e.total) {
          onProgress(Math.round((e.loaded * 100) / e.total));
        }
      },
    }),
  processVideo: (id, config) => api.post(`/api/videos/${id}/process`, config),
  getStatus: (id) => api.get(`/api/videos/${id}/status`),
  getResults: (id) => api.get(`/api/videos/${id}/results`),
  getStreamUrl: (id) => `${API_BASE_URL}/api/videos/${id}/stream`,
};

export const facesApi = {
  listFaces: () => api.get("/api/faces"),
  getFace: (id) => api.get(`/api/faces/${id}`),
  enrollFace: (formData) =>
    api.post("/api/faces/enroll", formData, {
      headers: { "Content-Type": "multipart/form-data" },
    }),
  deleteFace: (id) => api.delete(`/api/faces/${id}`),
  recognizeFace: (formData) =>
    api.post("/api/faces/recognize", formData, {
      headers: { "Content-Type": "multipart/form-data" },
    }),
};

export const eventsApi = {
  listEvents: (params) => api.get("/api/events", { params }),
  getEvent: (id) => api.get(`/api/events/${id}`),
  acknowledgeEvent: (id) => api.patch(`/api/events/${id}/acknowledge`),
};

export const analyticsApi = {
  getDashboardStats: () => api.get("/api/analytics/dashboard"),
  getDetectionsOverTime: (videoId) =>
    api.get("/api/analytics/detections-over-time", { params: { video_id: videoId } }),
  getEventsByType: (videoId) =>
    api.get("/api/analytics/events-by-type", { params: { video_id: videoId } }),
  getClassDistribution: (videoId) =>
    api.get("/api/analytics/class-distribution", { params: { video_id: videoId } }),
  getRecentEvents: (limit = 20) =>
    api.get("/api/analytics/recent-events", { params: { limit } }),
};

export default api;
