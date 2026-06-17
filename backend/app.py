from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routes.upload_routes import router as upload_router
from routes.auth_routes import router as auth_router

try:
    from routes.chat_routes import router as chat_router
except ImportError:
    chat_router = None

app = FastAPI(
    title="RAG Chatbot Backend",
    description="Backend API for the RAG chatbot project",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(upload_router)

if chat_router:
    app.include_router(chat_router)


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