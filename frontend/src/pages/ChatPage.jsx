import { useState, useEffect, useRef } from "react";
import StructuredAnswer from "../components/StructuredAnswer";

const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

const COLORS = {
  bg: "#121212",
  panel: "#1a1a1a",
  border: "#2e2e2e",
  red: "#e53935",
  redDark: "#c62828",
  textLight: "#f2f2f2",
  textDim: "#b5b5b5",
  assistantBubble: "#262626",
};

function ChatPage({ user, document, chatId, messages, setMessages, goBack }) {
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
      className="dashboard-page"
      style={{
        background: COLORS.bg,
        minHeight: "100vh",
        color: COLORS.textLight,
      }}
    >
      <header
        className="dashboard-header"
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          padding: "16px 20px",
          borderBottom: `1px solid ${COLORS.border}`,
        }}
      >
        <div
          className="brand-block"
          style={{
            display: "flex",
            alignItems: "center",
            gap: "10px",
          }}
        >
          <div
            className="brand-icon"
            style={{
              background: COLORS.red,
              color: COLORS.textLight,
              fontSize: "20px",
              border: `1px solid ${COLORS.red}`,
              borderRadius: "8px",
              width: "34px",
              height: "34px",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
            }}
          >
            ▣
          </div>

          <div>
            <h1
              style={{
                color: COLORS.textLight,
                fontSize: "18px",
                margin: 0,
              }}
            >
              {document?.file_name || "Document Chat"}
            </h1>

            <p
              style={{
                color: COLORS.textDim,
                margin: 0,
                fontSize: "13px",
              }}
            >
              Chat Session
            </p>
          </div>
        </div>

        <button
          onClick={goBack}
          style={{
            background: "transparent",
            color: COLORS.red,
            border: `1px solid ${COLORS.red}`,
            borderRadius: "8px",
            padding: "8px 16px",
            fontWeight: 700,
            cursor: "pointer",
          }}
        >
          Back
        </button>
      </header>

      <section
        style={{
          display: "flex",
          flexDirection: "column",
          padding: "20px",
          gap: "10px",
        }}
      >
        <div
          ref={scrollRef}
          style={{
            width: "100%",
            height: "60vh",
            overflowY: "auto",
            background: COLORS.panel,
            border: `1px solid ${COLORS.border}`,
            borderRadius: "12px",
            padding: "16px",
            display: "flex",
            flexDirection: "column",
          }}
        >
          {messages.length === 0 && !loading && (
            <p
              style={{
                color: COLORS.textDim,
                textAlign: "center",
                marginTop: "20px",
              }}
            >
              Ask something about this document to get started.
            </p>
          )}

          {messages.map((m, i) => (
            <div
              key={i}
              style={{
                display: "flex",
                justifyContent: m.role === "user" ? "flex-end" : "flex-start",
                margin: "8px 0",
              }}
            >
              <div
                style={{
                  maxWidth:
                    m.answer_type && m.answer_type !== "plain" ? "90%" : "75%",
                  padding: "10px 14px",
                  borderRadius: "14px",
                  background:
                    m.role === "user" ? COLORS.red : COLORS.assistantBubble,
                  border:
                    m.role === "assistant"
                      ? `1px solid ${COLORS.border}`
                      : "none",
                  color: COLORS.textLight,
                  fontWeight: m.role === "user" ? 700 : 400,
                  lineHeight: "1.4",
                  wordBreak: "break-word",
                  display: "inline-block",
                  whiteSpace: "pre-wrap",
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
            <div
              style={{
                display: "flex",
                justifyContent: "flex-start",
                margin: "8px 0",
              }}
            >
              <span
                style={{
                  padding: "10px 14px",
                  borderRadius: "14px",
                  background: COLORS.assistantBubble,
                  border: `1px solid ${COLORS.border}`,
                  color: COLORS.textDim,
                  fontStyle: "italic",
                }}
              >
                Thinking...
              </span>
            </div>
          )}
        </div>

        <div
          style={{
            display: "flex",
            gap: "10px",
            marginTop: "4px",
          }}
        >
          <input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Ask something..."
            style={{
              flex: 1,
              padding: "12px 14px",
              borderRadius: "10px",
              border: `1px solid ${COLORS.border}`,
              background: COLORS.panel,
              color: COLORS.textLight,
              outline: "none",
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
              padding: "12px 22px",
              fontWeight: 700,
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
            Send
          </button>
        </div>

        <p
          style={{
            color: COLORS.textDim,
            fontSize: "12px",
            textAlign: "center",
            margin: "6px 0 0",
          }}
        >
          You can write your question in any language. RAG Assistant will answer
          in English only.
        </p>
      </section>
    </div>
  );
}

export default ChatPage;