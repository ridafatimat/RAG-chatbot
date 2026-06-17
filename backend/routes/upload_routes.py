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

router = APIRouter()

UPLOAD_FOLDER = "uploads"


@router.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
    email: str = Form(...)
):
    """
    Upload a supported document, save it locally,
    find user by email, save metadata in MongoDB with user_id,
    and return a text preview.
    """

    if not file.filename:
        raise HTTPException(status_code=400, detail="No file selected")

    if not email:
        raise HTTPException(status_code=400, detail="Email is required")

    user = get_user_by_email(email)

    if not user:
        raise HTTPException(
            status_code=404,
            detail="User not found. Please register first."
        )

    user_id = user["_id"]

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
        content = await file.read()

        with open(file_path, "wb") as f:
            f.write(content)

        extracted_text = extract_text_from_document(file_path, file.filename)

        if not extracted_text:
            raise HTTPException(
                status_code=400,
                detail="Could not extract readable text from this document"
            )

        document_metadata = save_document_metadata(
            file_id=file_id,
            user_id=user_id,
            file_name=file.filename,
            saved_file_name=saved_file_name,
            file_type=file_extension,
            text_preview=extracted_text[:500],
            full_text_length=len(extracted_text),
            chunks_count=3,
        )

        return {
            "message": "Document uploaded, processed, and saved successfully",
            "document": document_metadata,
            "text_preview": extracted_text[:500],
            "full_text_length": len(extracted_text),
            "extracted_text": extracted_text,
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
    documents = get_all_documents()

    return {
        "documents": documents
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
    documents = get_documents_by_user(user_id)

    return {
        "documents": documents
    }