from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
import os
import re
import json

from services.chroma_service import search_chunks
from groq import Groq

from services.mongo_service import (
    save_chat_message,
    get_or_create_chat_session,
    get_chat_messages,
)

router = APIRouter()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))


class ChatRequest(BaseModel):
    question: str
    document_id: str
    user_id: str
    chat_id: Optional[str] = None


# ---------------------------------------------------------------------------
# Text helpers
# ---------------------------------------------------------------------------

def normalize_text(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r"\s+", " ", text)
    text = re.sub(r"[!,.?؛،۔]+$", "", text)
    return text


def has_urdu_script(text: str) -> bool:
    return any("\u0600" <= char <= "\u06FF" for char in text)


def looks_non_english(question: str) -> bool:
    """
    Detects if user input is likely Urdu/Roman Urdu/Hinglish.
    We still allow it, but we translate/search/answer in English.
    """

    text = normalize_text(question)

    if has_urdu_script(question):
        return True

    roman_urdu_words = [
        "kya", "kia", "kyun", "kyu", "kaise", "kesay", "kaisay",
        "kab", "kahan", "kidhar", "kon", "kaun", "kis",
        "mujhe", "mjy", "mje", "mujhy", "mera", "meri", "mere",
        "iska", "iske", "iski", "isse", "ye", "yeh", "yae",
        "batao", "btao", "samjhao", "smjhao", "karo", "krdo",
        "hai", "hain", "tha", "thi", "hoga", "hogaya", "hogayi",
        "nahi", "nae", "nai", "nahin", "acha", "achha", "theek",
        "haan", "han", "matlab", "wala", "wali", "mein", "mai", "main",
        "ko", "ka", "ki", "ke", "se", "say", "aur", "lekin", "agar",
    ]

    roman_urdu_phrases = [
        "is document ko",
        "isse document",
        "ye document",
        "yeh document",
        "document ko explain",
        "explain karo",
        "samjha do",
        "bata do",
        "batao is",
    ]

    clean_text = re.sub(r"[^a-zA-Z0-9\s]", " ", text)
    words = clean_text.split()

    roman_urdu_hits = sum(1 for word in words if word in roman_urdu_words)
    has_roman_phrase = any(phrase in text for phrase in roman_urdu_phrases)

    return roman_urdu_hits >= 1 or has_roman_phrase


def translate_question_to_english(question: str) -> str:
    """
    Converts any user question/request into clear English.
    This helps Chroma search English document chunks even when the user writes
    in Urdu, Roman Urdu, or Hinglish.
    """

    try:
        prompt = f"""
Convert the user's message into clear English.

Rules:
- Preserve the user's intent.
- If the message is already English, return it as clear English.
- If the message asks for MCQs, quiz, short questions, true/false, or past paper, preserve that request.
- Return ONLY the English version.
- Do not add explanation.

User message:
{question}
"""

        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "user", "content": prompt},
            ],
        )

        translated = response.choices[0].message.content.strip()

        if translated:
            return translated

        return question

    except Exception:
        return question


# ---------------------------------------------------------------------------
# Small talk
# ---------------------------------------------------------------------------

def is_question_like(text: str) -> bool:
    question_words = [
        # English
        "what", "why", "how", "when", "where", "who", "which",
        "explain", "describe", "summarize", "summary", "tell me",
        "can you", "could you", "does", "do", "is", "are", "was", "were",

        # Roman Urdu / Hinglish
        "kya", "kia", "kyun", "kyu", "kaise", "kesay", "kaisay",
        "kab", "kahan", "kidhar", "kon", "kaun", "kis",
        "batao", "btao", "samjhao", "smjhao", "summary do",
        "explain karo", "samjha do", "bata do",

        # Urdu script
        "کیا", "کیوں", "کیسے", "کب", "کہاں", "کون", "کس", "بتاؤ", "سمجھاؤ",
    ]

    if "?" in text:
        return True

    return any(word in text for word in question_words)


def handle_small_talk(question: str) -> Optional[str]:
    """
    Handles greetings, thanks, goodbye, and acknowledgements.
    IMPORTANT: We always reply in English now.
    """

    text = normalize_text(question)

    if not text:
        return "Please type a question about the uploaded document."

    if is_question_like(text):
        return None

    greetings = [
        "hi", "hello", "hey", "salam", "salaam", "aoa",
        "assalamualaikum", "assalam o alaikum", "assalamu alaikum",
        "السلام علیکم", "سلام",
    ]

    thanks_keywords = [
        "thank", "thanks", "thankyou", "thank you", "thx", "ty",
        "shukriya", "shukria", "jazakallah", "jazak allah",
        "جزاک", "شکریہ",
    ]

    goodbye_keywords = [
        "bye", "goodbye", "see you", "take care",
        "allah hafiz", "allah hafez", "khuda hafiz", "khuda hafez",
        "اللہ حافظ", "خدا حافظ",
    ]

    acknowledgement_phrases = [
        "ok", "okay", "acha", "achha", "theek", "theek hai",
        "haan", "han", "hmm", "got it", "done", "great", "nice",
        "samajh gaya", "samajh gai", "samajh aa gaya", "samajh aa gai",
        "ٹھیک", "ٹھیک ہے", "اچھا", "سمجھ گیا", "سمجھ گئی",
    ]

    if text in greetings:
        return "Hello! Feel free to ask me anything about the uploaded document."

    if any(word in text for word in thanks_keywords) and len(text.split()) <= 10:
        return "You're welcome! Let me know if you have more questions about the document."

    if any(word in text for word in goodbye_keywords) and len(text.split()) <= 10:
        return "Goodbye! Come back anytime to ask more questions about this document."

    if text in acknowledgement_phrases:
        return "Got it! Ask me another question whenever you're ready."

    return None


