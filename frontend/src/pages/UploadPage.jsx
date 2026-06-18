import UploadBox from "../components/UploadBox";

function UploadPage({ user, goBack, goToHistory, openDocumentChat }) {
  return (
    <div className="app-shell">
      <div className="top-nav">
        <button onClick={goBack}>← Dashboard</button>
        <button onClick={goToHistory}>Document History</button>
      </div>

      <UploadBox user={user} openDocumentChat={openDocumentChat} />

      <p
        style={{
          color: "#8f8f8f",
          fontSize: "12px",
          textAlign: "center",
          margin: "10px 0 0",
        }}
      >
        You can write your question in any language. RAG Assistant will answer
        in English only.
      </p>
    </div>
  );
}

export default UploadPage;