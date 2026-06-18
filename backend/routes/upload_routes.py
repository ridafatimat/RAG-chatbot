from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
import os
import uuid
import re

from services.auth_service import get_current_user

from services.document_service import (
    extract_text_from_document,
    is_supported_file,
    get_file_extension,
    SUPPORTED_EXTENSIONS,
)

from services.mongo_service import (
    save_document_metadata,
    get_documents_by_user,
    get_document_by_file_id_for_user,
)

from services.chunk_service import chunk_text
from services.chroma_service import store_chunks

router = APIRouter()

UPLOAD_FOLDER = "uploads"
MAX_FILE_SIZE = 10 * 1024 * 1024


def sanitize_filename(filename: str) -> str:
    filename = os.path.basename(filename)
    filename = filename.replace(" ", "_")
    filename = re.sub(r"[^a-zA-Z0-9_.-]", "", filename)
    return filename


@router.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user),
):
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file selected")

    user_id = current_user["_id"]

    if not is_supported_file(file.filename):
        allowed_types = ", ".join(SUPPORTED_EXTENSIONS)
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type. Allowed file types are: {allowed_types}",
        )

    content = await file.read()

    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=400,
            detail="File is too large. Maximum allowed size is 10MB.",
        )

    os.makedirs(UPLOAD_FOLDER, exist_ok=True)

    file_id = str(uuid.uuid4())
    file_extension = get_file_extension(file.filename)

    safe_file_name = sanitize_filename(file.filename)
    saved_file_name = f"{file_id}_{safe_file_name}"
    file_path = os.path.join(UPLOAD_FOLDER, saved_file_name)

    try:
        with open(file_path, "wb") as f:
            f.write(content)

        extracted_text = extract_text_from_document(file_path, file.filename)

        if not extracted_text:
            raise HTTPException(
                status_code=400,
                detail="Could not extract readable text from this document",
            )

        chunks = chunk_text(extracted_text)

        store_chunks(file_id, chunks)

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
            detail=f"Something went wrong while processing the document: {str(e)}",
        )


@router.get("/documents")
def get_documents(current_user: dict = Depends(get_current_user)):
    return {
        "documents": get_documents_by_user(current_user["_id"])
    }


@router.get("/documents/detail/{document_id}")
def get_single_document(
    document_id: str,
    current_user: dict = Depends(get_current_user),
):
    document = get_document_by_file_id_for_user(
        file_id=document_id,
        user_id=current_user["_id"],
    )

    if not document:
        raise HTTPException(
            status_code=404,
            detail="Document not found or access denied.",
        )

    return {
        "document": document
    }


@router.get("/documents/user/{user_id}")
def get_user_documents(
    user_id: str,
    current_user: dict = Depends(get_current_user),
):
    if user_id != current_user["_id"]:
        raise HTTPException(
            status_code=403,
            detail="You cannot access another user's documents.",
        )

    return {
        "documents": get_documents_by_user(current_user["_id"])
    }