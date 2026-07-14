import { useEffect, useRef, useState } from "react";
import StructuredAnswer from "./StructuredAnswer";

const API_BASE_URL = import.meta.env.PROD ? "/api" : "http://localhost:8000";

async function readApiResponse(response) {
  const contentType = response.headers.get("content-type") || "";

  if (contentType.includes("application/json")) {
    return response.json();
  }

  const responseText = await response.text();
  const preview = responseText.replace(/\s+/g, " ").trim().slice(0, 180);

  throw new Error(
    `Backend returned ${response.status}${preview ? `: ${preview}` : ""}`
  );
}

function getFileExtension(fileName = "") {
  const dotIndex = fileName.lastIndexOf(".");
  return dotIndex >= 0 ? fileName.slice(dotIndex).toLowerCase() : "";
}

function canPreviewInBrowser(fileName = "") {
  return [".pdf", ".png", ".jpg", ".jpeg", ".txt"].includes(
    getFileExtension(fileName)
  );
}

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
  const [openingDocument, setOpeningDocument] = useState(false);

  const scrollRef = useRef(null);
  const inputRef = useRef(null);

  useEffect(() => {
    if (scrollRef.current && window.innerWidth > 1024) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages, sending]);

  const handleFileChange = (event) => {
    const selectedFile = event.target.files?.[0] || null;

    setFile(selectedFile);
    setDocumentName(selectedFile ? selectedFile.name : "");
    setMessage("");
    setUploadedDoc(null);
    setMessages([]);
    setChatId(null);
    setInput("");
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

      const data = await readApiResponse(response);

      if (!response.ok) {
        setMessage(data.detail || "Upload failed.");
        return;
      }

      setMessage(
        data.message ||
          "Document uploaded, processed, and stored in the RAG system successfully."
      );

      if (!data.document) {
        setMessage("Document uploaded, but document details were not returned.");
        return;
      }

      setUploadedDoc(data.document);
      setMessages([]);

      const sessionRes = await fetch(
        `${API_BASE_URL}/chat/session?document_id=${data.document.file_id}`,
        {
          method: "GET",
          credentials: "include",
        }
      );

      const sessionData = await readApiResponse(sessionRes);

      if (!sessionRes.ok) {
        setMessage(sessionData.detail || "Could not create chat session.");
        return;
      }

      setChatId(sessionData.chat_id);
    } catch (error) {
      console.error("Upload error:", error);
      setMessage(
        error?.message ||
          "Could not connect to backend. Please make sure backend is running."
      );
    } finally {
      setLoading(false);
    }
  };

  const addAssistantError = (errorMessage) => {
    setMessages((previousMessages) => [
      ...previousMessages,
      {
        role: "assistant",
        message: errorMessage,
        answer_type: "plain",
        structured_answer: null,
        citations: [],
      },
    ]);
  };

  const sendMessage = async () => {
    if (!input.trim() || !uploadedDoc || !chatId || sending) return;

    const question = input.trim();

    setMessages((previousMessages) => [
      ...previousMessages,
      {
        role: "user",
        message: question,
        answer_type: "plain",
        structured_answer: null,
        citations: [],
      },
    ]);

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

      const data = await readApiResponse(res);

      if (!res.ok) {
        addAssistantError(data.detail || "Something went wrong.");
        return;
      }

      setMessages((previousMessages) => [
        ...previousMessages,
        {
          role: "assistant",
          message: data.answer || "No answer returned from the server.",
          answer_type: data.answer_type || "plain",
          structured_answer: data.structured_answer || null,
          citations: Array.isArray(data.citations) ? data.citations : [],
        },
      ]);
    } catch (error) {
      console.error("Chat request error:", error);
      addAssistantError(
        error?.message || "Something went wrong reaching the server."
      );
    } finally {
      setSending(false);
      inputRef.current?.focus();
    }
  };

  const openUploadedDocument = async () => {
    if (!uploadedDoc?.file_id || openingDocument) return;

    const previewable = canPreviewInBrowser(uploadedDoc.file_name);
    const previewWindow = previewable
      ? window.open("about:blank", "_blank")
      : null;

    try {
      setOpeningDocument(true);

      const response = await fetch(
        `${API_BASE_URL}/documents/file/${uploadedDoc.file_id}`,
        {
          method: "GET",
          credentials: "include",
        }
      );

      if (!response.ok) {
        const data = await readApiResponse(response);
        throw new Error(data.detail || "Could not open the document.");
      }

      const blob = await response.blob();
      const objectUrl = URL.createObjectURL(blob);

      if (previewable) {
        if (previewWindow) {
          previewWindow.location.replace(objectUrl);
        } else {
          window.location.assign(objectUrl);
        }
      } else {
        previewWindow?.close();

        const downloadLink = window.document.createElement("a");
        downloadLink.href = objectUrl;
        downloadLink.download = uploadedDoc.file_name || "document";
        window.document.body.appendChild(downloadLink);
        downloadLink.click();
        downloadLink.remove();
      }

      window.setTimeout(() => URL.revokeObjectURL(objectUrl), 60_000);
    } catch (error) {
      previewWindow?.close();
      console.error("Document open error:", error);
      setMessage(error?.message || "Could not open the uploaded document.");
    } finally {
      setOpeningDocument(false);
    }
  };

  return (
    <div className="rag-card">
      <header className="rag-header">
        <div className="brand-block">
          <div className="brand-icon" aria-hidden="true">
            ▣
          </div>

          <div className="brand-copy">
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
              accept=".pdf,.txt,.docx,.pptx,.csv,.xlsx,.jpg,.jpeg,.png"
              onChange={handleFileChange}
              hidden
            />

            <div className="cloud-icon" aria-hidden="true">
              ☁
            </div>

            <p>{documentName || "Drop file here or tap to browse"}</p>

            <span className="file-types">
              {uploadedDoc
                ? `${file?.name
                    ?.split(".")
                    .pop()
                    ?.toUpperCase()} document processed successfully`
                : "PDF, TXT, DOCX, PPTX, CSV, XLSX, JPG, JPEG, PNG supported"}
            </span>
          </label>

          <button
            className="process-btn"
            onClick={handleUpload}
            disabled={loading || !file}
          >
            {loading ? "Processing..." : "Process Document"}
          </button>

          {uploadedDoc && (
            <button
              type="button"
              className="view-document-btn"
              onClick={openUploadedDocument}
              disabled={openingDocument}
            >
              {openingDocument ? "Opening..." : "View Original Document"}
            </button>
          )}

          {message && (
            <div className="small-status" role="status" aria-live="polite">
              {message}
            </div>
          )}

          <p className="ocr-disclaimer">
            OCR support is currently limited to scanned PDFs and standalone
            images.
          </p>
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
              messages.map((chatMessage, index) => (
                <div
                  key={`${chatMessage.role}-${index}`}
                  className={
                    chatMessage.role === "user"
                      ? "user-message"
                      : "bot-message"
                  }
                >
                  {chatMessage.role === "assistant" ? (
                    <StructuredAnswer
                      message={chatMessage}
                      accentColor="#e53935"
                    />
                  ) : (
                    chatMessage.message
                  )}
                </div>
              ))}

            {sending && <div className="bot-message">Thinking...</div>}
          </div>

          <div className="chat-input-row">
            <textarea
              ref={inputRef}
              rows={1}
              value={input}
              onChange={(event) => setInput(event.target.value)}
              placeholder={
                uploadedDoc
                  ? "Ask something about this document..."
                  : "Upload a document first..."
              }
              disabled={!uploadedDoc || !chatId || sending}
              onKeyDown={(event) => {
                if (event.key === "Enter" && !event.shiftKey) {
                  event.preventDefault();
                  sendMessage();
                }
              }}
            />

            <button
              type="button"
              aria-label="Send message"
              onClick={sendMessage}
              disabled={!uploadedDoc || !chatId || sending || !input.trim()}
            >
              ↑
            </button>
          </div>

          <p className="chat-disclaimer">
            You can write your question in any language. RAG Assistant will
            answer in English only.
          </p>
        </main>
      </div>
    </div>
  );
}

export default UploadBox;