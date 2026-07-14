import { useEffect, useRef, useState } from "react";
import StructuredAnswer from "../components/StructuredAnswer";

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

function normalizeLoadedMessages(messages) {
  if (!Array.isArray(messages)) return [];

  return messages.map((message) => ({
    role: message.role,
    message: message.message || "",
    answer_type: message.answer_type || "plain",
    structured_answer: message.structured_answer || null,
    citations: Array.isArray(message.citations) ? message.citations : [],
  }));
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

function DocumentChatPage({
  user,
  document,
  chatId,
  messages,
  setMessages,
  goBack,
  goToHistory,
}) {
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [openingDocument, setOpeningDocument] = useState(false);
  const scrollRef = useRef(null);
  const inputRef = useRef(null);

  useEffect(() => {
    if (!chatId) return;

    const loadChat = async () => {
      try {
        const res = await fetch(`${API_BASE_URL}/chat/${chatId}`, {
          method: "GET",
          credentials: "include",
        });

        const data = await readApiResponse(res);

        if (!res.ok) {
          setMessages([
            {
              role: "assistant",
              message: data.detail || "Could not load chat history.",
              answer_type: "plain",
              structured_answer: null,
              citations: [],
            },
          ]);
          return;
        }

        setMessages(normalizeLoadedMessages(data.messages));
      } catch (error) {
        console.error("Chat history error:", error);

        setMessages([
          {
            role: "assistant",
            message:
              error?.message || "Could not load chat history from the server.",
            answer_type: "plain",
            structured_answer: null,
            citations: [],
          },
        ]);
      }
    };

    loadChat();
  }, [chatId, setMessages]);

  useEffect(() => {
    if (scrollRef.current && window.innerWidth > 1024) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages, loading]);

  const addAssistantError = (message) => {
    setMessages((previousMessages) => [
      ...previousMessages,
      {
        role: "assistant",
        message,
        answer_type: "plain",
        structured_answer: null,
        citations: [],
      },
    ]);
  };

  const sendMessage = async () => {
    if (!input.trim() || loading) return;

    if (!document?.file_id) {
      addAssistantError("No document selected.");
      return;
    }

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
    setLoading(true);

    try {
      const res = await fetch(`${API_BASE_URL}/chat`, {
        method: "POST",
        credentials: "include",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          question,
          document_id: document.file_id,
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
      addAssistantError(error?.message || "Could not connect to backend.");
    } finally {
      setLoading(false);
      inputRef.current?.focus();
    }
  };

  const openOriginalDocument = async () => {
    if (!document?.file_id || openingDocument) return;

    const previewable = canPreviewInBrowser(document.file_name);
    const previewWindow = previewable
      ? window.open("about:blank", "_blank")
      : null;

    try {
      setOpeningDocument(true);

      const response = await fetch(
        `${API_BASE_URL}/documents/file/${document.file_id}`,
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
        downloadLink.download = document.file_name || "document";
        window.document.body.appendChild(downloadLink);
        downloadLink.click();
        downloadLink.remove();
      }

      window.setTimeout(() => URL.revokeObjectURL(objectUrl), 60_000);
    } catch (error) {
      previewWindow?.close();
      console.error("Document open error:", error);
      addAssistantError(error?.message || "Could not open the original document.");
    } finally {
      setOpeningDocument(false);
    }
  };

  return (
    <div className="document-chat-page">
      <header className="document-chat-nav">
        <div className="document-chat-nav-actions">
          <button type="button" onClick={goBack}>
            ← Dashboard
          </button>

          {goToHistory && (
            <button type="button" onClick={goToHistory}>
              Document History
            </button>
          )}
        </div>
      </header>

      <section className="document-chat-hero">
        <div className="brand-block">
          <div className="brand-icon" aria-hidden="true">
            ▣
          </div>

          <div className="brand-copy">
            <h1>RAG Assistant</h1>
            <p>Document processed</p>
          </div>
        </div>

        <span className="chunks-status">
          {document?.chunks_count ?? 0} chunks active
        </span>
      </section>

      <main className="document-chat-layout">
        <aside className="document-chat-sidebar">
          <div className="panel-label">DOCUMENT</div>

          <div className="history-document-card">
            <div className="cloud-icon" aria-hidden="true">
              ☁
            </div>

            <strong>{document?.file_name || "No document selected"}</strong>
            <span>
              {document?.file_type
                ? `${document.file_type.toUpperCase()} document`
                : "Uploaded document"}
            </span>
          </div>

          <button
            type="button"
            className="view-document-btn"
            onClick={openOriginalDocument}
            disabled={!document?.file_id || openingDocument}
          >
            {openingDocument ? "Opening..." : "View Original Document"}
          </button>

          <div className="document-details-box">
            <p>
              <strong>Status:</strong> Processed
            </p>
            <p>
              <strong>Chunks:</strong> {document?.chunks_count ?? 0}
            </p>
            <p>
              <strong>Uploaded:</strong>{" "}
              {document?.upload_date
                ? new Date(document.upload_date).toLocaleString()
                : "Available in document history"}
            </p>
          </div>
        </aside>

        <section className="document-chat-chat">
          <div className="panel-label">CHAT</div>

          <div className="document-chat-messages" ref={scrollRef}>
            {messages.length === 0 && !loading && (
              <p className="chat-empty-state">
                Ask something about this document to get started.
              </p>
            )}

            {messages.map((message, index) => (
              <div
                key={`${message.role}-${index}`}
                className={`chat-message-row ${
                  message.role === "user" ? "chat-message-row-user" : ""
                }`}
              >
                <div
                  className={`chat-message-bubble ${
                    message.role === "user"
                      ? "chat-message-bubble-user"
                      : "chat-message-bubble-assistant"
                  } ${
                    message.answer_type && message.answer_type !== "plain"
                      ? "chat-message-bubble-structured"
                      : ""
                  }`}
                >
                  {message.role === "assistant" ? (
                    <StructuredAnswer message={message} accentColor="#e53935" />
                  ) : (
                    message.message
                  )}
                </div>
              </div>
            ))}

            {loading && (
              <div className="chat-message-row">
                <div className="chat-message-bubble chat-message-bubble-assistant thinking-message">
                  Thinking...
                </div>
              </div>
            )}
          </div>

          <div className="document-chat-composer">
            <textarea
              ref={inputRef}
              rows={1}
              value={input}
              onChange={(event) => setInput(event.target.value)}
              placeholder="Ask something about this document..."
              disabled={loading}
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
              disabled={loading || !input.trim()}
            >
              ↑
            </button>
          </div>

          <p className="standalone-chat-disclaimer">
            You can write your question in any language. RAG Assistant will
            answer in English only.
          </p>
        </section>
      </main>
    </div>
  );
}

export default DocumentChatPage;