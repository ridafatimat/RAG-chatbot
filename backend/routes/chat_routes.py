from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from services.chroma_service import search_chunks
from groq import Groq
import os

router = APIRouter()

# 🔥 Load API KEY from .env
client = Groq(api_key=os.getenv("GROQ_API_KEY"))


class ChatRequest(BaseModel):
    question: str
    document_id: str


@router.post("/chat")
def chat(request: ChatRequest):

    try:
        question = request.question
        document_id = request.document_id

        # Step 1: Retrieve relevant chunks from ChromaDB
        relevant_chunks = search_chunks(question)

        context = "\n\n".join(relevant_chunks)

        # Step 2: Build prompt (THIS IS RAG CORE)
        prompt = f"""
You are a helpful AI assistant.
Answer ONLY using the context below.

Context:
{context}

Question:
{question}

Answer in a clear and simple way.
"""

        # Step 3: Call Groq LLM
        response = client.chat.completions.create(
            model="llama3-8b-8192",
            messages=[
                {"role": "user", "content": prompt}
            ]
        )

        answer = response.choices[0].message.content

        return {
            "question": question,
            "answer": answer,
            "context_used": relevant_chunks
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))