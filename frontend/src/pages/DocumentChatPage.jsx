import { useState, useEffect, useRef } from "react";
import StructuredAnswer from "../components/StructuredAnswer";

const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

const COLORS = {
  bg: "#050505",
  panel: "#141414",
  panelDark: "#101010",
  border: "#2e2e2e",
  red: "#e53935",
  redDark: "#c62828",
  textLight: "#f2f2f2",
  textDim: "#8f8f8f",
  assistantBubble: "#1b1b1b",
};

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
  const scrollRef = useRef(null);

  useEffect(() => {
    if (!chatId) return;

    const loadChat = async () => {
      try {
        const res = await fetch(`${API_BASE_URL}/chat/${chatId}`, {
          method: "GET",
          credentials: "include",
        });

        const data = await res.json();

        if (!res.ok) {
          setMessages([
            {
              role: "assistant",
              message: data.detail || "Could not load chat history.",
              answer_type: "plain",
              structured_answer: null,
            },
          ]);
          return;
        }

        setMessages(data.messages || []);
      } catch (error) {
        setMessages([
          {
            role: "assistant",
            message: "Could not load chat history.",
            answer_type: "plain",
            structured_answer: null,
          },
        ]);
      }
    };

    loadChat();
  }, [chatId, setMessages]);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages, loading]);

  const sendMessage = async () => {
    if (!input.trim() || loading) return;

    if (!document?.file_id) {
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          message: "No document selected.",
          answer_type: "plain",
          structured_answer: null,
        },
      ]);
      return;
    }

    const question = input.trim();

    setMessages((prev) => [...prev, { role: "user", message: question }]);
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
    } catch (error) {
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          message: "Could not connect to backend.",
          answer_type: "plain",
          structured_answer: null,
        },
      ]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div
      className="document-chat-page"
      style={{
        background: COLORS.bg,
        minHeight: "100vh",
        color: COLORS.textLight,
      }}
    >
      <header
        style={{
          display: "flex",
          gap: "14px",
          alignItems: "center",
          padding: "18px 22px",
          borderBottom: `1px solid ${COLORS.border}`,
        }}
      >
        <button
          onClick={goBack}
          style={{
            background: COLORS.red,
            color: COLORS.textLight,
            border: "none",
            borderRadius: "10px",
            padding: "12px 22px",
            fontWeight: 700,
            cursor: "pointer",
          }}
        >
          ← Dashboard
        </button>

        <button
          onClick={goToHistory}
          style={{
            background: COLORS.red,
            color: COLORS.textLight,
            border: "none",
            borderRadius: "10px",
            padding: "12px 22px",
            fontWeight: 700,
            cursor: "pointer",
          }}
        >
          Document History
        </button>
      </header>

      <section
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          padding: "22px",
          borderBottom: `1px solid ${COLORS.border}`,
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: "14px" }}>
          <div
            style={{
              width: "58px",
              height: "58px",
              borderRadius: "10px",
              background: COLORS.red,
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              fontSize: "22px",
              color: COLORS.textLight,
            }}
          >
            ▣
          </div>

          <div>
            <h1
              style={{
                margin: 0,
                fontSize: "26px",
                color: COLORS.textLight,
              }}
            >
              RAG Assistant
            </h1>

            <p
              style={{
                margin: "4px 0 0",
                color: COLORS.textDim,
                fontSize: "14px",
              }}
            >
              Document processed
            </p>
          </div>
        </div>

        {document?.chunks_count && (
          <p
            style={{
              margin: 0,
              color: COLORS.textDim,
              fontWeight: 700,
              fontSize: "14px",
            }}
          >
            {document.chunks_count} chunks active
          </p>
        )}
      </section>

      <main
        style={{
          display: "grid",
          gridTemplateColumns: "42% 58%",
          minHeight: "calc(100vh - 160px)",
        }}
      >
        <aside
          style={{
            padding: "28px 22px",
            borderRight: `1px solid ${COLORS.border}`,
          }}
        >
          <h2
            style={{
              color: COLORS.textDim,
              fontSize: "13px",
              letterSpacing: "8px",
              margin: "0 0 18px",
            }}
          >
            DOCUMENT
          </h2>

          <div
            style={{
              background: COLORS.panelDark,
              border: `1px dashed ${COLORS.border}`,
              borderRadius: "12px",
              padding: "46px 20px",
              textAlign: "center",
              marginBottom: "18px",
            }}
          >
            <div
              style={{
                color: COLORS.red,
                fontSize: "30px",
                marginBottom: "14px",
              }}
            >
              ☁
            </div>

            <p
              style={{
                margin: 0,
                color: COLORS.textDim,
                fontSize: "15px",
              }}
            >
              {document?.file_name || "No document selected"}
            </p>

            <p
              style={{
                margin: "8px 0 0",
                color: COLORS.textDim,
                fontSize: "13px",
              }}
            >
              Document processed successfully
            </p>
          </div>

          <button
            style={{
              width: "100%",
              background: COLORS.red,
              color: COLORS.textLight,
              border: "none",
              borderRadius: "10px",
              padding: "16px",
              fontWeight: 800,
              fontSize: "15px",
              cursor: "default",
              marginBottom: "14px",
            }}
          >
            Process Document
          </button>

          <div
            style={{
              background: COLORS.panelDark,
              border: `1px solid ${COLORS.border}`,
              borderRadius: "10px",
              padding: "14px",
              color: COLORS.textLight,
              fontSize: "14px",
            }}
          >
            Document uploaded, processed, and stored in RAG system successfully
          </div>
        </aside>

        <section
          style={{
            padding: "28px 22px",
            display: "flex",
            flexDirection: "column",
          }}
        >
          <h2
            style={{
              color: COLORS.textDim,
              fontSize: "13px",
              letterSpacing: "8px",
              margin: "0 0 18px",
            }}
          >
            CHAT
          </h2>

          <div
            ref={scrollRef}
            style={{
              flex: 1,
              minHeight: "430px",
              maxHeight: "58vh",
              overflowY: "auto",
              background: "transparent",
              borderRadius: "12px",
              padding: "10px 0",
              display: "flex",
              flexDirection: "column",
              gap: "10px",
            }}
          >
            {messages.length === 0 && !loading && (
              <p
                style={{
                  color: COLORS.textDim,
                  textAlign: "center",
                  marginTop: "80px",
                }}
              >
                Ask something about this document to get started.
              </p>
            )}

            {messages.map((m, index) => (
              <div
                key={index}
                style={{
                  display: "flex",
                  justifyContent:
                    m.role === "user" ? "flex-end" : "flex-start",
                }}
              >
                <div
                  style={{
                    maxWidth:
                      m.answer_type && m.answer_type !== "plain" ? "90%" : "75%",
                    padding: "16px 18px",
                    borderRadius: "10px",
                    background:
                      m.role === "user" ? COLORS.red : COLORS.assistantBubble,
                    border:
                      m.role === "assistant"
                        ? `1px solid ${COLORS.border}`
                        : "none",
                    color: COLORS.textLight,
                    lineHeight: "1.55",
                    whiteSpace: "pre-wrap",
                    wordBreak: "break-word",
                    fontWeight: m.role === "user" ? 700 : 400,
                  }}
                >
                  {m.role === "assistant" ? (
                    <StructuredAnswer message={m} accentColor={COLORS.red} />
                  ) : (
                    m.message
                  )}
                </div>
              </div>
            ))}

            {loading && (
              <div style={{ display: "flex", justifyContent: "flex-start" }}>
                <div
                  style={{
                    padding: "14px 18px",
                    borderRadius: "10px",
                    background: COLORS.assistantBubble,
                    border: `1px solid ${COLORS.border}`,
                    color: COLORS.textDim,
                    fontStyle: "italic",
                  }}
                >
                  Thinking...
                </div>
              </div>
            )}
          </div>

          <div
            style={{
              display: "flex",
              gap: "10px",
              marginTop: "16px",
            }}
          >
            <input
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Ask something about this document..."
              style={{
                flex: 1,
                padding: "15px 16px",
                borderRadius: "10px",
                border: `1px solid ${COLORS.border}`,
                background: COLORS.panelDark,
                color: COLORS.textLight,
                outline: "none",
                fontSize: "14px",
              }}
              onKeyDown={(e) => {
                if (e.key === "Enter") {
                  sendMessage();
                }
              }}
            />

            <button
              onClick={sendMessage}
              disabled={loading}
              style={{
                background: COLORS.red,
                color: COLORS.textLight,
                border: "none",
                borderRadius: "10px",
                padding: "0 22px",
                fontWeight: 800,
                fontSize: "18px",
                cursor: loading ? "not-allowed" : "pointer",
                opacity: loading ? 0.7 : 1,
              }}
              onMouseDown={(e) => {
                if (!loading) {
                  e.currentTarget.style.background = COLORS.redDark;
                }
              }}
              onMouseUp={(e) => {
                if (!loading) {
                  e.currentTarget.style.background = COLORS.red;
                }
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.background = COLORS.red;
              }}
            >
              ↑
            </button>
          </div>

          <p
            style={{
              color: COLORS.textDim,
              fontSize: "12px",
              textAlign: "center",
              margin: "8px 0 0",
            }}
          >
            You can write your question in any language. RAG Assistant will
            answer in English only.
          </p>
        </section>
      </main>
    </div>
  );
}

export default DocumentChatPage;