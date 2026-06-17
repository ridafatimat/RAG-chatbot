import { useEffect, useState } from "react";
import LoginPage from "./pages/LoginPage";
import RegisterPage from "./RegisterPage";
import DashboardPage from "./pages/DashboardPage";
import UploadPage from "./pages/UploadPage";
import HistoryPage from "./pages/HistoryPage";
import DocumentChatPage from "./pages/DocumentChatPage";
import "./App.css";

function App() {
  const [page, setPage] = useState("login");
  const [user, setUser] = useState(null);
  const [selectedDocument, setSelectedDocument] = useState(null);

  useEffect(() => {
    const savedUser = localStorage.getItem("rag_user");

    if (savedUser) {
      const parsedUser = JSON.parse(savedUser);
      setUser(parsedUser);
      setPage("dashboard");
    }
  }, []);

  const handleLogin = (loggedInUser) => {
    localStorage.setItem("rag_user", JSON.stringify(loggedInUser));
    setUser(loggedInUser);
    setPage("dashboard");
  };

  const handleLogout = () => {
    localStorage.removeItem("rag_user");
    setUser(null);
    setSelectedDocument(null);
    setPage("login");
  };

  const openDocumentChat = (document) => {
    setSelectedDocument(document);
    setPage("document-chat");
  };

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
        onRegister={handleLogin}
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

  if (page === "document-chat") {
    return (
      <DocumentChatPage
        document={selectedDocument}
        goBack={() => setPage("history")}
        goToDashboard={() => setPage("dashboard")}
      />
    );
  }

  return null;
}

export default App;