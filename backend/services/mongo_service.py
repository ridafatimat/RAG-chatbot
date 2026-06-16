import os
from datetime import datetime, timezone
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI")
DATABASE_NAME = os.getenv("DATABASE_NAME", "rag_db")

if not MONGO_URI:
    raise ValueError("MONGO_URI is missing. Please add it to backend/.env")

client = MongoClient(MONGO_URI)
db = client[DATABASE_NAME]

documents_collection = db["documents"]


def save_document_metadata(
    file_id: str,
    file_name: str,
    saved_file_name: str,
    file_type: str,
    text_preview: str,
    full_text_length: int,
    chunks_count: int = 0,
):
    document = {
        "file_id": file_id,
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
        document["_id"] = str(document["_id"])

        if "upload_date" in document:
            document["upload_date"] = document["upload_date"].isoformat()

        documents.append(document)

    return documents