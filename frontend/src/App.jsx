import { useEffect, useState } from "react";

import LoginPage from "./pages/LoginPage";
import RegisterPage from "./RegisterPage";
import DashboardPage from "./pages/DashboardPage";
import UploadPage from "./pages/UploadPage";
import HistoryPage from "./pages/HistoryPage";
import ChatPage from "./pages/ChatPage";

import "./App.css";

const API_BASE_URL = "http://127.0.0.1:8000";

function App() {
  const [page, setPage] = useState("login");
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
        setPage("login");
      }
    } catch (error) {
      localStorage.removeItem("rag_user");
      setPage("login");
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

  // ---------------- LOGIN / REGISTER ----------------
  const handleLogin = (loggedInUser) => {
    localStorage.setItem("rag_user", JSON.stringify(loggedInUser));
    setUser(loggedInUser);
    setPage("dashboard");
  };

  const handleRegister = (registeredUser) => {
    localStorage.setItem("rag_user", JSON.stringify(registeredUser));
    setUser(registeredUser);
    setPage("dashboard");
  };

  // ---------------- LOGOUT ----------------
  const handleLogout = () => {
    localStorage.removeItem("rag_user");

    setUser(null);
    setSelectedDocument(null);
    setChatId(null);
    setMessages([]);
    setPage("login");
  };

  // ---------------- ROUTES ----------------
  if (page === "login") {
    return (
      <LoginPage
        onLogin={handleLogin}
        goToRegister={() => setPage("register")}
      />
    );
  }

  if (page === "register") {
    return (
      <RegisterPage
        onRegister={handleRegister}
        goToLogin={() => setPage("login")}
      />
    );
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