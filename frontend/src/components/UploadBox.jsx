import { useState, useRef, useEffect } from "react";
import StructuredAnswer from "./StructuredAnswer";

const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

function UploadBox({ user }) {
  const [file, setFile] = useState(null);
  const [message, setMessage] = useState("");
  const [loading, setLoading] = useState(false);
  const [documentName, setDocumentName] = useState("");

  const [uploadedDoc, setUploadedDoc] = useState(null);
  const [chatId, setChatId] = useState(null);
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [sending, setSending] = useState(false);

  const scrollRef = useRef(null);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages, sending]);

  const handleFileChange = (event) => {
    const selectedFile = event.target.files[0];

    setFile(selectedFile);
    setDocumentName(selectedFile ? selectedFile.name : "");
    setMessage("");
    setUploadedDoc(null);
    setMessages([]);
    setChatId(null);
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

      const response = await fetch(`${API_BASE_URL}/upload`, {
        method: "POST",
        credentials: "include",
        body: formData,
      });

      const data = await response.json();

      if (!response.ok) {
        setMessage(data.detail || "Upload failed.");
        return;
      }

      setMessage(
        data.message ||
          "Document uploaded, processed, and stored in RAG system successfully."
      );

      if (data.document) {
        setUploadedDoc(data.document);
        setMessages([]);

        const sessionRes = await fetch(
          `${API_BASE_URL}/chat/session?document_id=${data.document.file_id}`,
          {
            method: "GET",
            credentials: "include",
          }
        );

        const sessionData = await sessionRes.json();

        if (!sessionRes.ok) {
          setMessage(sessionData.detail || "Could not create chat session.");
          return;
        }

        setChatId(sessionData.chat_id);
      }
    } catch (error) {
      setMessage(
        "Could not connect to backend. Please make sure backend is running."
      );
    } finally {
      setLoading(false);
    }
  };

  const sendMessage = async () => {
    if (!input.trim() || !uploadedDoc || !chatId || sending) return;

    const question = input.trim();

    setMessages((prev) => [...prev, { role: "user", message: question }]);
    setInput("");
    setSending(true);

    try {
      const res = await fetch(`${API_BASE_URL}/chat`, {
        method: "POST",
        credentials: "include",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          question,
          document_id: uploadedDoc.file_id,
          chat_id: chatId,
        }),
      });

      const data = await res.json();

      if (!res.ok) {
        setMessages((prev) => [
          ...prev,
          {
            role: "assistant",
            message: data.detail || "Something went wrong.",
            answer_type: "plain",
            structured_answer: null,
          },
        ]);
        return;
      }

      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          message: data.answer || "No answer returned from the server.",
          answer_type: data.answer_type || "plain",
          structured_answer: data.structured_answer || null,
        },
      ]);
    } catch (err) {
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          message: "Something went wrong reaching the server.",
          answer_type: "plain",
          structured_answer: null,
        },
      ]);
    } finally {
      setSending(false);
    }
  };

  return (
    <div className="rag-card">
      <header className="rag-header">
        <div className="brand-block">
          <div className="brand-icon">▣</div>

          <div>
            <h1>RAG Assistant</h1>
            <p>
              {uploadedDoc ? "Document processed" : "Upload a document to begin"}
            </p>
          </div>
        </div>

        <div className="chunks-status">
          {uploadedDoc
            ? `${uploadedDoc.chunks_count ?? 0} chunks active`
            : "0 chunks active"}
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
              {uploadedDoc
                ? `${file?.name
                    ?.split(".")
                    .pop()
                    ?.toUpperCase()} document processed successfully`
                : "PDF, TXT, DOCX, PPTX, CSV, XLSX supported"}
            </span>
          </label>

          <button className="process-btn" onClick={handleUpload} disabled={loading}>
            {loading ? "Processing..." : "Process Document"}
          </button>

          {message && <div className="small-status">{message}</div>}
        </aside>

        <main className="chat-panel">
          <div className="panel-label">CHAT</div>

          <div className="chat-area" ref={scrollRef}>
            {!uploadedDoc && (
              <div className="bot-message">
                Upload a document first so we can start chatting about it.
              </div>
            )}

            {uploadedDoc && messages.length === 0 && (
              <div className="bot-message">
                Document loaded. Ask your first question.
              </div>
            )}

            {uploadedDoc &&
              messages.map((m, i) => (
                <div
                  key={i}
                  className={m.role === "user" ? "user-message" : "bot-message"}
                >
                  {m.role === "assistant" ? (
                    <StructuredAnswer message={m} accentColor="#e53935" />
                  ) : (
                    m.message
                  )}
                </div>
              ))}

            {sending && <div className="bot-message">Thinking...</div>}
          </div>

          <div className="chat-input-row">
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder={
                uploadedDoc
                  ? "Ask something about this document..."
                  : "Upload a document first..."
              }
              disabled={!uploadedDoc || sending}
              onKeyDown={(e) => {
                if (e.key === "Enter") {
                  sendMessage();
                }
              }}
            />

            <button onClick={sendMessage} disabled={!uploadedDoc || sending}>
              ↑
            </button>
          </div>

          <p
            style={{
              color: "#8f8f8f",
              fontSize: "12px",
              textAlign: "center",
              margin: "8px 0 0",
            }}
          >
            You can write your question in any language. RAG Assistant will
            answer in English only.
          </p>
        </main>
      </div>
    </div>
  );
}

export default UploadBox;