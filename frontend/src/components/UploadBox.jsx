import { useEffect, useState } from "react";

function UploadBox() {
  const [file, setFile] = useState(null);
  const [message, setMessage] = useState("");
  const [textPreview, setTextPreview] = useState("");
  const [loading, setLoading] = useState(false);
  const [documentName, setDocumentName] = useState("");
  const [uploadedDocuments, setUploadedDocuments] = useState([]);

  const API_BASE_URL = "http://127.0.0.1:8001";

  const fetchDocuments = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/documents`);
      const data = await response.json();

      setUploadedDocuments(data.documents || []);
    } catch (error) {
      console.log("Could not fetch uploaded documents", error);
    }
  };

  useEffect(() => {
    fetchDocuments();
  }, []);

  const handleFileChange = (event) => {
    const selectedFile = event.target.files[0];

    setFile(selectedFile);
    setDocumentName(selectedFile ? selectedFile.name : "");
    setMessage("");
    setTextPreview("");
  };

  const handleUpload = async () => {
    if (!file) {
      setMessage("Please select a document first.");
      return;
    }

    const formData = new FormData();
    formData.append("file", file);

    try {
      setLoading(true);
      setMessage("");
      setTextPreview("");

      const response = await fetch(`${API_BASE_URL}/upload`, {
        method: "POST",
        body: formData,
      });

      const data = await response.json();

      if (!response.ok) {
        setMessage(data.detail || "Upload failed.");
        return;
      }

      setMessage(data.message);
      setTextPreview(data.text_preview);

      await fetchDocuments();
    } catch (error) {
      setMessage("Could not connect to backend. Please make sure backend is running.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="rag-card">
      <header className="rag-header">
        <div className="brand-block">
          <div className="brand-icon">▣</div>
          <div>
            <h1>RAG Assistant</h1>
            <p>{textPreview ? "Document processed" : "Upload a document to begin"}</p>
          </div>
        </div>

        <div className="chunks-status">
          {textPreview ? "3 chunks active" : "0 chunks active"}
        </div>
      </header>

      <div className="rag-layout">
        <aside className="document-panel">
          <div className="panel-label">DOCUMENT</div>

          <label className="drop-zone">
            <input
              type="file"
              accept=".pdf,.txt,.docx,.pptx,.csv,.xlsx"
              onChange={handleFileChange}
              hidden
            />

            <div className="cloud-icon">☁</div>

            <p>{documentName ? documentName : "Drop file here"}</p>

            <span className="file-types">
              PDF, TXT, DOCX, PPTX, CSV, XLSX supported
            </span>
          </label>

          <button
            className="process-btn"
            onClick={handleUpload}
            disabled={loading}
          >
            {loading ? "Processing..." : "Process Document"}
          </button>

          {message && <div className="small-status">{message}</div>}

          <div className="panel-label retrieved-label">RETRIEVED CHUNKS</div>

          <div className={`chunk-card ${textPreview ? "active" : ""}`}>
            <span>Chunk 1 —</span>
            <p>{textPreview ? "Introduction..." : "Waiting..."}</p>
          </div>

          <div className={`chunk-card ${textPreview ? "active" : ""}`}>
            <span>Chunk 2 —</span>
            <p>{textPreview ? "Main content..." : "Waiting..."}</p>
          </div>

          <div className={`chunk-card ${textPreview ? "active" : ""}`}>
            <span>Chunk 3 —</span>
            <p>{textPreview ? "Details..." : "Waiting..."}</p>
          </div>

          <div className="panel-label uploaded-label">UPLOADED DOCUMENTS</div>

          <div className="documents-list">
            {uploadedDocuments.length === 0 ? (
              <p className="empty-documents">No documents saved yet.</p>
            ) : (
              uploadedDocuments.map((doc) => (
                <div className="saved-doc-card" key={doc._id}>
                  <span>{doc.file_name}</span>
                  <p>
                    {doc.file_type} · {doc.full_text_length} characters extracted
                  </p>
                </div>
              ))
            )}
          </div>
        </aside>

        <main className="chat-panel">
          <div className="panel-label">CHAT</div>

          <div className="chat-area">
            <div className="bot-message">
              {textPreview
                ? "Document loaded. Ask your question."
                : "Upload a document first so we can extract text from it."}
            </div>

            {textPreview && (
              <>
                <div className="user-message">
                  Show me the extracted preview.
                </div>

                <div className="bot-message preview-message">
                  {textPreview}
                </div>
              </>
            )}

            {!textPreview && (
              <div className="hint-message">
                Your extracted document preview will appear here after upload.
              </div>
            )}
          </div>

          <div className="chat-input-row">
            <input
              type="text"
              placeholder="Type here..."
              disabled
            />
            <button disabled>↑</button>
          </div>
        </main>
      </div>
    </div>
  );
}

export default UploadBox;