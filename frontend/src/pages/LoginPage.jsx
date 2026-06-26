import { useState, useEffect, useRef } from "react";

function LoginPage({ onLogin, initialMode = "login" }) {
  const [mode, setMode] = useState(initialMode);
  const [otpMode, setOtpMode] = useState("register");

  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");

  const [otp, setOtp] = useState("");
  const [newPassword, setNewPassword] = useState("");

  const [message, setMessage] = useState("");
  const [loading, setLoading] = useState(false);

  const [timer, setTimer] = useState(60);
  const [canResend, setCanResend] = useState(false);

  const intervalRef = useRef(null);

  const API_BASE_URL = "http://127.0.0.1:8000";

  const resetAll = () => {
    setName(""); setEmail(""); setPassword("");
    setConfirmPassword(""); setOtp(""); setNewPassword(""); setMessage("");
  };

  const goToLogin = () => { setMode("login"); resetAll(); };
  const goToRegister = () => { setMode("register"); resetAll(); };
  const goToForgot = () => { setMode("forgot"); resetAll(); };

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
    return () => { if (intervalRef.current) clearInterval(intervalRef.current); };
  }, [mode]);

  const handleLogin = async () => {
    setLoading(true); setMessage("Logging in...");
    try {
      const res = await fetch(`${API_BASE_URL}/login`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email: email.trim().toLowerCase(), password }),
      });
      const data = await res.json();
      if (!res.ok) { setMessage(data?.detail || "Login failed"); return; }
      localStorage.setItem("rag_token", data.access_token);
      localStorage.setItem("rag_user", JSON.stringify(data.user));
      setMessage("Login successful!");
      onLogin?.(data.user);
    } catch { setMessage("Server error"); }
    finally { setLoading(false); }
  };

  const handleRegister = async () => {
    if (password !== confirmPassword) { setMessage("Passwords do not match"); return; }
    setMode("otp"); setOtpMode("register");
    setLoading(true); setMessage("Sending verification code...");
    try {
      const res = await fetch(`${API_BASE_URL}/register`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name, email: email.trim().toLowerCase(), password }),
      });
      const data = await res.json();
      if (!res.ok) { setMessage(data?.detail || "Registration failed"); setMode("register"); return; }
      setMessage("Verification code sent to your email");
      startTimer();
    } catch { setMessage("Server error"); setMode("register"); }
    finally { setLoading(false); }
  };

  const handleForgotPassword = async () => {
    setLoading(true); setMessage("Sending reset code...");
    try {
      const res = await fetch(`${API_BASE_URL}/forgot-password`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email: email.trim().toLowerCase() }),
      });
      const data = await res.json();
      if (!res.ok) { setMessage(data?.detail || "Failed"); return; }
      setOtpMode("reset"); setMode("otp");
      setMessage("Password reset code sent to your email");
      startTimer();
    } catch { setMessage("Server error"); }
    finally { setLoading(false); }
  };

  const handleVerifyOTP = async () => {
    setLoading(true); setMessage("Verifying...");
    try {
      const endpoint = otpMode === "reset" ? "/verify-reset-password" : "/verify-email";
      const body = otpMode === "reset"
        ? { email: email.trim().toLowerCase(), otp, new_password: newPassword }
        : { email: email.trim().toLowerCase(), otp };
      const res = await fetch(`${API_BASE_URL}${endpoint}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      });
      const data = await res.json();
      if (!res.ok) { setMessage(data?.detail || "Failed"); return; }
      if (otpMode === "reset") {
        setMessage("Password reset successful!"); setMode("login");
      } else {
        localStorage.setItem("rag_token", data.access_token);
        localStorage.setItem("rag_user", JSON.stringify(data.user));
        setMessage("Account verified!");
        onLogin?.(data.user);
      }
    } catch { setMessage("Server error"); }
    finally { setLoading(false); }
  };

  const resendOTP = async () => {
    if (!canResend) return;
    setLoading(true); setMessage("Resending code...");
    try {
      const res = await fetch(`${API_BASE_URL}/resend-otp`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email: email.trim().toLowerCase() }),
      });
      const data = await res.json();
      if (res.ok) { setMessage("Code resent successfully"); startTimer(); }
      else { setMessage(data?.detail || "Failed to resend"); }
    } catch { setMessage("Server error"); }
    finally { setLoading(false); }
  };

  const styles = {
    page: {
      minHeight: "100vh",
      background: "#0a0a0a",
      display: "flex",
      alignItems: "center",
      justifyContent: "center",
      fontFamily: "'Inter', 'Segoe UI', sans-serif",
      padding: "1.5rem",
      position: "relative",
      overflow: "hidden",
    },
    glow: {
      position: "absolute",
      top: "50%",
      left: "50%",
      transform: "translate(-50%, -60%)",
      width: "600px",
      height: "600px",
      background: "radial-gradient(circle, rgba(255,107,0,0.08) 0%, transparent 70%)",
      pointerEvents: "none",
    },
    card: {
      background: "#111",
      border: "1px solid #222",
      borderRadius: "20px",
      padding: "2.5rem",
      width: "100%",
      maxWidth: "420px",
      position: "relative",
      zIndex: 1,
    },
    logoRow: {
      display: "flex",
      alignItems: "center",
      gap: "0.5rem",
      marginBottom: "2rem",
    },
    logoDot: {
      width: "28px",
      height: "28px",
      background: "#ff6b00",
      borderRadius: "8px",
      display: "flex",
      alignItems: "center",
      justifyContent: "center",
      fontSize: "0.75rem",
      fontWeight: "800",
      color: "#000",
    },
    logoText: {
      fontSize: "1rem",
      fontWeight: "700",
      color: "#fff",
      letterSpacing: "-0.3px",
    },
    heading: {
      fontSize: "1.6rem",
      fontWeight: "800",
      color: "#fff",
      marginBottom: "0.4rem",
      letterSpacing: "-0.5px",
    },
    subheading: {
      fontSize: "0.875rem",
      color: "#555",
      marginBottom: "2rem",
    },
    label: {
      display: "block",
      fontSize: "0.8rem",
      fontWeight: "500",
      color: "#888",
      marginBottom: "0.4rem",
      marginTop: "1rem",
    },
    input: {
      width: "100%",
      padding: "0.75rem 1rem",
      background: "#0a0a0a",
      border: "1px solid #2a2a2a",
      borderRadius: "10px",
      color: "#fff",
      fontSize: "0.9rem",
      outline: "none",
      transition: "border-color 0.2s",
      boxSizing: "border-box",
    },
    btn: {
      width: "100%",
      padding: "0.85rem",
      background: "#ff6b00",
      color: "#000",
      border: "none",
      borderRadius: "10px",
      fontSize: "0.95rem",
      fontWeight: "700",
      cursor: "pointer",
      marginTop: "1.5rem",
      transition: "background 0.2s, transform 0.15s",
    },
    btnSecondary: {
      width: "100%",
      padding: "0.75rem",
      background: "transparent",
      color: "#555",
      border: "1px solid #222",
      borderRadius: "10px",
      fontSize: "0.875rem",
      fontWeight: "500",
      cursor: "pointer",
      marginTop: "0.75rem",
      transition: "border-color 0.2s, color 0.2s",
    },
    link: {
      display: "block",
      textAlign: "center",
      marginTop: "1.25rem",
      fontSize: "0.85rem",
      color: "#ff6b00",
      cursor: "pointer",
      fontWeight: "500",
    },
    divider: {
      borderTop: "1px solid #1e1e1e",
      margin: "1.5rem 0",
    },
    msgSuccess: {
      marginTop: "1rem",
      padding: "0.75rem 1rem",
      background: "rgba(255,107,0,0.08)",
      border: "1px solid rgba(255,107,0,0.2)",
      borderRadius: "8px",
      color: "#ff6b00",
      fontSize: "0.85rem",
      textAlign: "center",
    },
    msgError: {
      marginTop: "1rem",
      padding: "0.75rem 1rem",
      background: "rgba(255,60,60,0.08)",
      border: "1px solid rgba(255,60,60,0.2)",
      borderRadius: "8px",
      color: "#ff6060",
      fontSize: "0.85rem",
      textAlign: "center",
    },
    timerRow: {
      display: "flex",
      alignItems: "center",
      justifyContent: "space-between",
      marginTop: "0.75rem",
    },
    timerText: {
      fontSize: "0.8rem",
      color: "#444",
    },
    otpNote: {
      fontSize: "0.78rem",
      color: "#444",
      marginTop: "0.5rem",
    },
  };

  const isError = message && (
    message.toLowerCase().includes("fail") ||
    message.toLowerCase().includes("error") ||
    message.toLowerCase().includes("match") ||
    message.toLowerCase().includes("invalid") ||
    message.toLowerCase().includes("wrong")
  );

  return (
    <div style={styles.page}>
      <div style={styles.glow} />
      <div style={styles.card}>

        {/* LOGO */}
        <div style={styles.logoRow}>
          <div style={styles.logoDot}>R</div>
          <span style={styles.logoText}>RAG Assistant</span>
        </div>

        {/* LOGIN */}
        {mode === "login" && (
          <>
            <h2 style={styles.heading}>Welcome back</h2>
            <p style={styles.subheading}>Sign in to your account to continue</p>

            <label style={styles.label}>Email</label>
            <input
              style={styles.input}
              placeholder="you@example.com"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
            />

            <label style={styles.label}>Password</label>
            <input
              style={styles.input}
              type="password"
              placeholder="••••••••"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
            />

            <div style={{ textAlign: "right", marginTop: "0.5rem" }}>
              <span onClick={goToForgot} style={{ fontSize: "0.8rem", color: "#ff6b00", cursor: "pointer" }}>
                Forgot password?
              </span>
            </div>

            <button
              style={styles.btn}
              onClick={handleLogin}
              disabled={loading}
            >
              {loading ? "Signing in..." : "Sign In"}
            </button>

            <div style={styles.divider} />

            <p style={{ textAlign: "center", fontSize: "0.85rem", color: "#555" }}>
              Don't have an account?{" "}
              <span onClick={goToRegister} style={{ color: "#ff6b00", cursor: "pointer", fontWeight: "600" }}>
                Create one
              </span>
            </p>
          </>
        )}

        {/* REGISTER */}
        {mode === "register" && (
          <>
            <h2 style={styles.heading}>Create account</h2>
            <p style={styles.subheading}>Start chatting with your documents today</p>

            <label style={styles.label}>Full Name</label>
            <input style={styles.input} placeholder="Easha Javed" value={name} onChange={(e) => setName(e.target.value)} />

            <label style={styles.label}>Email</label>
            <input style={styles.input} placeholder="you@example.com" value={email} onChange={(e) => setEmail(e.target.value)} />

            <label style={styles.label}>Password</label>
            <input style={styles.input} type="password" placeholder="••••••••" value={password} onChange={(e) => setPassword(e.target.value)} />

            <label style={styles.label}>Confirm Password</label>
            <input style={styles.input} type="password" placeholder="••••••••" value={confirmPassword} onChange={(e) => setConfirmPassword(e.target.value)} />

            <button style={styles.btn} onClick={handleRegister} disabled={loading}>
              {loading ? "Creating account..." : "Create Account"}
            </button>

            <div style={styles.divider} />

            <p style={{ textAlign: "center", fontSize: "0.85rem", color: "#555" }}>
              Already have an account?{" "}
              <span onClick={goToLogin} style={{ color: "#ff6b00", cursor: "pointer", fontWeight: "600" }}>
                Sign in
              </span>
            </p>
          </>
        )}

        {/* OTP */}
        {mode === "otp" && (
          <>
            <h2 style={styles.heading}>
              {otpMode === "reset" ? "Reset password" : "Verify email"}
            </h2>
            <p style={styles.subheading}>
              {otpMode === "reset"
                ? "Enter the code sent to your email and set a new password"
                : `We sent a verification code to ${email}`}
            </p>

            <label style={styles.label}>Verification Code</label>
            <input
              style={styles.input}
              placeholder="Enter 6-digit code"
              value={otp}
              onChange={(e) => setOtp(e.target.value)}
            />

            {otpMode === "reset" && (
              <>
                <label style={styles.label}>New Password</label>
                <input
                  style={styles.input}
                  type="password"
                  placeholder="••••••••"
                  value={newPassword}
                  onChange={(e) => setNewPassword(e.target.value)}
                />
              </>
            )}

            <p style={styles.otpNote}>Code is valid for 5 minutes</p>

            <button style={styles.btn} onClick={handleVerifyOTP} disabled={loading}>
              {loading ? "Verifying..." : otpMode === "reset" ? "Reset Password" : "Verify Account"}
            </button>

            <div style={styles.timerRow}>
              <span style={styles.timerText}>
                {canResend ? "Didn't receive it?" : `Resend available in ${timer}s`}
              </span>
              <span
                onClick={resendOTP}
                style={{
                  fontSize: "0.8rem",
                  color: canResend ? "#ff6b00" : "#333",
                  cursor: canResend ? "pointer" : "default",
                  fontWeight: "500",
                }}
              >
                Resend code
              </span>
            </div>
          </>
        )}

        {/* FORGOT PASSWORD */}
        {mode === "forgot" && (
          <>
            <h2 style={styles.heading}>Forgot password?</h2>
            <p style={styles.subheading}>Enter your email and we'll send you a reset code</p>

            <label style={styles.label}>Email</label>
            <input
              style={styles.input}
              placeholder="you@example.com"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
            />

            <button style={styles.btn} onClick={handleForgotPassword} disabled={loading}>
              {loading ? "Sending..." : "Send Reset Code"}
            </button>

            <span onClick={goToLogin} style={styles.link}>← Back to sign in</span>
          </>
        )}

        {message && (
          <div style={isError ? styles.msgError : styles.msgSuccess}>
            {message}
          </div>
        )}

      </div>
    </div>
  );
}

export default LoginPage;