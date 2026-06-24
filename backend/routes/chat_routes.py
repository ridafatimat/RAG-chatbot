import os
import re
import json
from typing import Optional

from fastapi import APIRouter, HTTPException, Depends, Request
from pydantic import BaseModel
from groq import Groq

from services.auth_service import get_current_user
from services.chroma_service import search_chunks
from services.rate_limiter import limiter

from services.mongo_service import (
    save_chat_message,
    get_or_create_chat_session,
    get_chat_messages,
    get_document_by_file_id_for_user,
    get_chat_session_by_id_for_user,
)

router = APIRouter()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))


class ChatRequest(BaseModel):
    question: str
    document_id: str
    chat_id: Optional[str] = None


# ---------------------------------------------------------------------------
# Text helpers
# ---------------------------------------------------------------------------

def normalize_text(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r"\s+", " ", text)
    text = re.sub(r"[!,.?؛،۔]+$", "", text)
    return text


def translate_question_to_english(question: str) -> str:
    """
    User can ask in any language. We convert intent to English,
    but final answer must always be in English.
    """
    try:
        prompt = f"""
Convert the user's message into clear English.

Rules:
- Preserve the user's exact intent.
- Preserve requested length exactly, for example "1-2 lines", "one paragraph", "5 bullet points".
- Preserve follow-up meaning, for example "now tell their answers", "explain these", "convert above into table".
- Preserve requested format exactly, for example MCQs, flashcards, chart, table, summary, Q&A.
- If already English, return the improved English version only.
- Return ONLY the English version.
- Do not add explanation.

User message:
{question}
"""
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": prompt}],
            temperature=0,
        )
        translated = response.choices[0].message.content.strip()
        return translated if translated else question
    except Exception:
        return question


# ---------------------------------------------------------------------------
# Intent Detection
# ---------------------------------------------------------------------------

def detect_intent(text: str) -> str:
    """
    Generic intent detector.
    Security/auth is not handled here.
    """
    t = text.lower()

    if any(k in t for k in [
        "pie chart", "bar chart", "line chart", "chart", "graph",
        "visualize", "visualise", "represent through chart",
        "represent karo", "chart k zariye", "chart ke zariye"
    ]):
        return "chart"

    if any(k in t for k in [
        "answers to these", "answer these", "tell their answers",
        "tell me their answers", "now tell their answers",
        "in ke answers", "inke answers", "answers batao"
    ]):
        return "followup_answers"

    if any(k in t for k in ["true false", "true/false", "true or false", "t/f", "truefalse"]):
        return "true_false"

    if any(k in t for k in ["fill in the blank", "fill blank", "fill-in", "blanks", "fill in blank"]):
        return "fill_blanks"

    if any(k in t for k in ["mcq", "mcqs", "multiple choice", "multiple-choice"]):
        return "mcq"

    if any(k in t for k in ["flashcard", "flash card", "flashcards"]):
        return "flashcard"

    if any(k in t for k in ["summary", "summarize", "summarise", "summarization", "tldr", "tl;dr"]):
        return "summary"

    if any(k in t for k in ["comparison", "compare", "vs", "versus", "difference between"]):
        return "comparison"

    if any(k in t for k in ["timeline", "chronological", "sequence of events", "in order"]):
        return "timeline"

    if any(k in t for k in ["checklist", "check list", "to-do", "todo list", "steps"]):
        return "checklist"

    if any(k in t for k in ["table", "tabular", "in a table"]):
        return "table"

    if any(k in t for k in ["short question", "short questions", "short q", "short qs", "sq"]):
        return "short_qa"

    if any(k in t for k in ["long question", "long questions", "long q", "long qs", "detailed question"]):
        return "long_qa"

    if any(k in t for k in ["definition", "define", "glossary", "meaning of"]):
        return "definition"

    if any(k in t for k in ["code", "snippet", "function", "algorithm", "program"]):
        return "code"

    return "generic"


