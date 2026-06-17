function DocumentChatPage({ document, goBack, goToDashboard }) {
  if (!document) {
    return (
      <div className="app-shell">
        <div className="top-nav">
          <button onClick={goBack}>← Back to History</button>
          <button onClick={goToDashboard}>Dashboard</button>
        </div>

        <p className="history-message">No document selected.</p>
      </div>
    );
  }

  return (
    <div className="app-shell">
      <div className="top-nav">
        <button onClick={goBack}>← Back to History</button>
        <button onClick={goToDashboard}>Dashboard</button>
      </div>

      <div className="rag-card">
        <header className="rag-header">
          <div className="brand-block">
            <div className="brand-icon">▣</div>

            <div>
              <h1>RAG Assistant</h1>
              <p>Document loaded from history</p>
            </div>
          </div>

          <div className="chunks-status">
            {document.chunks_count || 3} chunks active
          </div>
        </header>

        <div className="rag-layout">
          <aside className="document-panel">
            <div className="panel-label">DOCUMENT</div>

            <div className="drop-zone static-document-box">
              <div className="cloud-icon">☁</div>

              <p>{document.file_name}</p>

              <span className="file-types">
                {document.file_type?.replace(".", "").toUpperCase()} document
                loaded successfully
              </span>
            </div>

            <div className="small-status">
              Document opened from your saved history.
            </div>

            <div className="document-details-box">
              <p>
                <strong>Characters:</strong>{" "}
                {document.full_text_length?.toLocaleString()}
              </p>

              <p>
                <strong>Status:</strong> {document.status}
              </p>

              <p>
                <strong>Uploaded:</strong>{" "}
                {document.upload_date
                  ? new Date(document.upload_date).toLocaleString()
                  : "N/A"}
              </p>
            </div>

            <div className="panel-label retrieved-label">RETRIEVED CHUNKS</div>

            <div className="chunk-card active">
              <span>Chunk 1 —</span>
              <p>Introduction...</p>
            </div>

            <div className="chunk-card active">
              <span>Chunk 2 —</span>
              <p>Main content...</p>
            </div>

            <div className="chunk-card active">
              <span>Chunk 3 —</span>
              <p>Details...</p>
            </div>
          </aside>

          <main className="chat-panel">
            <div className="panel-label">CHAT</div>

            <div className="chat-area">
              <div className="bot-message">Document loaded. Ask your question.</div>

              <div className="user-message">Show extracted preview</div>

              <div className="bot-message preview-message">
                {document.text_preview ||
                  "No preview available for this document."}
              </div>

              <div className="hint-message">
                The real RAG chat API will be connected here by your partner.
              </div>
            </div>

            <div className="chat-input-row">
              <input
                type="text"
                placeholder="Chat API will be connected here later..."
                disabled
              />

              <button disabled>↑</button>
            </div>
          </main>
        </div>
      </div>
    </div>
  );
}

export default DocumentChatPage;