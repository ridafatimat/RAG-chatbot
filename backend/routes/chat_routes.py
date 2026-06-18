from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
import os

from services.chroma_service import search_chunks
from groq import Groq

from services.mongo_service import (
    save_chat_message,
    get_or_create_chat_session,
    get_chat_messages
)

router = APIRouter()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))


class ChatRequest(BaseModel):
    question: str
    document_id: str
    user_id: str
    chat_id: Optional[str] = None


@router.post("/chat")
def chat(request: ChatRequest):
    try:
        question = request.question.strip()
        document_id = request.document_id
        user_id = request.user_id
        chat_id = request.chat_id

        if not chat_id:
            chat = get_or_create_chat_session(
                user_id=user_id,
                document_id=document_id,
                title=question[:40]
            )
            chat_id = str(chat["_id"])

        save_chat_message(chat_id=chat_id, role="user", message=question)

        relevant_chunks = search_chunks(document_id, question)

        if not relevant_chunks:
            context = "No relevant context found in document."
        else:
            context = "\n\n".join(relevant_chunks)

        prompt = f"""
You are a helpful AI assistant.

Rules:
- Answer ONLY using the provided context
- If context is empty, say you cannot find the answer in the document
- Keep answers simple and clear

Context:
{context}

Question:
{question}
"""

        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": prompt}]
        )

        answer = response.choices[0].message.content.strip()

        save_chat_message(chat_id=chat_id, role="assistant", message=answer)

        return {
            "chat_id": chat_id,
            "question": question,
            "answer": answer,
            "context_used": relevant_chunks
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Chat processing failed: {str(e)}")


# IMPORTANT: this static route MUST be registered before /chat/{chat_id}
@router.get("/chat/session")
def get_chat_session(user_id: str, document_id: str):
    chat = get_or_create_chat_session(user_id, document_id)
    return {"chat_id": str(chat["_id"])}


@router.get("/chat/{chat_id}")
def get_chat(chat_id: str):
    messages = get_chat_messages(chat_id)

    formatted = [
        {"role": m.get("role"), "message": m.get("content") or m.get("message")}
        for m in messages
    ]

    return {"chat_id": chat_id, "messages": formatted}


@router.get("/debug/{document_id}")
def debug(document_id: str):
    from services.chroma_service import debug_document_chunks
    return debug_document_chunks(document_id)