from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

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