def detect_length_instruction(text: str) -> str:
    """
    Extract simple length constraints from user request.
    This is used inside prompt so the model does not ignore requests like 1-2 lines.
    """
    t = text.lower()

    match = re.search(r"(\d+)\s*[-–to]+\s*(\d+)\s*(line|lines|sentence|sentences|paragraph|paragraphs)", t)
    if match:
        return f"Answer in exactly {match.group(1)}-{match.group(2)} {match.group(3)}."

    match = re.search(r"(\d+)\s*(line|lines|sentence|sentences|paragraph|paragraphs|bullet points|points)", t)
    if match:
        return f"Answer in exactly {match.group(1)} {match.group(2)}."

    if any(k in t for k in ["brief", "briefly", "short", "concise", "very short"]):
        return "Keep the answer brief and concise."

    return "Follow the user's requested length. If no length is requested, use a clear helpful length."


# ---------------------------------------------------------------------------
# Chat history formatting
# ---------------------------------------------------------------------------

def build_recent_chat_history(chat_id: str, limit: int = 8) -> str:
    """
    Include recent conversation so follow-ups like
    'now tell their answers' work correctly.
    """
    try:
        messages = get_chat_messages(chat_id)
        recent_messages = messages[-limit:]

        formatted = []
        for msg in recent_messages:
            role = msg.get("role", "unknown")
            message = msg.get("message", "")

            structured = msg.get("structured_answer")
            if structured:
                try:
                    message = json.dumps(structured, ensure_ascii=False)
                except Exception:
                    pass

            if message:
                formatted.append(f"{role.upper()}: {message}")

        return "\n\n".join(formatted)
    except Exception:
        return ""


# ---------------------------------------------------------------------------
# Prompt builder
# ---------------------------------------------------------------------------

def get_not_found_json() -> str:
    return '''{
  "title": "Answer Not Found",
  "type": "structured",
  "blocks": [
    {
      "block_type": "warning",
      "content": "The document does not provide enough information to answer this."
    }
  ]
}'''


