function DashboardPage({ user, onLogout, goToUpload, goToHistory }) {
  return (
    <div className="dashboard-page">
      <header className="dashboard-header">
        <div className="brand-block">
          <div className="brand-icon">▣</div>

          <div>
            <h1>RAG Assistant</h1>
            <p>Welcome, {user?.name}</p>
          </div>
        </div>

        <button onClick={onLogout}>Logout</button>
      </header>

      <section className="dashboard-hero">
        <h2>Your Document Workspace</h2>
        <p>
          Upload a new document or continue from documents already processed in
          your account.
        </p>
      </section>

      <section className="dashboard-actions">
        <div className="dashboard-card" onClick={goToUpload}>
          <h2>Upload New Document</h2>
          <p>Process PDF, TXT, DOCX, PPTX, CSV, or XLSX files.</p>
          <span>Start upload →</span>
        </div>

        <div className="dashboard-card" onClick={goToHistory}>
          <h2>View Document History</h2>
          <p>See all documents uploaded from your account only.</p>
          <span>Open history →</span>
        </div>
      </section>
    </div>
  );
}

export default DashboardPage;