# ---------------------------------------------------------------------------
# Structured intent detection
# ---------------------------------------------------------------------------

def detect_structured_intent(question: str) -> str:
    """
    Detects whether user wants generated structured content.
    Use English-translated question for this function.
    """

    text = normalize_text(question)

    true_false_keywords = [
        "true false", "true/false", "true or false",
        "t/f", "tf questions", "true false questions",
    ]

    past_paper_keywords = [
        "past paper", "past papers", "long question", "long questions",
        "exam paper", "paper style", "section a", "section b",
        "create a paper", "make a paper",
    ]

    mcq_keywords = [
        "mcq", "mcqs", "multiple choice", "multiple-choice",
        "quiz", "quizzes", "choose the correct", "options",
    ]

    short_question_keywords = [
        "short questions", "short question", "short answer", "short answers",
        "qa", "q&a", "question answer", "question answers",
        "generate questions", "main questions",
        "important questions", "key questions",
    ]

    if any(keyword in text for keyword in true_false_keywords):
        return "true_false"

    if any(keyword in text for keyword in past_paper_keywords):
        return "past_paper"

    if any(keyword in text for keyword in mcq_keywords):
        return "mcq"

    if any(keyword in text for keyword in short_question_keywords):
        return "short_questions"

    return "plain"


def get_no_context_answer() -> str:
    return "I could not find the answer to your question in the provided document."


# ---------------------------------------------------------------------------
# Prompt builders
# ---------------------------------------------------------------------------

def build_rag_prompt(context: str, original_question: str, english_question: str) -> str:
    return f"""
You are a helpful document-question-answering assistant.

Language rule:
- The user may ask in any language, including Urdu, Roman Urdu, Hindi, or Hinglish.
- Understand the user's intent, but ALWAYS answer in English.
- Do NOT answer in Urdu, Roman Urdu, Hindi, or any other language.
- Your entire answer must be in clear English.

RAG rules:
- Answer using ONLY the information in the Document Context.
- Do NOT invent or assume facts not present in the context.
- If the answer cannot be found in the context, say:
  "I could not find the answer to your question in the provided document."
- Keep the answer clear, accurate, and concise.

Document Context:
{context}

Original User Question:
{original_question}

English Version of User Question:
{english_question}

Your answer in English:
"""


def build_structured_prompt(context: str, original_question: str, english_question: str, answer_type: str) -> str:
    if answer_type in ["mcq", "quiz"]:
        schema_instruction = """
Return ONLY valid JSON in this exact structure:
{
  "title": "MCQs",
  "questions": [
    {
      "question": "Question text",
      "options": ["A. Option", "B. Option", "C. Option", "D. Option"],
      "answer": "A. Correct option"
    }
  ]
}
"""

    elif answer_type == "short_questions":
        schema_instruction = """
Return ONLY valid JSON in this exact structure:
{
  "title": "Short Questions",
  "questions": [
    {
      "question": "Question text",
      "answer": "Short answer"
    }
  ]
}
"""

    elif answer_type == "true_false":
        schema_instruction = """
Return ONLY valid JSON in this exact structure:
{
  "title": "True/False Questions",
  "statements": [
    {
      "statement": "Statement text",
      "answer": "True"
    }
  ]
}
Use only "True" or "False" as the answer value.
"""

    elif answer_type == "past_paper":
        schema_instruction = """
Return ONLY valid JSON in this exact structure:
{
  "title": "Past Paper Style Questions",
  "sections": [
    {
      "heading": "Section A",
      "questions": [
        {
          "question": "Question text",
          "marks": "2",
          "answer": "Suggested answer"
        }
      ]
    }
  ]
}
"""

    else:
        schema_instruction = """
Return ONLY valid JSON:
{
  "title": "Generated Content",
  "questions": []
}
"""

    return f"""
You are a helpful document-question-answering assistant.

The user wants structured generated content from the uploaded document.

Language rule:
- The user may ask in any language, including Urdu, Roman Urdu, Hindi, or Hinglish.
- Understand the user's request, but generate ALL final content in English only.
- Do NOT generate Urdu, Roman Urdu, Hindi, or any other language.
- The JSON values must be written in English only.

Content rules:
- Use ONLY the provided document context.
- Do not invent facts outside the document.
- Generate useful exam/practice content from the document.
- Keep questions clear and student-friendly.

JSON rules:
- Return ONLY valid JSON.
- Do not include markdown.
- Do not include explanation outside JSON.
- Do not wrap JSON in backticks.

{schema_instruction}

Document Context:
{context}

Original User Request:
{original_question}

English Version of User Request:
{english_question}
"""


