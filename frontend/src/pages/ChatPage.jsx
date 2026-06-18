import { useState, useEffect, useRef } from "react";

const API_BASE_URL = "http://127.0.0.1:8000";

const COLORS = {
  bg: "#121212",
  panel: "#1a1a1a",
  border: "#2e2e2e",
  orange: "#ff7a18",
  orangeDark: "#e0670a",
  textLight: "#f2f2f2",
  textDim: "#b5b5b5",
  assistantBubble: "#262626",
};

function ChatPage({ user, document, chatId, messages, setMessages, goBack }) {
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const scrollRef = useRef(null);

  const getToken = () => localStorage.getItem("rag_token");

  useEffect(() => {
    if (!chatId) return;

    const loadChat = async () => {
      try {
        const token = getToken();

        if (!token) {
          setMessages([
            {
              role: "assistant",
              message: "Please login again. Your session is missing.",
            },
          ]);
          return;
        }

        const res = await fetch(`${API_BASE_URL}/chat/${chatId}`, {
          method: "GET",
          headers: {
            Authorization: `Bearer ${token}`,
          },
        });

        const data = await res.json();

        if (!res.ok) {
          setMessages([
            {
              role: "assistant",
              message: data.detail || "Could not load chat history.",
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

    const token = getToken();

    if (!token) {
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          message: "Please login again. Your session is missing.",
        },
      ]);
      return;
    }

    if (!document?.file_id) {
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          message: "No document selected.",
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
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
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
          },
        ]);
        return;
      }

      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          message: data.answer,
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
        },
      ]);
    } finally {
      setLoading(false);
    }
  };

  const renderStructuredAnswer = (message) => {
    const type = message.answer_type;
    const data = message.structured_answer;

    if (!data || type === "plain") {
      return <span>{message.message}</span>;
    }

    if (type === "mcq" || type === "quiz") {
      return (
        <div style={{ display: "flex", flexDirection: "column", gap: "14px" }}>
          {data.title && (
            <h3 style={{ margin: 0, color: COLORS.orange }}>{data.title}</h3>
          )}

          {(data.questions || []).map((q, index) => (
            <div
              key={index}
              style={{
                background: "#1f1f1f",
                border: `1px solid ${COLORS.border}`,
                borderLeft: `4px solid ${COLORS.orange}`,
                borderRadius: "12px",
                padding: "14px",
              }}
            >
              <p style={{ margin: "0 0 10px", fontWeight: 700 }}>
                {index + 1}. {q.question}
              </p>

              <div style={{ display: "grid", gap: "7px" }}>
                {(q.options || []).map((option, optionIndex) => (
                  <div
                    key={optionIndex}
                    style={{
                      background: "#151515",
                      border: `1px solid ${COLORS.border}`,
                      borderRadius: "8px",
                      padding: "8px 10px",
                    }}
                  >
                    {option}
                  </div>
                ))}
              </div>

              {q.answer && (
                <p style={{ margin: "12px 0 0", color: COLORS.orange }}>
                  <strong>Answer:</strong> {q.answer}
                </p>
              )}
            </div>
          ))}
        </div>
      );
    }

    if (type === "short_questions") {
      return (
        <div style={{ display: "flex", flexDirection: "column", gap: "12px" }}>
          {data.title && (
            <h3 style={{ margin: 0, color: COLORS.orange }}>{data.title}</h3>
          )}

          {(data.questions || []).map((q, index) => (
            <div
              key={index}
              style={{
                background: "#1f1f1f",
                border: `1px solid ${COLORS.border}`,
                borderLeft: `4px solid ${COLORS.orange}`,
                borderRadius: "12px",
                padding: "14px",
              }}
            >
              <p style={{ margin: "0 0 8px", fontWeight: 700 }}>
                {index + 1}. {q.question}
              </p>

              {q.answer && (
                <p style={{ margin: 0, color: COLORS.textDim }}>
                  <strong style={{ color: COLORS.orange }}>Answer:</strong>{" "}
                  {q.answer}
                </p>
              )}
            </div>
          ))}
        </div>
      );
    }

    if (type === "true_false") {
      return (
        <div style={{ display: "flex", flexDirection: "column", gap: "12px" }}>
          {data.title && (
            <h3 style={{ margin: 0, color: COLORS.orange }}>{data.title}</h3>
          )}

          {(data.statements || []).map((item, index) => (
            <div
              key={index}
              style={{
                background: "#1f1f1f",
                border: `1px solid ${COLORS.border}`,
                borderLeft: `4px solid ${COLORS.orange}`,
                borderRadius: "12px",
                padding: "14px",
              }}
            >
              <p style={{ margin: "0 0 8px", fontWeight: 700 }}>
                {index + 1}. {item.statement}
              </p>

              <span
                style={{
                  display: "inline-block",
                  background: item.answer === "True" ? "#1f3d2b" : "#3d1f1f",
                  color: COLORS.textLight,
                  borderRadius: "999px",
                  padding: "5px 12px",
                  fontWeight: 700,
                }}
              >
                {item.answer}
              </span>
            </div>
          ))}
        </div>
      );
    }

    if (type === "past_paper") {
      return (
        <div style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
          {data.title && (
            <h3 style={{ margin: 0, color: COLORS.orange }}>{data.title}</h3>
          )}

          {(data.sections || []).map((section, sectionIndex) => (
            <div
              key={sectionIndex}
              style={{
                background: "#1f1f1f",
                border: `1px solid ${COLORS.border}`,
                borderRadius: "12px",
                padding: "16px",
              }}
            >
              <h4 style={{ margin: "0 0 12px", color: COLORS.orange }}>
                {section.heading}
              </h4>

              {(section.questions || []).map((q, index) => (
                <div
                  key={index}
                  style={{
                    borderTop:
                      index === 0 ? "none" : `1px solid ${COLORS.border}`,
                    paddingTop: index === 0 ? 0 : "12px",
                    marginTop: index === 0 ? 0 : "12px",
                  }}
                >
                  <p style={{ margin: "0 0 8px", fontWeight: 700 }}>
                    {index + 1}. {q.question}
                  </p>

                  {q.marks && (
                    <p style={{ margin: 0, color: COLORS.textDim }}>
                      Marks: {q.marks}
                    </p>
                  )}

                  {q.answer && (
                    <p style={{ margin: "8px 0 0", color: COLORS.textDim }}>
                      <strong style={{ color: COLORS.orange }}>
                        Suggested answer:
                      </strong>{" "}
                      {q.answer}
                    </p>
                  )}
                </div>
              ))}
            </div>
          ))}
        </div>
      );
    }

    return <span>{message.message}</span>;
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
              color: COLORS.orange,
              fontSize: "20px",
              border: `1px solid ${COLORS.orange}`,
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
            color: COLORS.orange,
            border: `1px solid ${COLORS.orange}`,
            borderRadius: "8px",
            padding: "8px 16px",
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
                    m.role === "user" ? COLORS.orange : COLORS.assistantBubble,
                  color: m.role === "user" ? "#1a1a1a" : COLORS.textLight,
                  fontWeight: m.role === "user" ? 600 : 400,
                  lineHeight: "1.4",
                  wordBreak: "break-word",
                  display: "inline-block",
                  whiteSpace: "pre-wrap",
                }}
              >
                {m.role === "assistant" ? renderStructuredAnswer(m) : m.message}
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
              background: COLORS.orange,
              color: "#1a1a1a",
              border: "none",
              borderRadius: "10px",
              padding: "12px 22px",
              fontWeight: 600,
              cursor: loading ? "not-allowed" : "pointer",
              opacity: loading ? 0.7 : 1,
            }}
            onMouseDown={(e) => {
              if (!loading) {
                e.currentTarget.style.background = COLORS.orangeDark;
              }
            }}
            onMouseUp={(e) => {
              if (!loading) {
                e.currentTarget.style.background = COLORS.orange;
              }
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.background = COLORS.orange;
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