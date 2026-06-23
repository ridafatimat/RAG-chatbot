import { useState, useEffect, useRef } from "react";

function LoginPage({ onLogin }) {
  const [mode, setMode] = useState("login"); // login | register | otp

  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [otp, setOtp] = useState("");

  const [message, setMessage] = useState("");
  const [loading, setLoading] = useState(false);

  const [timer, setTimer] = useState(60);
  const [canResend, setCanResend] = useState(false);

  const intervalRef = useRef(null);

  const API_BASE_URL = "http://127.0.0.1:8000";

  // ---------------- RESET ----------------
  const resetAll = () => {
    setName("");
    setEmail("");
    setPassword("");
    setConfirmPassword("");
    setOtp("");
    setMessage("");
  };

  const goToLogin = () => {
    setMode("login");
    resetAll();
  };

  const goToRegister = () => {
    setMode("register");
    resetAll();
  };

  const goToOTP = () => {
    setMode("otp");
    setOtp("");
    setMessage("");
  };

  // ---------------- TIMER (FIXED) ----------------
  const startTimer = () => {
    if (intervalRef.current) clearInterval(intervalRef.current);

    setTimer(60);
    setCanResend(false);

    intervalRef.current = setInterval(() => {
      setTimer((prev) => {
        if (prev <= 1) {
          clearInterval(intervalRef.current);
          intervalRef.current = null;
          setCanResend(true);
          return 0;
        }
        return prev - 1;
      });
    }, 1000);
  };

  useEffect(() => {
    if (mode === "otp") startTimer();

    return () => {
      if (intervalRef.current) clearInterval(intervalRef.current);
    };
  }, [mode]);

  // ---------------- LOGIN ----------------
  const handleLogin = async () => {
    if (!email || !password) {
      setMessage("Enter email & password");
      return;
    }

    setLoading(true);
    setMessage("Logging in...");

    try {
      const res = await fetch(`${API_BASE_URL}/login`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          email: email.trim().toLowerCase(),
          password,
        }),
      });

      const data = await res.json();

      if (!res.ok) {
        setMessage(data?.detail || "Login failed");
        return;
      }

      setMessage("Login successful!");

      localStorage.setItem("rag_token", data.access_token);
      localStorage.setItem("rag_user", JSON.stringify(data.user));

      onLogin?.(data.user);
    } catch {
      setMessage("Server error");
    } finally {
      setLoading(false);
    }
  };

  // ---------------- REGISTER (IMPROVED UX) ----------------
  const handleRegister = async () => {
    if (!name || !email || !password || !confirmPassword) {
      setMessage("Fill all fields");
      return;
    }

    if (password !== confirmPassword) {
      setMessage("Passwords do not match");
      return;
    }

    // 🔥 instant UX change
    setMode("otp");
    setLoading(true);
    setMessage("Sending OTP...");

    try {
      const res = await fetch(`${API_BASE_URL}/register`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          name,
          email: email.trim().toLowerCase(),
          password,
        }),
      });

      const data = await res.json();

      if (!res.ok) {
        setMessage(data?.detail || "Registration failed");

        // rollback UX if failed
        setMode("register");
        return;
      }

      setMessage("OTP sent! Check inbox + spam folder.");

    } catch {
      setMessage("Server error");
      setMode("register");
    } finally {
      setLoading(false);
    }
  };

  // ---------------- VERIFY OTP ----------------
  const handleVerifyOTP = async () => {
    if (!otp) {
      setMessage("Enter OTP");
      return;
    }

    setLoading(true);
    setMessage("Verifying OTP...");

    try {
      const res = await fetch(`${API_BASE_URL}/verify-email`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          email: email.trim().toLowerCase(),
          otp,
        }),
      });

      const data = await res.json();

      if (!res.ok) {
        setMessage(data?.detail || "OTP failed");
        return;
      }

      localStorage.setItem("rag_token", data.access_token);
      localStorage.setItem("rag_user", JSON.stringify(data.user));

      setMessage("Account verified!");

      onLogin?.(data.user);
    } catch {
      setMessage("Server error");
    } finally {
      setLoading(false);
    }
  };

  // ---------------- RESEND OTP (FIXED FULL FLOW) ----------------
  const resendOTP = async () => {
    if (!canResend) return;

    setLoading(true);
    setMessage("Resending OTP...");

    try {
      const res = await fetch(`${API_BASE_URL}/resend-otp`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          email: email.trim().toLowerCase(),
        }),
      });

      const data = await res.json();

      if (res.ok) {
        setMessage("OTP resent successfully!");
        startTimer(); // 🔥 IMPORTANT FIX
      } else {
        setMessage(data?.detail || "Failed to resend OTP");
      }
    } catch {
      setMessage("Failed to resend OTP");
    } finally {
      setLoading(false);
    }
  };

  // ---------------- UI ----------------
  return (
    <div className="auth-page">
      <div className="auth-card">

        <h1>RAG Assistant</h1>

        {/* ---------------- LOGIN ---------------- */}
        {mode === "login" && (
          <>
            <input
              placeholder="Email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
            />

            <input
              type="password"
              placeholder="Password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
            />

            <button onClick={handleLogin} disabled={loading}>
              {loading ? "Processing..." : "Login"}
            </button>

            <p>
              No account?{" "}
              <span
                onClick={goToRegister}
                style={{ color: "orange", fontWeight: "bold", cursor: "pointer" }}
              >
                Create Account
              </span>
            </p>
          </>
        )}

        {/* ---------------- REGISTER ---------------- */}
        {mode === "register" && (
          <>
            <input
              placeholder="Name"
              value={name}
              onChange={(e) => setName(e.target.value)}
            />

            <input
              placeholder="Email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
            />

            <input
              type="password"
              placeholder="Password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
            />

            <input
              type="password"
              placeholder="Confirm Password"
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
            />

            <button onClick={handleRegister} disabled={loading}>
              {loading ? "Sending OTP..." : "Create Account"}
            </button>

            <p>
              Already have account?{" "}
              <span
                onClick={goToLogin}
                style={{ color: "orange", fontWeight: "bold", cursor: "pointer" }}
              >
                Login
              </span>
            </p>
          </>
        )}

        {/* ---------------- OTP ---------------- */}
        {mode === "otp" && (
          <>
            <input
              placeholder="Enter OTP"
              value={otp}
              onChange={(e) => setOtp(e.target.value)}
            />

            <p style={{ fontSize: "12px", color: "gray" }}>
              Check Inbox + Spam folder. OTP valid for 5 minutes.
            </p>

            <button onClick={handleVerifyOTP} disabled={loading}>
              {loading ? "Verifying..." : "Verify OTP"}
            </button>

            <button
              onClick={resendOTP}
              disabled={!canResend || loading}
              style={{
                opacity: canResend ? 1 : 0.5,
                cursor: canResend ? "pointer" : "not-allowed",
              }}
            >
              Resend OTP
            </button>

            <p style={{ fontSize: "12px" }}>
              {canResend
                ? "You can resend OTP now"
                : `Resend available in ${timer}s`}
            </p>
          </>
        )}

        {/* ---------------- MESSAGE ---------------- */}
        {message && <p>{message}</p>}

      </div>
    </div>
  );
}

export default LoginPage;