def parse_structured_answer(raw_answer: str):
    try:
        cleaned = raw_answer.strip()

        if cleaned.startswith("```"):
            cleaned = cleaned.replace("```json", "").replace("```", "").strip()

        return json.loads(cleaned)

    except Exception:
        return None


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@router.post("/chat")
def chat(request: ChatRequest):
    try:
        question = request.question.strip()
        document_id = request.document_id
        user_id = request.user_id
        chat_id = request.chat_id

        if not question:
            raise HTTPException(status_code=400, detail="Question cannot be empty.")

        if not chat_id:
            chat_session = get_or_create_chat_session(
                user_id=user_id,
                document_id=document_id,
                title=question[:40],
            )
            chat_id = str(chat_session["_id"])

        save_chat_message(
            chat_id=chat_id,
            role="user",
            message=question,
            answer_type="plain",
            structured_answer=None,
        )

        # Small talk still returns English only
        small_talk_answer = handle_small_talk(question)

        if small_talk_answer:
            save_chat_message(
                chat_id=chat_id,
                role="assistant",
                message=small_talk_answer,
                answer_type="plain",
                structured_answer=None,
            )

            return {
                "chat_id": chat_id,
                "question": question,
                "answer": small_talk_answer,
                "answer_type": "plain",
                "structured_answer": None,
                "context_used": [],
                "intent": "small_talk",
                "language": "English",
            }

        # Convert any input language to English before retrieval/intent detection
        english_question = translate_question_to_english(question)

        # Chroma search uses English query for better retrieval against English docs
        relevant_chunks = search_chunks(document_id, english_question)

        if not relevant_chunks:
            answer = get_no_context_answer()

            save_chat_message(
                chat_id=chat_id,
                role="assistant",
                message=answer,
                answer_type="plain",
                structured_answer=None,
            )

            return {
                "chat_id": chat_id,
                "question": question,
                "translated_question": english_question,
                "answer": answer,
                "answer_type": "plain",
                "structured_answer": None,
                "context_used": [],
                "intent": "document_question_no_context",
                "language": "English",
            }

        context = "\n\n".join(relevant_chunks)

        answer_type = detect_structured_intent(english_question)

        if answer_type != "plain":
            prompt = build_structured_prompt(
                context=context,
                original_question=question,
                english_question=english_question,
                answer_type=answer_type,
            )
        else:
            prompt = build_rag_prompt(
                context=context,
                original_question=question,
                english_question=english_question,
            )

        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "user", "content": prompt},
            ],
        )

        raw_answer = response.choices[0].message.content.strip()

        structured_answer = None
        final_answer_type = answer_type

        if answer_type != "plain":
            structured_answer = parse_structured_answer(raw_answer)

            if structured_answer:
                display_answer = f"Generated {answer_type.replace('_', ' ')}."
            else:
                display_answer = raw_answer
                final_answer_type = "plain"
        else:
            display_answer = raw_answer

        save_chat_message(
            chat_id=chat_id,
            role="assistant",
            message=display_answer,
            answer_type=final_answer_type,
            structured_answer=structured_answer,
        )

        return {
            "chat_id": chat_id,
            "question": question,
            "translated_question": english_question,
            "answer": display_answer,
            "answer_type": final_answer_type,
            "structured_answer": structured_answer,
            "context_used": relevant_chunks,
            "intent": "structured_generation" if structured_answer else "document_question",
            "language": "English",
        }

    except HTTPException:
        raise

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Chat processing failed: {str(e)}")


@router.get("/chat/session")
def get_chat_session(user_id: str, document_id: str):
    chat = get_or_create_chat_session(user_id, document_id)
    return {"chat_id": str(chat["_id"])}


@router.get("/chat/{chat_id}")
def get_chat(chat_id: str):
    messages = get_chat_messages(chat_id)

    formatted = [
        {
            "role": m.get("role"),
            "message": m.get("message"),
            "answer_type": m.get("answer_type", "plain"),
            "structured_answer": m.get("structured_answer"),
        }
        for m in messages
    ]

    return {"chat_id": chat_id, "messages": formatted}


@router.get("/debug/{document_id}")
def debug(document_id: str):
    from services.chroma_service import debug_document_chunks

    return debug_document_chunks(document_id)