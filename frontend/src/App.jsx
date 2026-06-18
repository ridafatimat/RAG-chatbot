import { useEffect, useState } from "react";
import LoginPage from "./pages/LoginPage";
import DashboardPage from "./pages/DashboardPage";
import UploadPage from "./pages/UploadPage";
import HistoryPage from "./pages/HistoryPage";
import ChatPage from "./pages/ChatPage";

import "./App.css";

function App() {
  const [page, setPage] = useState("login");
  const [user, setUser] = useState(null);

  const [selectedDocument, setSelectedDocument] = useState(null);
  const [chatId, setChatId] = useState(null);
  const [messages, setMessages] = useState([]);

  // ---------------- LOGIN RESTORE ----------------
  useEffect(() => {
    const savedUser = localStorage.getItem("rag_user");

    if (savedUser) {
      setUser(JSON.parse(savedUser));
      setPage("dashboard");
    }
  }, []);

  // ---------------- OPEN CHAT ----------------
  const openDocumentChat = async (doc) => {
    setSelectedDocument(doc);
    setMessages([]);

    try {
      const res = await fetch(
        `http://127.0.0.1:8000/chat/session?user_id=${user._id}&document_id=${doc.file_id}`
      );

      const data = await res.json();
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
    setPage("login");
  };

  // ---------------- ROUTES ----------------
  if (page === "login") {
    return <LoginPage onLogin={handleLogin} goToRegister={() => setPage("register")} />;
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