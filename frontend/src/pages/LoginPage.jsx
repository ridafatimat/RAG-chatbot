import { useState, useEffect, useRef } from "react";

function LoginPage({ onLogin }) {
  const [mode, setMode] = useState("login");
  // login | register | otp | forgot

  const [otpMode, setOtpMode] = useState("register");
  // register | reset

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

  const API_BASE_URL =
    import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

  // ---------------- RESET ----------------
  const resetAll = () => {
    setName("");
    setEmail("");
    setPassword("");
    setConfirmPassword("");
    setOtp("");
    setNewPassword("");
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

  const goToForgot = () => {
    setMode("forgot");
    resetAll();
  };

  // ---------------- TIMER ----------------
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
    setLoading(true);
    setMessage("Logging in...");

    try {
      const res = await fetch(`${API_BASE_URL}/login`, {
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

      const data = await res.json();

      if (!res.ok) {
        setMessage(data?.detail || "Login failed");
        return;
      }

      localStorage.setItem("rag_user", JSON.stringify(data.user));

      setMessage("Login successful!");
      onLogin?.(data.user);
    } catch {
      setMessage("Server error");
    } finally {
      setLoading(false);
    }
  };

  // ---------------- REGISTER ----------------
  const handleRegister = async () => {
    if (password !== confirmPassword) {
      setMessage("Passwords do not match");
      return;
    }

    setMode("otp");
    setOtpMode("register");

    setLoading(true);
    setMessage("Sending verification code...");

    try {
      const res = await fetch(`${API_BASE_URL}/register`, {
        method: "POST",
        credentials: "include",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          name,
          email: email.trim().toLowerCase(),
          password,
        }),
      });

      const data = await res.json();

      if (!res.ok) {
        setMessage(data?.detail || "Registration failed");
        setMode("register");
        return;
      }

      setMessage("Verification code sent to your email");
      startTimer();
    } catch {
      setMessage("Server error");
      setMode("register");
    } finally {
      setLoading(false);
    }
  };

  // ---------------- FORGOT PASSWORD ----------------
  const handleForgotPassword = async () => {
    setLoading(true);
    setMessage("Sending reset code...");

    try {
      const res = await fetch(`${API_BASE_URL}/forgot-password`, {
        method: "POST",
        credentials: "include",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          email: email.trim().toLowerCase(),
        }),
      });

      const data = await res.json();

      if (!res.ok) {
        setMessage(data?.detail || "Failed");
        return;
      }

      setOtpMode("reset");
      setMode("otp");

      setMessage("Password reset code sent to your email");
      startTimer();
    } catch {
      setMessage("Server error");
    } finally {
      setLoading(false);
    }
  };

  // ---------------- VERIFY OTP (REGISTER + RESET) ----------------
  const handleVerifyOTP = async () => {
    setLoading(true);
    setMessage("Verifying...");

    try {
      const endpoint =
        otpMode === "reset"
          ? "/verify-reset-password"
          : "/verify-email";

      const body =
        otpMode === "reset"
          ? {
              email: email.trim().toLowerCase(),
              otp,
              new_password: newPassword,
            }
          : {
              email: email.trim().toLowerCase(),
              otp,
            };

      const res = await fetch(`${API_BASE_URL}${endpoint}`, {
        method: "POST",
        credentials: "include",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(body),
      });

      const data = await res.json();

      if (!res.ok) {
        setMessage(data?.detail || "Failed");
        return;
      }

      if (otpMode === "reset") {
        setMessage("Password reset successful! Please login.");
        setMode("login");
      } else {
        // Security: token is stored in httpOnly cookie by backend.
        // Do not store access_token in localStorage.
        localStorage.setItem("rag_user", JSON.stringify(data.user));
        setMessage("Account verified!");
        onLogin?.(data.user);
      }
    } catch {
      setMessage("Server error");
    } finally {
      setLoading(false);
    }
  };

  // ---------------- RESEND OTP ----------------
  const resendOTP = async () => {
    if (!canResend) return;

    setLoading(true);
    setMessage("Resending code...");

    try {
      const res = await fetch(`${API_BASE_URL}/resend-otp`, {
        method: "POST",
        credentials: "include",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          email: email.trim().toLowerCase(),
        }),
      });

      const data = await res.json();

      if (res.ok) {
        setMessage("Code resent successfully");
        startTimer();
      } else {
        setMessage(data?.detail || "Failed to resend");
      }
    } catch {
      setMessage("Server error");
    } finally {
      setLoading(false);
    }
  };

  // ---------------- UI ----------------
  return (
    <div className="auth-page">
      <div className="auth-card">
        <h1>RAG Assistant</h1>

        {/* LOGIN */}
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
              Login
            </button>

            <p
              onClick={goToRegister}
              style={{
                cursor: "pointer",
                color: "orange",
                fontWeight: "bold",
              }}
            >
              Create Account
            </p>

            <p
              onClick={goToForgot}
              style={{
                cursor: "pointer",
                color: "orange",
                fontWeight: "bold",
              }}
            >
              Forgot Password?
            </p>
          </>
        )}

        {/* REGISTER */}
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
              Create Account
            </button>

            <p
              onClick={goToLogin}
              style={{
                cursor: "pointer",
                color: "orange",
                fontWeight: "bold",
              }}
            >
              Back to Login
            </p>
          </>
        )}

        {/* OTP SCREEN (REGISTER + RESET) */}
        {mode === "otp" && (
          <>
            <input
              placeholder={
                otpMode === "reset"
                  ? "Enter password reset code"
                  : "Enter verification code"
              }
              value={otp}
              onChange={(e) => setOtp(e.target.value)}
            />

            {otpMode === "reset" && (
              <input
                type="password"
                placeholder="New Password"
                value={newPassword}
                onChange={(e) => setNewPassword(e.target.value)}
              />
            )}

            <p style={{ fontSize: "12px", color: "gray" }}>
              {otpMode === "reset"
                ? "Password reset code valid for 5 minutes"
                : "Verification code valid for 5 minutes"}
            </p>

            <button onClick={handleVerifyOTP} disabled={loading}>
              {otpMode === "reset" ? "Reset Password" : "Verify Account"}
            </button>

            <button onClick={resendOTP} disabled={!canResend || loading}>
              Resend Code
            </button>

            <p>
              {canResend
                ? "You can resend now"
                : `Resend available in ${timer}s`}
            </p>

            <p
              onClick={goToLogin}
              style={{
                cursor: "pointer",
                color: "orange",
                fontWeight: "bold",
              }}
            >
              Back to Login
            </p>
          </>
        )}

        {/* FORGOT PASSWORD */}
        {mode === "forgot" && (
          <>
            <input
              placeholder="Enter email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
            />

            <button onClick={handleForgotPassword} disabled={loading}>
              Send Reset Code
            </button>

            <p
              onClick={goToLogin}
              style={{
                cursor: "pointer",
                color: "orange",
                fontWeight: "bold",
              }}
            >
              Back to Login
            </p>
          </>
        )}

        {message && <p>{message}</p>}
      </div>
    </div>
  );
}

export default LoginPage;