def build_prompt_for_intent(
    intent: str,
    context: str,
    chat_history: str,
    original_question: str,
    english_question: str,
) -> str:

    length_rule = detect_length_instruction(original_question + " " + english_question)
    not_found_json = get_not_found_json()

    base_rules = f"""
You are a strict document-based RAG assistant.

ABSOLUTE RULES:
- Answer in English only.
- Use ONLY the provided Document Context and relevant Recent Chat History.
- Do NOT use outside knowledge.
- Do NOT invent names, technologies, definitions, databases, tools, dates, or facts.
- If the information is not available in the document/context, return the not-found JSON.
- Follow the user's requested format exactly.
- {length_rule}
- Do not repeat headings.
- Do not add unnecessary headings.
- Do not mention retrieved chunks.
- Return ONLY valid JSON.
- No markdown.
- No backticks.
- No explanation outside JSON.

IMPORTANT:
- Examples are NOT document facts. Do not copy examples as answers.
- If user asks "from this document", all content must come from Document Context.
- If user asks a follow-up like "now tell their answers", use Recent Chat History to identify what "their" refers to, then answer using Document Context.

Document Context:
{context}

Recent Chat History:
{chat_history if chat_history else "No previous chat history available."}

Original User Request:
{original_question}

English Version:
{english_question}
"""

    # -----------------------------------------------------------------------
    if intent == "summary":
        return base_rules + f"""
TASK:
Summarize the document according to the user's exact requested length.

STRICT SUMMARY RULES:
- If the user asked for 1-2 lines, return only one paragraph block with 1-2 lines.
- Do NOT add "Overview" or "Key Points" unless the user specifically asks for headings/key points.
- Do NOT include bullet points unless the user asks for bullet points.

Return JSON:
{{
  "title": "Summary",
  "type": "structured",
  "blocks": [
    {{
      "block_type": "paragraph",
      "content": "The summary here, following the exact requested length."
    }}
  ]
}}

If not enough context, return:
{not_found_json}
"""

    # -----------------------------------------------------------------------
    if intent == "mcq":
        return base_rules + f"""
TASK:
Generate MCQs only from the document.

STRICT MCQ RULES:
- Each MCQ must be based on an explicit document fact.
- Do NOT ask about concepts not present in the document.
- Do NOT use generic RAG/AI examples unless they are actually in the document.
- Each MCQ must have exactly 4 options: A, B, C, D.
- The answer must be the full correct option.
- Generate the number of MCQs requested by the user. If no number is requested, generate 5.

Return JSON:
{{
  "title": "Multiple Choice Questions",
  "type": "structured",
  "blocks": [
    {{
      "block_type": "mcq",
      "question": "Question based only on the document?",
      "options": [
        "A. Option from document",
        "B. Plausible option",
        "C. Plausible option",
        "D. Plausible option"
      ],
      "answer": "A. Option from document"
    }}
  ]
}}

If not enough context, return:
{not_found_json}
"""

    # -----------------------------------------------------------------------
    if intent == "flashcard":
        return base_rules + f"""
TASK:
Generate flashcards from important document points.

STRICT FLASHCARD RULES:
- Only use terms, tasks, goals, features, dates, or facts that appear in the document.
- Do NOT create flashcards about general concepts unless the document explains them.
- Keep each answer concise.
- Generate the number requested by the user. If no number is requested, generate 6.

Return JSON:
{{
  "title": "Flashcards",
  "type": "structured",
  "blocks": [
    {{
      "block_type": "qa",
      "question": "Front side of flashcard",
      "answer": "Back side of flashcard based only on document."
    }}
  ]
}}

If not enough context, return:
{not_found_json}
"""

    # -----------------------------------------------------------------------
    if intent == "followup_answers":
        return base_rules + f"""
TASK:
The user is asking for answers to previously generated questions.

STRICT FOLLOW-UP RULES:
- Find the previous questions from Recent Chat History.
- Answer those exact questions.
- Use Document Context for the answers.
- Do NOT create new questions.
- Do NOT change the previous questions.
- If an answer is not available in Document Context, write: "Not available in the document."

Return JSON:
{{
  "title": "Answers",
  "type": "structured",
  "blocks": [
    {{
      "block_type": "qa",
      "question": "Previous question copied here?",
      "answer": "Answer from the document."
    }}
  ]
}}

If there are no previous questions in Recent Chat History, return:
{{
  "title": "No Previous Questions Found",
  "type": "structured",
  "blocks": [
    {{
      "block_type": "warning",
      "content": "I could not find previous questions in this chat to answer."
    }}
  ]
}}
"""

    # -----------------------------------------------------------------------
    if intent == "chart":
        return base_rules + f"""
TASK:
Represent document information as chart-ready data.

STRICT CHART RULES:
- If the user asks for a pie chart, provide labels and numeric values.
- Values should be based on reasonable counts from the document context, such as number of tasks, features, sections, or mentions.
- Do NOT pretend an actual image chart was created.
- Do NOT provide random percentages unless you can derive them from the document context.
- Include a short explanation of what the values represent.

Return JSON:
{{
  "title": "Chart Data",
  "type": "structured",
  "blocks": [
    {{
      "block_type": "paragraph",
      "content": "This chart data represents the document content by category."
    }},
    {{
      "block_type": "table",
      "headers": ["Label", "Value"],
      "rows": [
        ["Category 1", "3"],
        ["Category 2", "2"]
      ]
    }}
  ]
}}

If not enough context, return:
{not_found_json}
"""

    # -----------------------------------------------------------------------
    if intent == "true_false":
        return base_rules + f"""
TASK:
Generate True/False statements from the document.

STRICT RULES:
- Each question must be a declarative statement.
- The answer must be only "True" or "False".
- Do NOT use blanks.
- Generate the number requested by the user. If no number is requested, generate 5.

Return JSON:
{{
  "title": "True/False Questions",
  "type": "structured",
  "blocks": [
    {{
      "block_type": "qa",
      "question": "A statement based on the document.",
      "answer": "True"
    }}
  ]
}}

If not enough context, return:
{not_found_json}
"""

    # -----------------------------------------------------------------------
    if intent == "fill_blanks":
        return base_rules + f"""
TASK:
Generate fill-in-the-blank questions from the document.

STRICT RULES:
- Replace one key document term with ______.
- The answer must be the missing word or phrase.
- Generate the number requested by the user. If no number is requested, generate 5.

Return JSON:
{{
  "title": "Fill in the Blanks",
  "type": "structured",
  "blocks": [
    {{
      "block_type": "qa",
      "question": "Sentence with ______ blank.",
      "answer": "Missing word or phrase"
    }}
  ]
}}

If not enough context, return:
{not_found_json}
"""

    # -----------------------------------------------------------------------
    if intent == "short_qa":
        return base_rules + f"""
TASK:
Generate short question-answer pairs from the document.

STRICT RULES:
- Questions must be based only on document facts.
- Answers must be 1-2 sentences.
- Generate the number requested by the user. If no number is requested, generate 5.

Return JSON:
{{
  "title": "Short Questions and Answers",
  "type": "structured",
  "blocks": [
    {{
      "block_type": "qa",
      "question": "Question from document?",
      "answer": "Short answer from document."
    }}
  ]
}}

If not enough context, return:
{not_found_json}
"""

    # -----------------------------------------------------------------------
    if intent == "long_qa":
        return base_rules + f"""
TASK:
Generate detailed question-answer pairs from the document.

STRICT RULES:
- Questions must be based only on document facts.
- Answers should be detailed but not invented.
- Generate the number requested by the user. If no number is requested, generate 3.

Return JSON:
{{
  "title": "Detailed Questions and Answers",
  "type": "structured",
  "blocks": [
    {{
      "block_type": "qa",
      "question": "Detailed question from document?",
      "answer": "Detailed answer from document."
    }}
  ]
}}

If not enough context, return:
{not_found_json}
"""

    # -----------------------------------------------------------------------
    if intent == "table":
        return base_rules + f"""
TASK:
Present requested document information in a table.

Return JSON:
{{
  "title": "Table",
  "type": "structured",
  "blocks": [
    {{
      "block_type": "table",
      "headers": ["Column 1", "Column 2"],
      "rows": [
        ["Value 1", "Value 2"]
      ]
    }}
  ]
}}

If not enough context, return:
{not_found_json}
"""

    # -----------------------------------------------------------------------
    if intent == "comparison":
        return base_rules + f"""
TASK:
Compare topics mentioned in the user's request using only document content.

Return JSON:
{{
  "title": "Comparison",
  "type": "structured",
  "blocks": [
    {{
      "block_type": "table",
      "headers": ["Aspect", "Item 1", "Item 2"],
      "rows": [
        ["Aspect from document", "Details", "Details"]
      ]
    }}
  ]
}}

If not enough context, return:
{not_found_json}
"""

    # -----------------------------------------------------------------------
    if intent == "timeline":
        return base_rules + f"""
TASK:
Create a timeline or ordered sequence from the document.

Return JSON:
{{
  "title": "Timeline",
  "type": "structured",
  "blocks": [
    {{
      "block_type": "numbered_list",
      "items": ["First event or step", "Second event or step"]
    }}
  ]
}}

If not enough context, return:
{not_found_json}
"""

    # -----------------------------------------------------------------------
    if intent == "checklist":
        return base_rules + f"""
TASK:
Create a checklist from the document.

Return JSON:
{{
  "title": "Checklist",
  "type": "structured",
  "blocks": [
    {{
      "block_type": "list",
      "items": ["Checklist item 1", "Checklist item 2"]
    }}
  ]
}}

If not enough context, return:
{not_found_json}
"""

    # -----------------------------------------------------------------------
    if intent == "definition":
        return base_rules + f"""
TASK:
Define or explain terms using only the document.

Return JSON:
{{
  "title": "Definitions",
  "type": "structured",
  "blocks": [
    {{
      "block_type": "qa",
      "question": "Term or question",
      "answer": "Definition from the document."
    }}
  ]
}}

If not enough context, return:
{not_found_json}
"""

    # -----------------------------------------------------------------------
    if intent == "code":
        return base_rules + f"""
TASK:
Answer code or technical questions using only code/technical content in the document.

Return JSON:
{{
  "title": "Code Explanation",
  "type": "structured",
  "blocks": [
    {{
      "block_type": "paragraph",
      "content": "Explanation from the document."
    }},
    {{
      "block_type": "code",
      "content": "Code from the document if available."
    }}
  ]
}}

If not enough context, return:
{not_found_json}
"""

    # -----------------------------------------------------------------------
    return base_rules + f"""
TASK:
Answer the user's request using the most suitable structure.

STRICT GENERIC RULES:
- If the user asks a direct question, answer directly.
- If the user asks for a format, follow that format.
- If the user asks for a short answer, keep it short.
- Do not add extra sections unless useful or requested.

Allowed block types:
- paragraph
- list
- numbered_list
- qa
- mcq
- table
- code
- quote
- warning

Return JSON:
{{
  "title": "Answer",
  "type": "structured",
  "blocks": [
    {{
      "block_type": "paragraph",
      "content": "Answer from the document."
    }}
  ]
}}

If not enough context, return:
{not_found_json}
"""


