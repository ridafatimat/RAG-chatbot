import { useState, useRef, useEffect } from "react";

const API_BASE_URL = "http://127.0.0.1:8000";

function getInitials(name) {
  if (!name) return "?";
  const parts = name.trim().split(" ").filter(Boolean);
  if (parts.length === 1) return parts[0][0].toUpperCase();
  return (parts[0][0] + parts[parts.length - 1][0]).toUpperCase();
}

function DashboardPage({ user, onLogout, goToUpload, goToHistory }) {
  const [menuOpen, setMenuOpen] = useState(false);
  const [settingsOpen, setSettingsOpen] = useState(false);
  const [activeTab, setActiveTab] = useState("name");
  const [currentUser, setCurrentUser] = useState(user);

  const menuRef = useRef(null);

  useEffect(() => {
    function handleClickOutside(e) {
      if (menuRef.current && !menuRef.current.contains(e.target)) {
        setMenuOpen(false);
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  function openSettings(tab) {
    setActiveTab(tab);
    setSettingsOpen(true);
    setMenuOpen(false);
  }

  return (
    <div className="dash-root">
      <style>{`
        :root {
          --bg: #0a0a0a;
          --surface: #111111;
          --surface-2: #0d0d0d;
          --border: #1f1f1f;
          --orange: #ff6b00;
          --orange-dim: #ff6b0026;
          --text: #ffffff;
          --text-muted: #888888;
          --text-faint: #666666;
        }

        .dash-root {
          background: var(--bg);
          min-height: 100vh;
          font-family: 'Inter', 'Segoe UI', -apple-system, sans-serif;
          color: var(--text);
        }

        .dash-header {
          display: flex;
          align-items: center;
          justify-content: space-between;
          padding: 20px 40px;
          border-bottom: 1px solid var(--border);
          position: sticky;
          top: 0;
          background: rgba(10, 10, 10, 0.85);
          backdrop-filter: blur(10px);
          z-index: 50;
        }

        .brand-block {
          display: flex;
          align-items: center;
          gap: 14px;
        }

        .scan-mark {
          width: 38px;
          height: 38px;
          position: relative;
          flex-shrink: 0;
        }
        .scan-mark span {
          position: absolute;
          width: 12px;
          height: 12px;
          border: 2px solid var(--orange);
          transition: all 0.3s ease;
        }
        .scan-mark .tl { top: 0; left: 0; border-right: none; border-bottom: none; }
        .scan-mark .tr { top: 0; right: 0; border-left: none; border-bottom: none; }
        .scan-mark .bl { bottom: 0; left: 0; border-right: none; border-top: none; }
        .scan-mark .br { bottom: 0; right: 0; border-left: none; border-top: none; }
        .scan-mark::after {
          content: '';
          position: absolute;
          top: 50%;
          left: 4px;
          right: 4px;
          height: 1.5px;
          background: var(--orange);
          box-shadow: 0 0 8px var(--orange);
          animation: scanline 2.4s ease-in-out infinite;
        }
        @keyframes scanline {
          0%, 100% { top: 22%; opacity: 0.4; }
          50% { top: 78%; opacity: 1; }
        }

        .brand-text h1 {
          font-size: 18px;
          font-weight: 800;
          letter-spacing: -0.5px;
          margin: 0;
          line-height: 1.2;
        }
        .brand-text p {
          font-size: 13px;
          color: var(--text-muted);
          margin: 2px 0 0 0;
        }

        .header-right {
          position: relative;
        }

        .avatar-btn {
          display: flex;
          align-items: center;
          gap: 10px;
          background: var(--surface);
          border: 1px solid var(--border);
          border-radius: 100px;
          padding: 6px 14px 6px 6px;
          cursor: pointer;
          transition: border-color 0.2s ease;
        }
        .avatar-btn:hover {
          border-color: var(--orange);
        }
        .avatar-circle {
          width: 30px;
          height: 30px;
          border-radius: 50%;
          background: var(--orange-dim);
          border: 1.5px solid var(--orange);
          color: var(--orange);
          font-weight: 700;
          font-size: 12px;
          display: flex;
          align-items: center;
          justify-content: center;
          letter-spacing: 0;
        }
        .avatar-btn .uname {
          font-size: 13px;
          font-weight: 600;
          color: var(--text);
          max-width: 120px;
          overflow: hidden;
          text-overflow: ellipsis;
          white-space: nowrap;
        }
        .avatar-btn .chev {
          color: var(--text-faint);
          font-size: 10px;
          transition: transform 0.2s ease;
        }
        .avatar-btn .chev.open {
          transform: rotate(180deg);
        }

        .dropdown {
          position: absolute;
          top: calc(100% + 10px);
          right: 0;
          background: var(--surface);
          border: 1px solid var(--border);
          border-radius: 14px;
          min-width: 220px;
          padding: 8px;
          box-shadow: 0 10px 40px rgba(0,0,0,0.5);
          animation: dropIn 0.16s ease;
          z-index: 100;
        }
        @keyframes dropIn {
          from { opacity: 0; transform: translateY(-6px); }
          to { opacity: 1; transform: translateY(0); }
        }

        .dropdown-label {
          font-size: 10px;
          text-transform: uppercase;
          letter-spacing: 1px;
          color: var(--text-faint);
          padding: 8px 10px 4px;
          font-weight: 700;
        }

        .dropdown-item {
          display: flex;
          align-items: center;
          gap: 10px;
          width: 100%;
          background: transparent;
          border: none;
          color: var(--text);
          font-size: 13.5px;
          font-weight: 500;
          padding: 10px 10px;
          border-radius: 8px;
          cursor: pointer;
          text-align: left;
          transition: background 0.15s ease;
        }
        .dropdown-item:hover {
          background: #1a1a1a;
        }
        .dropdown-item.danger {
          color: #ff5c5c;
        }
        .dropdown-item.danger:hover {
          background: #2a131388;
        }
        .dropdown-item svg {
          flex-shrink: 0;
        }

        .dropdown-divider {
          height: 1px;
          background: var(--border);
          margin: 6px 4px;
        }

        .dash-hero {
          padding: 64px 40px 32px;
          max-width: 1100px;
          margin: 0 auto;
        }
        .dash-hero h2 {
          font-size: 34px;
          font-weight: 800;
          letter-spacing: -1px;
          margin: 0 0 10px 0;
        }
        .dash-hero p {
          font-size: 15px;
          color: var(--text-muted);
          max-width: 520px;
          line-height: 1.6;
          margin: 0;
        }

        .dash-actions {
          display: grid;
          grid-template-columns: repeat(2, 1fr);
          gap: 20px;
          max-width: 1100px;
          margin: 0 auto;
          padding: 0 40px 64px;
        }

        @media (max-width: 720px) {
          .dash-actions { grid-template-columns: 1fr; }
          .dash-header { padding: 16px 20px; }
          .dash-hero { padding: 40px 20px 24px; }
          .dash-actions { padding: 0 20px 40px; }
        }

        .action-card {
          background: var(--surface);
          border: 1px solid var(--border);
          border-radius: 14px;
          padding: 28px;
          cursor: pointer;
          transition: transform 0.22s ease, border-color 0.22s ease, box-shadow 0.22s ease;
          position: relative;
          overflow: hidden;
        }
        .action-card:hover {
          transform: translateY(-4px);
          border-color: var(--orange);
          box-shadow: 0 8px 30px var(--orange-dim);
        }
        .action-card:focus-visible {
          outline: 2px solid var(--orange);
          outline-offset: 2px;
        }

        .action-icon {
          width: 44px;
          height: 44px;
          border-radius: 10px;
          background: var(--orange-dim);
          display: flex;
          align-items: center;
          justify-content: center;
          color: var(--orange);
          margin-bottom: 20px;
        }

        .action-card h2 {
          font-size: 18px;
          font-weight: 700;
          letter-spacing: -0.3px;
          margin: 0 0 8px 0;
        }
        .action-card p {
          font-size: 13.5px;
          color: var(--text-muted);
          line-height: 1.55;
          margin: 0 0 18px 0;
        }
        .action-card span.cta {
          font-size: 13px;
          font-weight: 700;
          color: var(--orange);
          letter-spacing: 0.2px;
        }

        /* ---------- Modal ---------- */
        .modal-overlay {
          position: fixed;
          inset: 0;
          background: rgba(0,0,0,0.65);
          backdrop-filter: blur(4px);
          display: flex;
          align-items: center;
          justify-content: center;
          z-index: 200;
          animation: fadeIn 0.15s ease;
          padding: 20px;
        }
        @keyframes fadeIn {
          from { opacity: 0; }
          to { opacity: 1; }
        }

        .modal-card {
          background: var(--surface);
          border: 1px solid var(--border);
          border-radius: 16px;
          width: 100%;
          max-width: 440px;
          padding: 0;
          animation: modalIn 0.2s ease;
        }
        @keyframes modalIn {
          from { opacity: 0; transform: translateY(8px) scale(0.98); }
          to { opacity: 1; transform: translateY(0) scale(1); }
        }

        .modal-header {
          display: flex;
          align-items: center;
          justify-content: space-between;
          padding: 22px 24px 0;
        }
        .modal-header h3 {
          font-size: 17px;
          font-weight: 800;
          letter-spacing: -0.4px;
          margin: 0;
        }
        .modal-close {
          background: transparent;
          border: none;
          color: var(--text-faint);
          font-size: 20px;
          cursor: pointer;
          line-height: 1;
          padding: 4px;
        }
        .modal-close:hover {
          color: var(--text);
        }

        .modal-tabs {
          display: flex;
          gap: 4px;
          margin: 18px 24px 0;
          background: var(--surface-2);
          border: 1px solid var(--border);
          border-radius: 10px;
          padding: 4px;
        }
        .modal-tab {
          flex: 1;
          text-align: center;
          background: transparent;
          border: none;
          color: var(--text-muted);
          font-size: 12.5px;
          font-weight: 700;
          text-transform: uppercase;
          letter-spacing: 0.6px;
          padding: 9px 0;
          border-radius: 7px;
          cursor: pointer;
          transition: all 0.15s ease;
        }
        .modal-tab.active {
          background: var(--orange);
          color: #000;
        }

        .modal-body {
          padding: 22px 24px 26px;
        }

        .field-group {
          margin-bottom: 16px;
        }
        .field-label {
          display: block;
          font-size: 11px;
          text-transform: uppercase;
          letter-spacing: 0.8px;
          color: var(--text-faint);
          font-weight: 700;
          margin-bottom: 7px;
        }
        .field-input {
          width: 100%;
          background: var(--surface-2);
          border: 1px solid var(--border);
          border-radius: 9px;
          padding: 11px 13px;
          color: var(--text);
          font-size: 14px;
          font-family: inherit;
          outline: none;
          transition: border-color 0.15s ease;
          box-sizing: border-box;
        }
        .field-input:focus {
          border-color: var(--orange);
        }
        .field-input::placeholder {
          color: var(--text-faint);
        }

        .form-msg {
          font-size: 12.5px;
          font-weight: 600;
          padding: 10px 12px;
          border-radius: 8px;
          margin-bottom: 14px;
        }
        .form-msg.error {
          background: #2a1313;
          color: #ff6b6b;
          border: 1px solid #4a1f1f;
        }
        .form-msg.success {
          background: #14241a;
          color: #4ade80;
          border: 1px solid #1f4a2f;
        }

        .btn {
          font-family: inherit;
          font-size: 13.5px;
          font-weight: 700;
          border-radius: 9px;
          padding: 11px 18px;
          cursor: pointer;
          border: none;
          transition: opacity 0.15s ease, transform 0.1s ease;
          width: 100%;
        }
        .btn:active {
          transform: scale(0.98);
        }
        .btn:disabled {
          opacity: 0.5;
          cursor: not-allowed;
        }
        .btn-solid {
          background: var(--orange);
          color: #000;
        }
        .btn-solid:hover:not(:disabled) {
          opacity: 0.9;
        }
      `}</style>

      {/* HEADER */}
      <header className="dash-header">
        <div className="brand-block">
          <div className="scan-mark">
            <span className="tl"></span>
            <span className="tr"></span>
            <span className="bl"></span>
            <span className="br"></span>
          </div>
          <div className="brand-text">
            <h1>RAG Assistant</h1>
            <p>Welcome, {currentUser?.name}</p>
          </div>
        </div>

        <div className="header-right" ref={menuRef}>
          <button className="avatar-btn" onClick={() => setMenuOpen((o) => !o)}>
            <div className="avatar-circle">{getInitials(currentUser?.name)}</div>
            <span className="uname">{currentUser?.name}</span>
            <span className={`chev ${menuOpen ? "open" : ""}`}>▼</span>
          </button>

          {menuOpen && (
            <div className="dropdown">
              <div className="dropdown-label">Account</div>

              <button className="dropdown-item" onClick={() => openSettings("name")}>
                <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2" />
                  <circle cx="12" cy="7" r="4" />
                </svg>
                Edit name
              </button>

              <button className="dropdown-item" onClick={() => openSettings("password")}>
                <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <rect x="3" y="11" width="18" height="11" rx="2" />
                  <path d="M7 11V7a5 5 0 0 1 10 0v4" />
                </svg>
                Change password
              </button>

              <div className="dropdown-divider"></div>

              <button className="dropdown-item danger" onClick={onLogout}>
                <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4" />
                  <polyline points="16 17 21 12 16 7" />
                  <line x1="21" y1="12" x2="9" y2="12" />
                </svg>
                Logout
              </button>
            </div>
          )}
        </div>
      </header>

      {/* HERO */}
      <section className="dash-hero">
        <h2>Your Document Workspace</h2>
        <p>
          Upload a new document or continue from documents already processed in
          your account.
        </p>
      </section>

      {/* ACTIONS */}
      <section className="dash-actions">
        <div
          className="action-card"
          onClick={goToUpload}
          role="button"
          tabIndex={0}
          onKeyDown={(e) => e.key === "Enter" && goToUpload()}
        >
          <div className="action-icon">
            <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
              <polyline points="17 8 12 3 7 8" />
              <line x1="12" y1="3" x2="12" y2="15" />
            </svg>
          </div>
          <h2>Upload New Document</h2>
          <p>Process PDF, TXT, DOCX, PPTX, CSV, or XLSX files.</p>
          <span className="cta">Start upload →</span>
        </div>

        <div
          className="action-card"
          onClick={goToHistory}
          role="button"
          tabIndex={0}
          onKeyDown={(e) => e.key === "Enter" && goToHistory()}
        >
          <div className="action-icon">
            <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <circle cx="12" cy="12" r="9" />
              <polyline points="12 7 12 12 16 14" />
            </svg>
          </div>
          <h2>View Document History</h2>
          <p>See all documents uploaded from your account only.</p>
          <span className="cta">Open history →</span>
        </div>
      </section>

      {/* SETTINGS MODAL — popup, no new route/page */}
      {settingsOpen && (
        <SettingsModal
          activeTab={activeTab}
          setActiveTab={setActiveTab}
          currentUser={currentUser}
          setCurrentUser={setCurrentUser}
          onClose={() => setSettingsOpen(false)}
        />
      )}
    </div>
  );
}

function SettingsModal({ activeTab, setActiveTab, currentUser, setCurrentUser, onClose }) {
  const [name, setName] = useState(currentUser?.name || "");
  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  function switchTab(tab) {
    setActiveTab(tab);
    setError("");
    setSuccess("");
  }

  async function handleNameSubmit(e) {
    e.preventDefault();
    setError("");
    setSuccess("");

    const trimmed = name.trim();
    if (!trimmed) {
      setError("Name cannot be empty.");
      return;
    }

    setLoading(true);
    try {
      const token = localStorage.getItem("rag_token");
      const res = await fetch(`${API_BASE_URL}/change-name`, {
        method: "PUT",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({ name: trimmed }),
      });

      const data = await res.json();

      if (!res.ok) {
        setError(data.detail || "Could not update name.");
        return;
      }

      setCurrentUser(data.user);
      localStorage.setItem("rag_user", JSON.stringify(data.user));
      setSuccess("Name updated successfully.");
    } catch (err) {
      setError("Network error. Please try again.");
    } finally {
      setLoading(false);
    }
  }

  async function handlePasswordSubmit(e) {
    e.preventDefault();
    setError("");
    setSuccess("");

    if (!currentPassword || !newPassword || !confirmPassword) {
      setError("Please fill in all fields.");
      return;
    }
    if (newPassword.length < 6) {
      setError("New password must be at least 6 characters long.");
      return;
    }
    if (newPassword !== confirmPassword) {
      setError("New password and confirmation do not match.");
      return;
    }

    setLoading(true);
    try {
      const token = localStorage.getItem("rag_token");
      const res = await fetch(`${API_BASE_URL}/change-password`, {
        method: "PUT",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          current_password: currentPassword,
          new_password: newPassword,
        }),
      });

      const data = await res.json();

      if (!res.ok) {
        setError(data.detail || "Could not change password.");
        return;
      }

      setSuccess("Password changed successfully.");
      setCurrentPassword("");
      setNewPassword("");
      setConfirmPassword("");
    } catch (err) {
      setError("Network error. Please try again.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="modal-overlay" onMouseDown={(e) => e.target === e.currentTarget && onClose()}>
      <div className="modal-card">
        <div className="modal-header">
          <h3>Profile Settings</h3>
          <button className="modal-close" onClick={onClose} aria-label="Close">×</button>
        </div>

        <div className="modal-tabs">
          <button
            className={`modal-tab ${activeTab === "name" ? "active" : ""}`}
            onClick={() => switchTab("name")}
          >
            Name
          </button>
          <button
            className={`modal-tab ${activeTab === "password" ? "active" : ""}`}
            onClick={() => switchTab("password")}
          >
            Password
          </button>
        </div>

        <div className="modal-body">
          {error && <div className="form-msg error">{error}</div>}
          {success && <div className="form-msg success">{success}</div>}

          {activeTab === "name" ? (
            <form onSubmit={handleNameSubmit}>
              <div className="field-group">
                <label className="field-label">Full name</label>
                <input
                  className="field-input"
                  type="text"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  placeholder="Your name"
                  autoFocus
                />
              </div>
              <button className="btn btn-solid" type="submit" disabled={loading}>
                {loading ? "Saving..." : "Save name"}
              </button>
            </form>
          ) : (
            <form onSubmit={handlePasswordSubmit}>
              <div className="field-group">
                <label className="field-label">Current password</label>
                <input
                  className="field-input"
                  type="password"
                  value={currentPassword}
                  onChange={(e) => setCurrentPassword(e.target.value)}
                  placeholder="••••••••"
                  autoFocus
                />
              </div>
              <div className="field-group">
                <label className="field-label">New password</label>
                <input
                  className="field-input"
                  type="password"
                  value={newPassword}
                  onChange={(e) => setNewPassword(e.target.value)}
                  placeholder="At least 6 characters"
                />
              </div>
              <div className="field-group">
                <label className="field-label">Confirm new password</label>
                <input
                  className="field-input"
                  type="password"
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  placeholder="Re-enter new password"
                />
              </div>
              <button className="btn btn-solid" type="submit" disabled={loading}>
                {loading ? "Updating..." : "Update password"}
              </button>
            </form>
          )}
        </div>
      </div>
    </div>
  );
}

export default DashboardPage;