import { useState, useEffect } from "react";

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

  useEffect(() => {
    if (!chatId) return;

    const load = async () => {
      const res = await fetch(`${API_BASE_URL}/chat/${chatId}`);
      const data = await res.json();
      setMessages(data.messages || []);
    };

    load();
  }, [chatId]);

  const sendMessage = async () => {
    if (!input.trim()) return;

    const question = input;

    setMessages((prev) => [...prev, { role: "user", message: question }]);
    setInput("");
    setLoading(true);

    const res = await fetch(`${API_BASE_URL}/chat`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        question,
        document_id: document.file_id,
        user_id: user._id,
        chat_id: chatId,
      }),
    });

    const data = await res.json();

    setMessages((prev) => [...prev, { role: "assistant", message: data.answer }]);
    setLoading(false);
  };

  return (
    <div className="dashboard-page" style={{ background: COLORS.bg, minHeight: "100vh", color: COLORS.textLight }}>
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
        <div className="brand-block" style={{ display: "flex", alignItems: "center", gap: "10px" }}>
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
            <h1 style={{ color: COLORS.textLight, fontSize: "18px", margin: 0 }}>
              {document?.file_name}
            </h1>
            <p style={{ color: COLORS.textDim, margin: 0, fontSize: "13px" }}>Chat Session</p>
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

      <section style={{ display: "flex", flexDirection: "column", padding: "20px", gap: "10px" }}>
        <div
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
            <p style={{ color: COLORS.textDim, textAlign: "center", marginTop: "20px" }}>
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
              <span
                style={{
                  maxWidth: "75%",
                  padding: "10px 14px",
                  borderRadius: "14px",
                  background: m.role === "user" ? COLORS.orange : COLORS.assistantBubble,
                  color: m.role === "user" ? "#1a1a1a" : COLORS.textLight,
                  fontWeight: m.role === "user" ? 600 : 400,
                  lineHeight: "1.4",
                  wordBreak: "break-word",
                  display: "inline-block",
                }}
              >
                {m.message}
              </span>
            </div>
          ))}

          {loading && (
            <div style={{ display: "flex", justifyContent: "flex-start", margin: "8px 0" }}>
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

        <div style={{ display: "flex", gap: "10px", marginTop: "4px" }}>
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
            onKeyDown={(e) => e.key === "Enter" && sendMessage()}
          />
          <button
            onClick={sendMessage}
            style={{
              background: COLORS.orange,
              color: "#1a1a1a",
              border: "none",
              borderRadius: "10px",
              padding: "12px 22px",
              fontWeight: 600,
              cursor: "pointer",
            }}
            onMouseDown={(e) => (e.currentTarget.style.background = COLORS.orangeDark)}
            onMouseUp={(e) => (e.currentTarget.style.background = COLORS.orange)}
          >
            Send
          </button>
        </div>
      </section>
    </div>
  );
}

export default ChatPage;