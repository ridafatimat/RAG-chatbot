import { useEffect, useState } from "react";

function HistoryPage({ user, goBack, openDocumentChat }) {
  const [documents, setDocuments] = useState([]);
  const [message, setMessage] = useState("");
  const [loading, setLoading] = useState(true);

  const API_BASE_URL = "http://127.0.0.1:8000";

  const fetchDocuments = async () => {
    if (!user?._id) {
      setMessage("User not found. Please login again.");
      setLoading(false);
      return;
    }

    try {
      setLoading(true);
      setMessage("");

      const response = await fetch(`${API_BASE_URL}/documents/user/${user._id}`);
      const data = await response.json();

      if (!response.ok) {
        setMessage(data.detail || "Could not fetch documents.");
        return;
      }

      setDocuments(data.documents || []);
    } catch (error) {
      setMessage("Could not connect to backend.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDocuments();
  }, []);

  return (
    <div className="history-page">
      <header className="dashboard-header">
        <div>
          <h1>Document History</h1>
          <p>Only documents uploaded from your account are shown here.</p>
        </div>

        <button onClick={goBack}>← Dashboard</button>
      </header>

      {loading && <p className="history-message">Loading documents...</p>}

      {message && <p className="history-message">{message}</p>}

      {!loading && documents.length === 0 && (
        <p className="history-message">No documents uploaded yet.</p>
      )}

      <section className="history-grid">
        {documents.map((doc) => (
          <div
            className="history-card"
            key={doc._id}
            onClick={() => openDocumentChat(doc)}
          >
            <h2>{doc.file_name}</h2>

            <p>
              <strong>Type:</strong>{" "}
              {doc.file_type?.replace(".", "").toUpperCase()}
            </p>

            <p>
              <strong>Characters:</strong>{" "}
              {doc.full_text_length?.toLocaleString()}
            </p>

            <p>
              <strong>Status:</strong> {doc.status}
            </p>

            <p>
              <strong>Uploaded:</strong>{" "}
              {doc.upload_date
                ? new Date(doc.upload_date).toLocaleString()
                : "N/A"}
            </p>

            <span>Open document chat →</span>
          </div>
        ))}
      </section>
    </div>
  );
}

export default HistoryPage;