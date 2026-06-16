from fastapi import APIRouter, UploadFile, File, HTTPException
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
)

router = APIRouter()

UPLOAD_FOLDER = "uploads"


@router.post("/upload")
async def upload_document(file: UploadFile = File(...)):
    """
    Upload a supported document, save it locally,
    extract text, save metadata in MongoDB,
    and return a text preview.
    """

    if not file.filename:
        raise HTTPException(status_code=400, detail="No file selected")

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
            file_name=file.filename,
            saved_file_name=saved_file_name,
            file_type=file_extension,
            text_preview=extracted_text[:500],
            full_text_length=len(extracted_text),
            chunks_count=0,
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
    """
    Return all uploaded document metadata from MongoDB.
    """

    documents = get_all_documents()

    return {
        "documents": documents
    }