def parse_structured_answer(raw_answer: str):
    try:
        cleaned = raw_answer.strip()
        if cleaned.startswith("```"):
            cleaned = cleaned.replace("```json", "").replace("```", "").strip()

        data = json.loads(cleaned)

        if not isinstance(data, dict):
            return None

        if "blocks" not in data or not isinstance(data["blocks"], list):
            return None

        if "title" not in data:
            data["title"] = "Generated Answer"

        data["type"] = "structured"

        # Remove duplicate adjacent heading blocks
        cleaned_blocks = []
        previous_heading = None

        for block in data["blocks"]:
            if not isinstance(block, dict):
                continue

            if block.get("block_type") == "heading":
                current_heading = str(block.get("content", "")).strip().lower()
                if current_heading and current_heading == previous_heading:
                    continue
                previous_heading = current_heading
            else:
                previous_heading = None

            cleaned_blocks.append(block)

        data["blocks"] = cleaned_blocks

        return data
    except Exception:
        return None


# ---------------------------------------------------------------------------
# Small talk
# ---------------------------------------------------------------------------

def is_question_like(text: str) -> bool:
    question_words = [
        "what", "why", "how", "when", "where", "who", "which",
        "explain", "describe", "summarize", "summary", "tell me",
        "can you", "could you", "does", "do", "is", "are", "was", "were",
        "generate", "create", "make", "give", "write", "prepare",
        "mcq", "mcqs", "quiz", "question", "questions", "true false",
        "fill in the blanks", "fill blanks", "blanks", "past paper",
        "flashcards", "table", "timeline", "checklist", "comparison",
        "definitions", "notes", "points", "chart", "graph", "pie chart",
        "kya", "kia", "kyun", "kyu", "kaise", "kesay", "kaisay",
        "kab", "kahan", "kidhar", "kon", "kaun", "kis",
        "batao", "btao", "samjhao", "smjhao", "summary do",
        "explain karo", "samjha do", "bata do", "generate karo",
        "bana do", "answers", "jawab", "jawaab",
        "کیا", "کیوں", "کیسے", "کب", "کہاں", "کون", "کس", "بتاؤ", "سمجھاؤ",
    ]
    if "?" in text:
        return True
    return any(word in text for word in question_words)


