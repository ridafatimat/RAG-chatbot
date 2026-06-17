from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
import os

from services.chroma_service import search_chunks
from groq import Groq

# MongoDB imports (NEW)
from services.mongo_service import (
    save_chat_message,
    get_or_create_chat_session
)

router = APIRouter()

# Groq client
client = Groq(api_key=os.getenv("GROQ_API_KEY"))


# -----------------------------
# REQUEST MODEL (UPDATED)
# -----------------------------
class ChatRequest(BaseModel):
    question: str
    document_id: str
    user_id: str
    chat_id: Optional[str] = None   


# -----------------------------
# MAIN CHAT ROUTE (RAG + MEMORY)
# -----------------------------
@router.post("/chat")
def chat(request: ChatRequest):

    try:
        question = request.question
        document_id = request.document_id
        user_id = request.user_id
        chat_id = request.chat_id

        # Step 1: Create new chat session if not exists
        if not chat_id:
            title = question[:40]

            chat_id = get_or_create_chat_session(
                user_id=user_id,
                document_id=document_id,
                title=title
            )

        # Step 2: Save user message
        save_chat_message(
            chat_id=chat_id,
            role="user",
            message=question
        )

        # Step 3: Retrieve chunks
        relevant_chunks = search_chunks(question, document_id)
        context = "\n\n".join(relevant_chunks)

        # Step 4: Prompt
        prompt = f"""
You are a helpful AI assistant.
Answer ONLY using the context below.

Context:
{context}

Question:
{question}

Answer in a clear and simple way.
"""

        # Step 5: Groq call
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": prompt}]
        )

        answer = response.choices[0].message.content

        # Step 6: Save bot message
        save_chat_message(
            chat_id=chat_id,
            role="assistant",
            message=answer
        )

        return {
            "chat_id": chat_id,
            "question": question,
            "answer": answer,
            "context_used": relevant_chunks
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
# -----------------------------
# OPTIONAL: GET CHAT HISTORY
# -----------------------------
from services.mongo_service import get_chat_messages


@router.get("/chat/{chat_id}")
def get_chat(chat_id: str):
    return {
        "chat_id": chat_id,
        "messages": get_chat_messages(chat_id)
    }
@router.get("/debug/{document_id}")
def debug(document_id: str):
    from services.chroma_service import debug_document_chunks

    return debug_document_chunks(document_id)