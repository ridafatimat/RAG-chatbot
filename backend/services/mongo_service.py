import os
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import certifi
from bson import ObjectId
from dotenv import load_dotenv
from pymongo import MongoClient


load_dotenv()

MONGO_URI = os.getenv("MONGO_URI")
DATABASE_NAME = os.getenv("DATABASE_NAME", "rag_db")

if not MONGO_URI:
    raise ValueError("MONGO_URI is missing. Please add it to backend/.env")

client = MongoClient(
    MONGO_URI,
    tls=True,
    tlsCAFile=certifi.where(),
    serverSelectionTimeoutMS=30000,
)

db = client[DATABASE_NAME]

# -----------------------------
# COLLECTIONS
# -----------------------------
users_collection = db["users"]
documents_collection = db["documents"]
chat_sessions_collection = db["chat_sessions"]
chat_messages_collection = db["chat_messages"]
email_verifications_collection = db["email_verifications"]


# -----------------------------
# HELPERS
# -----------------------------
def _iso_datetime(value):
    if isinstance(value, datetime):
        return value.isoformat()

    return value


def format_document(document):
    if not document:
        return None

    formatted = dict(document)
    formatted["_id"] = str(formatted["_id"])

    if "user_id" in formatted and formatted["user_id"] is not None:
        formatted["user_id"] = str(formatted["user_id"])

    if formatted.get("upload_date"):
        formatted["upload_date"] = _iso_datetime(formatted["upload_date"])

    return formatted


def format_chat_session(session):
    if not session:
        return None

    formatted = dict(session)
    formatted["_id"] = str(formatted["_id"])

    if "user_id" in formatted and formatted["user_id"] is not None:
        formatted["user_id"] = str(formatted["user_id"])

    if formatted.get("created_at"):
        formatted["created_at"] = _iso_datetime(formatted["created_at"])

    return formatted


# -----------------------------
# USERS
# -----------------------------
def get_user_by_email(email: str):
    user = users_collection.find_one({"email": email})

    if not user:
        return None

    return {
        "_id": str(user["_id"]),
        "name": user.get("name"),
        "email": user.get("email"),
    }


# -----------------------------
# EMAIL OTP VERIFICATION HELPERS
# -----------------------------
def save_email_verification(
    name: str,
    email: str,
    password_hash: str,
    otp: str,
    expires_at,
    purpose: str = "register",
):
    record = {
        "name": name,
        "email": email,
        "password_hash": password_hash,
        "otp": otp,
        "expires_at": expires_at,
        "purpose": purpose,
        "created_at": datetime.now(timezone.utc),
    }

    email_verifications_collection.insert_one(record)


def get_email_verification(email: str, purpose: str | None = None):
    query = {"email": email}

    if purpose:
        query["purpose"] = purpose

    return email_verifications_collection.find_one(query)


def delete_email_verification(email: str, purpose: str | None = None):
    query = {"email": email}

    if purpose:
        query["purpose"] = purpose

    email_verifications_collection.delete_one(query)


# -----------------------------
# DOCUMENTS
# -----------------------------
def save_document_metadata(
    file_id: str,
    file_name: str,
    saved_file_name: str,
    file_type: str,
    text_preview: str,
    full_text_length: int,
    chunks_count: int = 0,
    user_id: str = None,
):
    document = {
        "file_id": file_id,
        "user_id": str(user_id) if user_id else None,
        "file_name": file_name,
        "saved_file_name": saved_file_name,
        "file_type": file_type,
        "upload_date": datetime.now(timezone.utc),
        "text_preview": text_preview,
        "full_text_length": full_text_length,
        "chunks_count": chunks_count,
        "citation_ready": True,
        "status": "uploaded_extracted",
    }

    result = documents_collection.insert_one(document)
    document["_id"] = result.inserted_id

    return format_document(document)


def get_documents_by_user(user_id: str):
    documents = []

    for document in documents_collection.find(
        {"user_id": str(user_id)}
    ).sort("upload_date", -1):
        documents.append(format_document(document))

    return documents


def get_document_by_file_id_for_user(file_id: str, user_id: str):
    document = documents_collection.find_one(
        {
            "file_id": file_id,
            "user_id": str(user_id),
        }
    )

    return format_document(document) if document else None


def get_document_by_id_for_user(document_id: str, user_id: str):
    document = documents_collection.find_one(
        {
            "file_id": document_id,
            "user_id": str(user_id),
        }
    )

    if document:
        return format_document(document)

    try:
        document = documents_collection.find_one(
            {
                "_id": ObjectId(document_id),
                "user_id": str(user_id),
            }
        )
    except Exception:
        return None

    return format_document(document) if document else None


def get_all_documents():
    """
    Internal/debug only. Do not expose this directly in public routes.
    """
    return [
        format_document(document)
        for document in documents_collection.find().sort("upload_date", -1)
    ]


# -----------------------------
# CHAT SESSIONS
# -----------------------------
def get_or_create_chat_session(user_id: str, document_id: str, title: str = None):
    user_id = str(user_id)

    existing = chat_sessions_collection.find_one(
        {
            "user_id": user_id,
            "document_id": document_id,
        }
    )

    if existing:
        return format_chat_session(existing)

    session = {
        "user_id": user_id,
        "document_id": document_id,
        "title": title or "New Chat",
        "created_at": datetime.now(timezone.utc),
    }

    result = chat_sessions_collection.insert_one(session)
    session["_id"] = result.inserted_id

    return format_chat_session(session)


def get_user_chat_sessions(user_id: str):
    sessions = chat_sessions_collection.find(
        {"user_id": str(user_id)}
    ).sort("created_at", -1)

    result = []

    for session in sessions:
        result.append(
            {
                "_id": str(session["_id"]),
                "title": session.get("title", "New Chat"),
                "document_id": session.get("document_id"),
                "created_at": _iso_datetime(session.get("created_at")),
            }
        )

    return result


def get_chat_session_by_id_for_user(chat_id: str, user_id: str):
    try:
        chat = chat_sessions_collection.find_one(
            {
                "_id": ObjectId(chat_id),
                "user_id": str(user_id),
            }
        )
    except Exception:
        return None

    return format_chat_session(chat) if chat else None


# -----------------------------
# CHAT MESSAGES
# -----------------------------
def save_chat_message(
    chat_id: str,
    role: str,
    message: str,
    answer_type: str = "plain",
    structured_answer=None,
    citations: Optional[List[Dict[str, Any]]] = None,
):
    """
    Save a chat message and any source citations used by that answer.
    """
    msg = {
        "chat_id": str(chat_id),
        "role": role,
        "message": message,
        "answer_type": answer_type,
        "structured_answer": structured_answer,
        "citations": citations or [],
        "timestamp": datetime.now(timezone.utc),
    }

    result = chat_messages_collection.insert_one(msg)
    return str(result.inserted_id)


def get_chat_messages(chat_id: str):
    messages = chat_messages_collection.find(
        {"chat_id": str(chat_id)}
    ).sort("timestamp", 1)

    result = []

    for message in messages:
        result.append(
            {
                "role": message.get("role"),
                "message": message.get("message"),
                "answer_type": message.get("answer_type", "plain"),
                "structured_answer": message.get("structured_answer"),
                "citations": message.get("citations", []),
                "timestamp": _iso_datetime(message.get("timestamp")),
            }
        )

    return result


def get_chat_messages_for_user(chat_id: str, user_id: str):
    chat = get_chat_session_by_id_for_user(chat_id, user_id)

    if not chat:
        return None

    return get_chat_messages(chat_id)