def handle_small_talk(question: str) -> Optional[str]:
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


def get_no_context_answer() -> str:
    return "The document does not provide enough information to answer this."


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@router.post("/chat")
@limiter.limit("20/minute")
def chat(
    request: Request,
    chat_request: ChatRequest,
    current_user: dict = Depends(get_current_user),
):
    try:
        question = chat_request.question.strip()
        document_id = chat_request.document_id
        chat_id = chat_request.chat_id
        user_id = current_user["_id"]

        if not question:
            raise HTTPException(status_code=400, detail="Question cannot be empty.")

        # SECURITY: Do not change.
        document = get_document_by_file_id_for_user(
            file_id=document_id,
            user_id=user_id,
        )
        if not document:
            raise HTTPException(
                status_code=403,
                detail="You do not have access to this document.",
            )

        # SECURITY: Do not change.
        if chat_id:
            existing_chat = get_chat_session_by_id_for_user(
                chat_id=chat_id,
                user_id=user_id,
            )
            if not existing_chat:
                raise HTTPException(
                    status_code=403,
                    detail="You do not have access to this chat.",
                )
            if existing_chat.get("document_id") != document_id:
                raise HTTPException(
                    status_code=403,
                    detail="This chat session does not belong to this document.",
                )

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

        # Small talk check
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

        # User can ask in any language, but answer should be English.
        english_question = translate_question_to_english(question)

        # Detect intent from combined original + translated text.
        intent = detect_intent(f"{question} {english_question}")

        # Recent chat history for follow-ups like "now tell their answers"
        chat_history = build_recent_chat_history(chat_id)

        # For follow-up questions, search using current question + recent history
        # so retrieval has better context.
        retrieval_query = english_question
        if intent == "followup_answers" and chat_history:
            retrieval_query = f"{english_question}\n\nRecent chat:\n{chat_history}"

        relevant_chunks = search_chunks(
            document_id=document_id,
            question=retrieval_query,
            user_id=user_id,
        )

        if not relevant_chunks:
            no_context_answer = {
                "title": "Answer Not Found",
                "type": "structured",
                "blocks": [
                    {
                        "block_type": "warning",
                        "content": get_no_context_answer(),
                    }
                ],
            }
            save_chat_message(
                chat_id=chat_id,
                role="assistant",
                message="Answer not found in the document.",
                answer_type="structured",
                structured_answer=no_context_answer,
            )
            return {
                "chat_id": chat_id,
                "question": question,
                "translated_question": english_question,
                "answer": "Answer not found in the document.",
                "answer_type": "structured",
                "structured_answer": no_context_answer,
                "context_used": [],
                "intent": "document_question_no_context",
                "language": "English",
            }

        context = "\n\n".join(relevant_chunks)

        prompt = build_prompt_for_intent(
            intent=intent,
            context=context,
            chat_history=chat_history,
            original_question=question,
            english_question=english_question,
        )

        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,
        )

        raw_answer = response.choices[0].message.content.strip()
        structured_answer = parse_structured_answer(raw_answer)

        if structured_answer:
            display_answer = structured_answer.get("title", "Generated answer.")
            final_answer_type = "structured"
        else:
            # Fallback if model ever fails JSON
            display_answer = raw_answer
            final_answer_type = "plain"

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
            "intent": intent,
            "language": "English",
        }

    except HTTPException:
        raise
    except Exception as error:
        print("CHAT ERROR:", error)
        raise HTTPException(
            status_code=500,
            detail="Chat processing failed.",
        )


