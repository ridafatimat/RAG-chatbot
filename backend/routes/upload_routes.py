from fastapi import APIRouter, UploadFile, File, Form, HTTPException
import os
import uuid

from services.document_service import (
    extract_text_from_document,
    is_supported_file,
    get_file_extension,
    SUPPORTED_EXTENSIONS,
)

from services.mongo_service import (
    save_document_metadata,
    get_all_documents,
    get_documents_by_user,
    get_document_by_id,
    get_user_by_email,
)

# 🔥 RAG IMPORTS (MEMBER 2 ADDITION)
from services.chunk_service import chunk_text
from services.chroma_service import store_chunks

router = APIRouter()

UPLOAD_FOLDER = "uploads"


@router.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
    email: str = Form(...)
):
    """
    Upload a supported document, extract text,
    chunk it, store embeddings in ChromaDB,
    and save metadata in MongoDB.
    """

    if not file.filename:
        raise HTTPException(status_code=400, detail="No file selected")

    if not email:
        raise HTTPException(status_code=400, detail="Email is required")

    # Get user from MongoDB
    user = get_user_by_email(email)

    if not user:
        raise HTTPException(
            status_code=404,
            detail="User not found. Please register first."
        )

    user_id = user["_id"]

    # Validate file type
    if not is_supported_file(file.filename):
        allowed_types = ", ".join(SUPPORTED_EXTENSIONS)
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type. Allowed file types are: {allowed_types}"
        )

    os.makedirs(UPLOAD_FOLDER, exist_ok=True)

    file_id = str(uuid.uuid4())
    file_extension = get_file_extension(file.filename)

    safe_file_name = file.filename.replace(" ", "_")
    saved_file_name = f"{file_id}_{safe_file_name}"
    file_path = os.path.join(UPLOAD_FOLDER, saved_file_name)

    try:
        # Save file locally
        content = await file.read()

        with open(file_path, "wb") as f:
            f.write(content)

        # Extract text from PDF/document
        extracted_text = extract_text_from_document(file_path, file.filename)

        if not extracted_text:
            raise HTTPException(
                status_code=400,
                detail="Could not extract readable text from this document"
            )

        # ================================
        # 🔥 RAG PIPELINE STARTS HERE
        # ================================

        # Step 1: Chunk text
        chunks = chunk_text(extracted_text)

        # Step 2: Store embeddings in ChromaDB
        store_chunks(file_id, chunks)

        # ================================
        # Save metadata in MongoDB
        # ================================
        document_metadata = save_document_metadata(
            file_id=file_id,
            user_id=user_id,
            file_name=file.filename,
            saved_file_name=saved_file_name,
            file_type=file_extension,
            text_preview=extracted_text[:500],
            full_text_length=len(extracted_text),
            chunks_count=len(chunks),
        )

        return {
            "message": "Document uploaded, processed, and stored in RAG system successfully",
            "document": document_metadata,
            "text_preview": extracted_text[:500],
            "full_text_length": len(extracted_text),
            "chunks_count": len(chunks),
        }

    except HTTPException:
        raise

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Something went wrong while processing the document: {str(e)}"
        )


@router.get("/documents")
def get_documents():
    return {
        "documents": get_all_documents()
    }


@router.get("/documents/detail/{document_id}")
def get_single_document(document_id: str):
    document = get_document_by_id(document_id)

    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    return {
        "document": document
    }


@router.get("/documents/user/{user_id}")
def get_user_documents(user_id: str):
    return {
        "documents": get_documents_by_user(user_id)
    }