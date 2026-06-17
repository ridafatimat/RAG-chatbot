import { useState } from "react";

function RegisterPage({ onRegister, goToLogin }) {
  const [name, setName] = useState("Rida");
  const [email, setEmail] = useState("rida@test.com");
  const [password, setPassword] = useState("123456");
  const [message, setMessage] = useState("");
  const [loading, setLoading] = useState(false);

  const API_BASE_URL = "http://127.0.0.1:8000";

  const handleRegister = async () => {
    if (!name || !email || !password) {
      setMessage("Please fill all fields.");
      return;
    }

    try {
      setLoading(true);
      setMessage("");

      const response = await fetch(`${API_BASE_URL}/register`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          name,
          email,
          password,
        }),
      });

      const data = await response.json();

      if (!response.ok) {
        setMessage(data.detail || "Registration failed.");
        return;
      }

      onRegister(data.user);
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

        <h1>Create Account</h1>
        <p>Create an account to save your own document history.</p>

        <input
          type="text"
          placeholder="Name"
          value={name}
          onChange={(event) => setName(event.target.value)}
        />

        <input
          type="email"
          placeholder="Email"
          value={email}
          onChange={(event) => setEmail(event.target.value)}
        />

        <input
          type="password"
          placeholder="Password"
          value={password}
          onChange={(event) => setPassword(event.target.value)}
        />

        <button onClick={handleRegister} disabled={loading}>
          {loading ? "Creating..." : "Create Account"}
        </button>

        {message && <p className="auth-message">{message}</p>}

        <p className="auth-link">
          Already have an account? <span onClick={goToLogin}>Login</span>
        </p>
      </div>
    </div>
  );
}

export default RegisterPage;