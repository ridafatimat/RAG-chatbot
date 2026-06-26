import { useEffect, useState } from "react";

import LoginPage from "./pages/LoginPage";
import HomePage from "./pages/HomePage";
import DashboardPage from "./pages/DashboardPage";
import UploadPage from "./pages/UploadPage";
import HistoryPage from "./pages/HistoryPage";
import ChatPage from "./pages/ChatPage";

import "./App.css";

const API_BASE_URL = "http://127.0.0.1:8000";

function App() {
  const [page, setPage] = useState("home");
  const [user, setUser] = useState(null);

  const [selectedDocument, setSelectedDocument] = useState(null);
  const [chatId, setChatId] = useState(null);
  const [messages, setMessages] = useState([]);

  // ---------------- LOGIN RESTORE ----------------
  useEffect(() => {
    const savedUser = localStorage.getItem("rag_user");
    if (!savedUser) return;
    try {
      const parsedUser = JSON.parse(savedUser);
      if (parsedUser?._id && parsedUser?.email) {
        setUser(parsedUser);
        setPage("dashboard");
      } else {
        localStorage.removeItem("rag_user");
        setPage("home");
      }
    } catch {
      localStorage.removeItem("rag_user");
      setPage("home");
    }
  }, []);

  // ---------------- OPEN CHAT ----------------
  const openDocumentChat = async (doc) => {
    if (!user?._id || !doc?.file_id) {
      console.error("Missing user ID or document ID.");
      return;
    }
    setSelectedDocument(doc);
    setMessages([]);
    try {
      const res = await fetch(
        `${API_BASE_URL}/chat/session?user_id=${user._id}&document_id=${doc.file_id}`
      );
      const data = await res.json();
      if (!res.ok) {
        console.error("Could not open chat session:", data.detail);
        return;
      }
      setChatId(data.chat_id);
      setPage("chat");
    } catch (err) {
      console.error("Chat open error:", err);
    }
  };

  // ---------------- LOGIN ----------------
  const handleLogin = (loggedInUser) => {
    localStorage.setItem("rag_user", JSON.stringify(loggedInUser));
    setUser(loggedInUser);
    setPage("dashboard");
  };

  // ---------------- LOGOUT ----------------
  const handleLogout = () => {
    localStorage.removeItem("rag_user");
    setUser(null);
    setSelectedDocument(null);
    setChatId(null);
    setMessages([]);
    setPage("home");
  };

  // ---------------- ROUTES ----------------
  if (page === "home") {
    return <HomePage onNavigate={setPage} />;
  }

  if (page === "login" || page === "register") {
    return <LoginPage initialMode={page} onLogin={handleLogin} />;
  }

  if (page === "dashboard") {
    return (
      <DashboardPage
        user={user}
        onLogout={handleLogout}
        goToUpload={() => setPage("upload")}
        goToHistory={() => setPage("history")}
      />
    );
  }

  if (page === "upload") {
    return (
      <UploadPage
        user={user}
        goBack={() => setPage("dashboard")}
        goToHistory={() => setPage("history")}
        openDocumentChat={openDocumentChat}
      />
    );
  }

  if (page === "history") {
    return (
      <HistoryPage
        user={user}
        goBack={() => setPage("dashboard")}
        openDocumentChat={openDocumentChat}
      />
    );
  }

  if (page === "chat") {
    return (
      <ChatPage
        user={user}
        document={selectedDocument}
        chatId={chatId}
        messages={messages}
        setMessages={setMessages}
        goBack={() => setPage("history")}
      />
    );
  }

  return null;
}

export default App;