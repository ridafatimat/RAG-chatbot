from fastapi import APIRouter, UploadFile, File, HTTPException
import os
import uuid
from services.pdf_service import extract_text_from_pdf

router = APIRouter()

UPLOAD_FOLDER = "uploads"


@router.post("/upload")
async def upload_pdf(file: UploadFile = File(...)):
    """
    Upload a PDF, save it locally, extract text, and return a preview.
    """

    if not file.filename:
        raise HTTPException(status_code=400, detail="No file selected")

    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are allowed")

    os.makedirs(UPLOAD_FOLDER, exist_ok=True)

    file_id = str(uuid.uuid4())
    safe_file_name = file.filename.replace(" ", "_")
    saved_file_name = f"{file_id}_{safe_file_name}"
    file_path = os.path.join(UPLOAD_FOLDER, saved_file_name)

    try:
        content = await file.read()

        with open(file_path, "wb") as f:
            f.write(content)

        extracted_text = extract_text_from_pdf(file_path)

        if not extracted_text:
            raise HTTPException(
                status_code=400,
                detail="Could not extract readable text from this PDF"
            )

        return {
            "message": "PDF uploaded and processed successfully",
            "file_id": file_id,
            "file_name": file.filename,
            "saved_file_name": saved_file_name,
            "text_preview": extracted_text[:500],
            "full_text_length": len(extracted_text),
            "extracted_text": extracted_text
        }

    except HTTPException:
        raise

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Something went wrong while processing the PDF: {str(e)}"
        )