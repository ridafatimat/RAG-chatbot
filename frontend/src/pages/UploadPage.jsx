import UploadBox from "../components/UploadBox";

function UploadPage({ user, goBack, goToHistory, openDocumentChat }) {
  return (
    <div className="app-shell">
      <div className="top-nav">
        <button onClick={goBack}>← Dashboard</button>
        <button onClick={goToHistory}>Document History</button>
      </div>

      <UploadBox user={user} openDocumentChat={openDocumentChat} />
    </div>
  );
}

export default UploadPage;