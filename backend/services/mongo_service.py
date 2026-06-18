import os
from datetime import datetime, timezone

from bson import ObjectId
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI")
DATABASE_NAME = os.getenv("DATABASE_NAME", "rag_db")

if not MONGO_URI:
    raise ValueError("MONGO_URI is missing. Please add it to backend/.env")

client = MongoClient(MONGO_URI)
db = client[DATABASE_NAME]

users_collection = db["users"]
documents_collection = db["documents"]
chat_sessions_collection = db["chat_sessions"]
chat_messages_collection = db["chat_messages"]


# -----------------------------
# HELPERS
# -----------------------------

def format_document(document):
    if not document:
        return None

    document["_id"] = str(document["_id"])

    if "user_id" in document:
        document["user_id"] = str(document["user_id"])

    if "upload_date" in document and document["upload_date"]:
        document["upload_date"] = document["upload_date"].isoformat()

    return document


def format_chat_session(session):
    if not session:
        return None

    session["_id"] = str(session["_id"])

    if "user_id" in session:
        session["user_id"] = str(session["user_id"])

    if "created_at" in session and session["created_at"]:
        session["created_at"] = session["created_at"].isoformat()

    return session


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
        "status": "uploaded_extracted",
    }

    result = documents_collection.insert_one(document)

    document["_id"] = str(result.inserted_id)
    document["upload_date"] = document["upload_date"].isoformat()

    return document


def get_all_documents():
    documents = []

    for document in documents_collection.find().sort("upload_date", -1):
        documents.append(format_document(document))

    return documents


def get_documents_by_user(user_id: str):
    documents = []

    for document in documents_collection.find(
        {"user_id": str(user_id)}
    ).sort("upload_date", -1):
        documents.append(format_document(document))

    return documents


def get_document_by_id(document_id: str):
    document = documents_collection.find_one({"file_id": document_id})

    if not document:
        try:
            document = documents_collection.find_one({"_id": ObjectId(document_id)})
        except Exception:
            return None

    if not document:
        return None

    return format_document(document)


def get_document_by_file_id_for_user(file_id: str, user_id: str):
    document = documents_collection.find_one({
        "file_id": file_id,
        "user_id": str(user_id),
    })

    if not document:
        return None

    return format_document(document)


# -----------------------------
# CHAT SESSIONS
# -----------------------------

def get_or_create_chat_session(user_id, document_id, title=None):
    user_id = str(user_id)

    existing = chat_sessions_collection.find_one({
        "user_id": user_id,
        "document_id": document_id,
    })

    if existing:
        return format_chat_session(existing)

    session = {
        "user_id": user_id,
        "document_id": document_id,
        "title": title or "New Chat",
        "created_at": datetime.now(timezone.utc),
    }

    result = chat_sessions_collection.insert_one(session)
    session["_id"] = str(result.inserted_id)
    session["created_at"] = session["created_at"].isoformat()

    return session


def get_user_chat_sessions(user_id):
    sessions = chat_sessions_collection.find(
        {"user_id": str(user_id)}
    ).sort("created_at", -1)

    result = []

    for session in sessions:
        result.append({
            "_id": str(session["_id"]),
            "title": session.get("title", "New Chat"),
            "document_id": session.get("document_id"),
            "created_at": session["created_at"].isoformat()
            if session.get("created_at")
            else None,
        })

    return result


def get_chat_session_by_id_for_user(chat_id: str, user_id: str):
    try:
        chat = chat_sessions_collection.find_one({
            "_id": ObjectId(chat_id),
            "user_id": str(user_id),
        })
    except Exception:
        return None

    if not chat:
        return None

    return format_chat_session(chat)


# -----------------------------
# CHAT MESSAGES
# -----------------------------

def save_chat_message(
    chat_id,
    role,
    message,
    answer_type="plain",
    structured_answer=None,
):
    msg = {
        "chat_id": str(chat_id),
        "role": role,
        "message": message,
        "answer_type": answer_type,
        "structured_answer": structured_answer,
        "timestamp": datetime.now(timezone.utc),
    }

    chat_messages_collection.insert_one(msg)


def get_chat_messages(chat_id):
    messages = chat_messages_collection.find(
        {"chat_id": str(chat_id)}
    ).sort("timestamp", 1)

    result = []

    for message in messages:
        result.append({
            "role": message.get("role"),
            "message": message.get("content") or message.get("message"),
            "answer_type": message.get("answer_type", "plain"),
            "structured_answer": message.get("structured_answer"),
            "timestamp": message["timestamp"].isoformat()
            if message.get("timestamp")
            else None,
        })

    return result


def get_chat_messages_for_user(chat_id: str, user_id: str):
    chat = get_chat_session_by_id_for_user(chat_id, user_id)

    if not chat:
        return None

    return get_chat_messages(chat_id)