@router.get("/chat/session")
@limiter.limit("30/minute")
def get_chat_session(
    request: Request,
    document_id: str,
    current_user: dict = Depends(get_current_user),
):
    user_id = current_user["_id"]

    # SECURITY: Do not change.
    document = get_document_by_file_id_for_user(
        file_id=document_id,
        user_id=user_id,
    )
    if not document:
        raise HTTPException(
            status_code=403,
            detail="You do not have access to this document.",
        )

    chat = get_or_create_chat_session(
        user_id=user_id,
        document_id=document_id,
    )

    return {"chat_id": str(chat["_id"])}


@router.get("/chat/{chat_id}")
@limiter.limit("60/minute")
def get_chat(
    request: Request,
    chat_id: str,
    current_user: dict = Depends(get_current_user),
):
    user_id = current_user["_id"]

    # SECURITY: Do not change.
    chat = get_chat_session_by_id_for_user(
        chat_id=chat_id,
        user_id=user_id,
    )
    if not chat:
        raise HTTPException(
            status_code=403,
            detail="You do not have access to this chat.",
        )

    messages = get_chat_messages(chat_id)

    formatted = [
        {
            "role": message.get("role"),
            "message": message.get("message"),
            "answer_type": message.get("answer_type", "plain"),
            "structured_answer": message.get("structured_answer"),
        }
        for message in messages
    ]

    return {
        "chat_id": chat_id,
        "messages": formatted,
    }