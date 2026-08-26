import React, { useState, useEffect } from "react";
import { UserCheck, Trash2, Upload, AlertTriangle, ShieldCheck } from "lucide-react";
import PrivacyNotice from "../components/PrivacyNotice";
import { facesApi } from "../services/api";

export default function FaceRecognition() {
  const [faces, setFaces] = useState([]);
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [imageFile, setImageFile] = useState(null);
  const [previewUrl, setPreviewUrl] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);

  useEffect(() => {
    loadFaces();
  }, []);

  const loadFaces = async () => {
    try {
      const res = await facesApi.listFaces();
      setFaces(res.data);
    } catch (err) {
      console.error("Failed to load faces:", err);
    }
  };

  const handleImageChange = (e) => {
    const file = e.target.files[0];
    if (file) {
      setImageFile(file);
      setPreviewUrl(URL.createObjectURL(file));
    }
  };

  const handleEnroll = async (e) => {
    e.preventDefault();
    if (!name || !imageFile) {
      setError("Please provide a name and select a face image.");
      return;
    }

    setLoading(true);
    setError(null);
    setSuccess(null);

    const formData = new FormData();
    formData.append("name", name);
    formData.append("description", description);
    formData.append("image", imageFile);

    try {
      await facesApi.enrollFace(formData);
      setSuccess(`Face identity '${name}' enrolled successfully!`);
      setName("");
      setDescription("");
      setImageFile(null);
      setPreviewUrl(null);
      loadFaces();
    } catch (err) {
      setError(err.response?.data?.detail || "Enrollment failed. Ensure image contains a clear single face.");
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (id, faceName) => {
    if (!window.confirm(`Delete enrolled face '${faceName}'?`)) return;
    try {
      await facesApi.deleteFace(id);
      loadFaces();
    } catch (err) {
      console.error("Failed to delete face:", err);
    }
  };

  return (
    <div>
      <PrivacyNotice />

      <div className="grid-2">
        {/* Consent-Based Face Enrollment Form */}
        <div className="panel">
          <div className="panel-header">
            <div className="panel-title">
              <UserCheck size={18} color="#10b981" />
              Consent-Based Face Identity Enrollment
            </div>
          </div>

          <div className="panel-body">
            {error && (
              <div style={{ padding: "0.75rem", background: "rgba(239, 68, 68, 0.15)", border: "1px solid #ef4444", borderRadius: "0.4rem", color: "#f87171", fontSize: "0.85rem", marginBottom: "1rem" }}>
                <AlertTriangle size={16} inline /> {error}
              </div>
            )}
            {success && (
              <div style={{ padding: "0.75rem", background: "rgba(16, 185, 129, 0.15)", border: "1px solid #10b981", borderRadius: "0.4rem", color: "#10b981", fontSize: "0.85rem", marginBottom: "1rem" }}>
                <ShieldCheck size={16} inline /> {success}
              </div>
            )}

            <form onSubmit={handleEnroll}>
              <div className="form-group">
                <label className="form-label">Full Name / Identifier</label>
                <input
                  type="text"
                  placeholder="e.g. Sarah Jenkins (Employee)"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  className="form-input"
                  required
                />
              </div>

              <div className="form-group">
                <label className="form-label">Description / Note</label>
                <input
                  type="text"
                  placeholder="e.g. Authorized Personnel - Gate 3"
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  className="form-input"
                />
              </div>

              <div className="form-group">
                <label className="form-label">Enrollment Photo (Single clear face)</label>
                <input type="file" accept="image/*" onChange={handleImageChange} className="form-input" required />
              </div>

              {previewUrl && (
                <div style={{ textAlign: "center", margin: "1rem 0" }}>
                  <img
                    src={previewUrl}
                    alt="Enrollment Preview"
                    style={{ maxHeight: "150px", borderRadius: "0.5rem", border: "1px solid var(--border-light)" }}
                  />
                </div>
              )}

              <button className="btn btn-primary" style={{ width: "100%", justifyContent: "center" }} disabled={loading}>
                <Upload size={16} />
                {loading ? "EXTRACTING EMBEDDINGS..." : "ENROLL FACE IDENTITY"}
              </button>
            </form>
          </div>
        </div>

        {/* Enrolled Face Database Table */}
        <div className="panel">
          <div className="panel-header">
            <div className="panel-title">Enrolled Identities ({faces.length})</div>
          </div>
          <div className="panel-body" style={{ padding: 0 }}>
            {faces.length === 0 ? (
              <div style={{ padding: "2rem", textAlign: "center", color: "#6b7280" }}>
                No face identities enrolled yet. Use the form to enroll authorized personnel.
              </div>
            ) : (
              <table className="custom-table">
                <thead>
                  <tr>
                    <th>Name</th>
                    <th>Embeddings</th>
                    <th>Consent</th>
                    <th>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {faces.map((f) => {
                    const isAdmin = f.name.toLowerCase() === "admin";
                    return (
                      <tr key={f.id} style={{ background: isAdmin ? "rgba(16, 185, 129, 0.08)" : "transparent" }}>
                        <td style={{ fontWeight: 600, color: isAdmin ? "#10b981" : "#fff" }}>
                          {isAdmin ? "★ Admin" : f.name}
                        </td>
                        <td>{f.image_count || 1} vectors</td>
                        <td>
                          {isAdmin ? (
                            <span className="badge badge-success">ADMIN USER</span>
                          ) : (
                            <span className="badge badge-info">AUTO-REGISTERED</span>
                          )}
                        </td>
                        <td>
                          <button className="btn btn-danger" style={{ padding: "0.25rem 0.5rem", fontSize: "0.75rem" }} onClick={() => handleDelete(f.id, f.name)}>
                            <Trash2 size={14} /> Delete
                          </button>
                        </td>
                      </tr>
                    );
                  })}

                </tbody>
              </table>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
