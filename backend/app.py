import os
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from slowapi import _rate_limit_exceeded_handler

from services.rate_limiter import limiter

from routes.auth_routes import router as auth_router
from routes.upload_routes import router as upload_router

# chat_routes optional (safe import)
try:
    from routes.chat_routes import router as chat_router
except ImportError:
    chat_router = None


# -----------------------------
# ENVIRONMENT CONFIG
# -----------------------------
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")


# -----------------------------
# FASTAPI APP CONFIG
# -----------------------------
if ENVIRONMENT == "production":
    app = FastAPI(
        title="RAG Chatbot Backend",
        description="Backend API for the RAG chatbot project",
        version="1.0.0",
        docs_url=None,
        redoc_url=None,
        openapi_url=None,
    )
else:
    app = FastAPI(
        title="RAG Chatbot Backend",
        description="Backend API for the RAG chatbot project",
        version="1.0.0",
    )


# -----------------------------
# RATE LIMITER CONFIG
# -----------------------------
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)


# -----------------------------
# CORS CONFIG
# -----------------------------
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:5173")

allowed_origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    FRONTEND_URL,
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"],
)


# -----------------------------
# SECURITY HEADERS
# -----------------------------
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)

    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = (
        "camera=(), microphone=(), geolocation=(), payment=()"
    )
    response.headers["Cross-Origin-Opener-Policy"] = "same-origin"
    response.headers["Cross-Origin-Resource-Policy"] = "same-site"

    return response


# -----------------------------
# ROUTES
# -----------------------------
app.include_router(auth_router)
app.include_router(upload_router)

if chat_router:
    app.include_router(chat_router)


# -----------------------------
# BASIC ENDPOINTS
# -----------------------------
@app.get("/")
def home():
    return {
        "message": "RAG Chatbot Backend is running successfully"
    }


@app.get("/health")
def health_check():
    return {
        "status": "ok"
    }