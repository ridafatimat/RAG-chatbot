import { useState } from "react";

function LoginPage({ onLogin, goToRegister }) {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");

  const [message, setMessage] = useState("");
  const [loading, setLoading] = useState(false);

  const API_BASE_URL = "http://localhost:8000";
  const handleLogin = async () => {
    if (!email.trim() || !password.trim()) {
      setMessage("Please enter email and password.");
      return;
    }

    try {
      setLoading(true);
      setMessage("");

      const response = await fetch(`${API_BASE_URL}/login`, {
        method: "POST",
        credentials: "include",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          email: email.trim().toLowerCase(),
          password,
        }),
      });

      const data = await response.json();

      if (!response.ok) {
        setMessage(data.detail || "Login failed.");
        return;
      }

      localStorage.setItem("rag_user", JSON.stringify(data.user));

      onLogin(data.user);
    } catch (error) {
      setMessage("Could not connect to backend.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="auth-page">
      <div className="auth-card">
        <div className="brand-icon auth-icon">▣</div>

        <h1>RAG Assistant</h1>
        <p>Login to access your personal document workspace.</p>

        <input
          type="email"
          placeholder="Enter your email"
          value={email}
          onChange={(event) => setEmail(event.target.value)}
        />

        <input
          type="password"
          placeholder="Enter your password"
          value={password}
          onChange={(event) => setPassword(event.target.value)}
          onKeyDown={(event) => event.key === "Enter" && handleLogin()}
        />

        <button onClick={handleLogin} disabled={loading}>
          {loading ? "Logging in..." : "Login"}
        </button>

        {message && <p className="auth-message">{message}</p>}

        <p className="auth-link">
          Don't have an account?{" "}
          <span onClick={goToRegister}>Create account</span>
        </p>
      </div>
    </div>
  );
}

export default LoginPage;