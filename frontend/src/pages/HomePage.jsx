import { useEffect, useRef } from "react";

function HomePage({ onNavigate }) {
  const featuresRef = useRef(null);
  const howItWorksRef = useRef(null);

  const scrollTo = (ref) => {
    ref.current?.scrollIntoView({ behavior: "smooth" });
  };

  // Push history state so browser back button returns to homepage
  useEffect(() => {
    window.history.pushState({ page: "home" }, "");

    const handlePopState = () => {
      onNavigate("home");
    };

    window.addEventListener("popstate", handlePopState);
    return () => window.removeEventListener("popstate", handlePopState);
  }, []);

  const navigateTo = (page) => {
    window.history.pushState({ page }, "");
    onNavigate(page);
  };

  useEffect(() => {
    const style = document.createElement("style");
    style.textContent = `
      * { margin: 0; padding: 0; box-sizing: border-box; }

      html, body {
        background: #0a0a0a;
        color: #ffffff;
        font-family: 'Inter', 'Segoe UI', sans-serif;
        overflow-x: hidden;
        overflow-y: auto;
        scroll-behavior: smooth;
        height: auto;
      }

      #root {
        overflow-y: auto;
        height: auto;
      }

      .hp-nav {
        position: sticky;
        top: 0;
        z-index: 100;
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 1rem 2.5rem;
        background: rgba(10, 10, 10, 0.85);
        backdrop-filter: blur(12px);
        border-bottom: 1px solid #1f1f1f;
      }

      .hp-nav-logo {
        font-size: 1.3rem;
        font-weight: 700;
        color: #d63b32;
        letter-spacing: -0.5px;
      }

      .hp-nav-links {
        display: flex;
        gap: 2rem;
        list-style: none;
      }

      .hp-nav-links li {
        font-size: 0.9rem;
        color: #aaa;
        cursor: pointer;
        transition: color 0.2s;
      }

      .hp-nav-links li:hover { color: #fff; }

      .hp-nav-btns {
        display: flex;
        gap: 0.75rem;
      }

      .hp-btn-outline {
        padding: 0.5rem 1.2rem;
        border: 1.5px solid #d63b32;
        background: transparent;
        color: #d63b32;
        border-radius: 8px;
        font-size: 0.875rem;
        font-weight: 500;
        cursor: pointer;
        transition: background 0.2s, color 0.2s;
      }

      .hp-btn-outline:hover {
        background: #d63b32;
        color: #000;
      }

      .hp-btn-solid {
        padding: 0.5rem 1.2rem;
        border: none;
        background: #d63b32;
        color: #000;
        border-radius: 8px;
        font-size: 0.875rem;
        font-weight: 600;
        cursor: pointer;
        transition: background 0.2s, transform 0.15s;
      }

      .hp-btn-solid:hover {
        background: #e05f00;
        transform: scale(1.03);
      }

      .hp-hero {
        min-height: 90vh;
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        text-align: center;
        padding: 4rem 2rem;
        position: relative;
        overflow: hidden;
      }

      .hp-hero::before {
        content: '';
        position: absolute;
        top: -100px;
        left: 50%;
        transform: translateX(-50%);
        width: 700px;
        height: 700px;
        background: radial-gradient(circle, rgba(255, 107, 0, 0.12) 0%, transparent 70%);
        pointer-events: none;
      }

      .hp-hero-badge {
        display: inline-block;
        background: rgba(255, 107, 0, 0.12);
        color: #d63b32;
        border: 1px solid rgba(255, 107, 0, 0.3);
        padding: 0.35rem 1rem;
        border-radius: 999px;
        font-size: 0.8rem;
        font-weight: 500;
        margin-bottom: 1.5rem;
        letter-spacing: 0.5px;
      }

      .hp-hero h1 {
        font-size: clamp(2.2rem, 5vw, 4rem);
        font-weight: 800;
        line-height: 1.15;
        letter-spacing: -1px;
        margin-bottom: 1.25rem;
        max-width: 780px;
      }

      .hp-hero h1 span { color: #d63b32; }

      .hp-hero p {
        font-size: 1.1rem;
        color: #888;
        max-width: 560px;
        line-height: 1.7;
        margin-bottom: 2.5rem;
      }

      .hp-hero-btns {
        display: flex;
        gap: 1rem;
        flex-wrap: wrap;
        justify-content: center;
      }

      .hp-btn-hero-solid {
        padding: 0.85rem 2rem;
        background: #d63b32;
        color: #000;
        border: none;
        border-radius: 10px;
        font-size: 1rem;
        font-weight: 700;
        cursor: pointer;
        transition: background 0.2s, transform 0.15s;
      }

      .hp-btn-hero-solid:hover {
        background: #e05f00;
        transform: translateY(-2px);
      }

      .hp-btn-hero-ghost {
        padding: 0.85rem 2rem;
        background: transparent;
        color: #ccc;
        border: 1.5px solid #333;
        border-radius: 10px;
        font-size: 1rem;
        font-weight: 500;
        cursor: pointer;
        transition: border-color 0.2s, color 0.2s;
      }

      .hp-btn-hero-ghost:hover {
        border-color: #d63b32;
        color: #d63b32;
      }

      .hp-section {
        padding: 5rem 2rem;
        max-width: 1100px;
        margin: 0 auto;
      }

      .hp-section-label {
        text-align: center;
        font-size: 0.8rem;
        font-weight: 600;
        color: #d63b32;
        text-transform: uppercase;
        letter-spacing: 1.5px;
        margin-bottom: 0.75rem;
      }

      .hp-section-title {
        text-align: center;
        font-size: clamp(1.6rem, 3vw, 2.2rem);
        font-weight: 700;
        margin-bottom: 0.75rem;
        letter-spacing: -0.5px;
      }

      .hp-section-sub {
        text-align: center;
        color: #666;
        font-size: 1rem;
        margin-bottom: 3rem;
        max-width: 500px;
        margin-left: auto;
        margin-right: auto;
      }

      .hp-features-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(230px, 1fr));
        gap: 1.25rem;
      }

      .hp-feature-card {
        background: #111;
        border: 1px solid #1f1f1f;
        border-radius: 14px;
        padding: 1.75rem;
        transition: border-color 0.25s, transform 0.2s;
      }

      .hp-feature-card:hover {
        border-color: rgba(255, 107, 0, 0.4);
        transform: translateY(-4px);
      }

      .hp-feature-icon {
        width: 44px;
        height: 44px;
        background: rgba(255, 107, 0, 0.1);
        border-radius: 10px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 1.3rem;
        margin-bottom: 1rem;
      }

      .hp-feature-card h3 {
        font-size: 1rem;
        font-weight: 600;
        margin-bottom: 0.5rem;
        color: #fff;
      }

      .hp-feature-card p {
        font-size: 0.875rem;
        color: #666;
        line-height: 1.6;
      }

      .hp-hiw-bg {
        background: #0d0d0d;
      }

      .hp-steps {
        display: flex;
        gap: 1rem;
        flex-wrap: wrap;
        justify-content: center;
      }

      .hp-step {
        flex: 1;
        min-width: 200px;
        max-width: 280px;
        text-align: center;
        padding: 1.5rem 1rem;
      }

      .hp-step-num {
        width: 48px;
        height: 48px;
        border-radius: 50%;
        background: #d63b32;
        color: #000;
        font-size: 1.1rem;
        font-weight: 800;
        display: flex;
        align-items: center;
        justify-content: center;
        margin: 0 auto 1rem;
      }

      .hp-step h3 {
        font-size: 1rem;
        font-weight: 600;
        margin-bottom: 0.5rem;
      }

      .hp-step p {
        font-size: 0.85rem;
        color: #666;
        line-height: 1.6;
      }

      .hp-cta {
        text-align: center;
        padding: 5rem 2rem;
        position: relative;
        overflow: hidden;
      }

      .hp-cta::before {
        content: '';
        position: absolute;
        top: 50%;
        left: 50%;
        transform: translate(-50%, -50%);
        width: 600px;
        height: 300px;
        background: radial-gradient(ellipse, rgba(255, 107, 0, 0.1) 0%, transparent 70%);
        pointer-events: none;
      }

      .hp-cta h2 {
        font-size: clamp(1.6rem, 3vw, 2.4rem);
        font-weight: 800;
        margin-bottom: 1rem;
        letter-spacing: -0.5px;
        position: relative;
      }

      .hp-cta p {
        color: #666;
        font-size: 1rem;
        margin-bottom: 2rem;
        position: relative;
      }

      .hp-footer {
        border-top: 1px solid #1a1a1a;
        padding: 2rem 2.5rem;
        display: flex;
        align-items: center;
        justify-content: space-between;
        flex-wrap: wrap;
        gap: 1rem;
      }

      .hp-footer-logo {
        font-size: 1.1rem;
        font-weight: 700;
        color: #d63b32;
      }

      .hp-footer p {
        font-size: 0.8rem;
        color: #444;
      }

      .hp-footer-links {
        display: flex;
        gap: 1.5rem;
      }

      .hp-footer-links span {
        font-size: 0.8rem;
        color: #444;
        cursor: pointer;
        transition: color 0.2s;
      }

      .hp-footer-links span:hover { color: #d63b32; }

      .hp-credits {
        border-top: 1px solid #1e1e1e;
        padding: 2.5rem 2.5rem;
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 3rem;
        flex-wrap: wrap;
        background: #080808;
      }

      .hp-credits-label {
        font-size: 0.75rem;
        color: #888;
        text-transform: uppercase;
        letter-spacing: 2px;
        font-weight: 600;
      }

      .hp-credit-person {
        display: flex;
        align-items: center;
        gap: 0.9rem;
      }

      .hp-credit-avatar {
        width: 42px;
        height: 42px;
        border-radius: 50%;
        background: rgba(255, 107, 0, 0.12);
        border: 2px solid rgba(255, 107, 0, 0.35);
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 0.85rem;
        font-weight: 700;
        color: #d63b32;
        flex-shrink: 0;
        transition: all 0.25s ease;
      }

      .hp-credit-person:hover .hp-credit-avatar {
        background: #d63b32;
        color: #000;
        transform: scale(1.06);
      }

      .hp-credit-info {
        display: flex;
        flex-direction: column;
        gap: 0.25rem;
      }

      .hp-credit-name {
        font-size: 0.95rem;
        font-weight: 600;
        color: #f0f0f0;
      }

      .hp-credit-email {
        font-size: 0.8rem;
        color: #888;
        text-decoration: none;
        transition: color 0.2s;
      }

      .hp-credit-email:hover { color: #d63b32; }

      .hp-credits-dot {
        width: 4px;
        height: 4px;
        border-radius: 50%;
        background: #2a2a2a;
      }

      @media (max-width: 768px) {
        .hp-credits {
          flex-direction: column;
          gap: 1.5rem;
          text-align: center;
        }
        .hp-credits-dot { display: none; }
        .hp-credit-person { justify-content: center; }
      }
    `;
    document.head.appendChild(style);
    return () => document.head.removeChild(style);
  }, []);

  return (
    <div style={{ overflowY: "auto", height: "100vh" }}>
      <nav className="hp-nav">
        <div className="hp-nav-logo">RAG Chatbot</div>
        <ul className="hp-nav-links">
          <li onClick={() => scrollTo(featuresRef)}>Features</li>
          <li onClick={() => scrollTo(howItWorksRef)}>How It Works</li>
        </ul>
        <div className="hp-nav-btns">
          <button className="hp-btn-outline" onClick={() => navigateTo("login")}>Login</button>
          <button className="hp-btn-solid" onClick={() => navigateTo("register")}>Create Account</button>
        </div>
      </nav>

      <section className="hp-hero">
        <div className="hp-hero-badge">AI-Powered Document Chat</div>
        <h1>Chat With Your Documents.<br /><span>Instantly.</span></h1>
        <p>
          Upload any PDF and ask questions in plain English.
          Get accurate, context-aware answers powered by RAG and LLMs, no hallucinations, just your data.
        </p>
        <div className="hp-hero-btns">
          <button className="hp-btn-hero-solid" onClick={() => navigateTo("register")}>
            Get Started Free
          </button>
          <button className="hp-btn-hero-ghost" onClick={() => scrollTo(howItWorksRef)}>
            See How It Works
          </button>
        </div>
      </section>

      <div ref={featuresRef}>
        <div className="hp-section">
          <div className="hp-section-label">Features</div>
          <h2 className="hp-section-title">Everything you need</h2>
          <p className="hp-section-sub">Built for speed, accuracy, and simplicity: from upload to answer in seconds.</p>
          <div className="hp-features-grid">
            {[
              { icon: "📄", title: "Upload PDFs", desc: "Drop any PDF and it's instantly processed, chunked, and indexed for search." },
              { icon: "💬", title: "Ask Questions", desc: "Type naturally. No special syntax required, just ask what you want to know." },
              { icon: "🤖", title: "AI-Powered Answers", desc: "Powered by Groq's LLaMA model with RAG for grounded, accurate responses." },
              { icon: "🕓", title: "Chat History", desc: "Every conversation is saved so you can revisit answers anytime." },
            ].map((f, i) => (
              <div className="hp-feature-card" key={i}>
                <div className="hp-feature-icon">{f.icon}</div>
                <h3>{f.title}</h3>
                <p>{f.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </div>

      <div className="hp-hiw-bg" ref={howItWorksRef}>
        <div className="hp-section">
          <div className="hp-section-label">How It Works</div>
          <h2 className="hp-section-title">Three steps to clarity</h2>
          <p className="hp-section-sub">No setup. No configuration. Just results.</p>
          <div className="hp-steps">
            {[
              { n: "1", title: "Upload your PDF", desc: "Select any document from your device. We handle text extraction and chunking automatically." },
              { n: "2", title: "Ask a question", desc: "Type your question in plain English, about anything in your document." },
              { n: "3", title: "Get instant answers", desc: "Our RAG pipeline finds the most relevant chunks and generates a precise answer." },
            ].map((s, i) => (
              <div className="hp-step" key={i}>
                <div className="hp-step-num">{s.n}</div>
                <h3>{s.title}</h3>
                <p>{s.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </div>

      <section className="hp-cta">
        <h2>Start chatting with your docs today</h2>
        <p>Create a free account and upload your first PDF in under a minute.</p>
        <button className="hp-btn-hero-solid" onClick={() => navigateTo("register")}>
          Create Account
        </button>
      </section>

      <footer className="hp-footer">
        <div className="hp-footer-logo">RAG Chatbot</div>
        <p>Built with React, Flask, ChromaDB & Groq</p>
        <div className="hp-footer-links">
          <span onClick={() => navigateTo("login")}>Login</span>
          <span onClick={() => navigateTo("register")}>Sign Up</span>
        </div>
      </footer>

      <div className="hp-credits">
        <span className="hp-credits-label">Designed & Developed by</span>
        <div className="hp-credits-dot" />
        <div className="hp-credit-person">
          <div className="hp-credit-avatar">EJ</div>
          <div className="hp-credit-info">
            <span className="hp-credit-name">Easha Javed</span>
            <a className="hp-credit-email" href="mailto:eashajaved896@gmail.com">eashajaved896@gmail.com</a>
          </div>
        </div>
        <div className="hp-credits-dot" />
        <div className="hp-credit-person">
          <div className="hp-credit-avatar">RFT</div>
          <div className="hp-credit-info">
            <span className="hp-credit-name">Rida Fatima Tanvir</span>
            <a className="hp-credit-email" href="mailto:ridafatimat@gmail.com">ridafatimat@gmail.com</a>
          </div>
        </div>
      </div>
    </div>
  );
}

export default HomePage;