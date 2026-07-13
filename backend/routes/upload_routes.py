import os
import re
import uuid
from typing import Any, Dict, List

from fastapi import APIRouter, Depends, File, HTTPException, Request, UploadFile

from services.auth_service import get_current_user
from services.chroma_service import delete_document_chunks, store_chunks
from services.chunk_service import chunk_text
from services.document_service import (
    DocumentExtractionError,
    OCRUnavailableError,
    SUPPORTED_EXTENSIONS,
    extract_text_from_document,
    get_file_extension,
    is_supported_file,
)
from services.mongo_service import (
    get_document_by_file_id_for_user,
    get_documents_by_user,
    save_document_metadata,
)
from services.rate_limiter import limiter


router = APIRouter()

UPLOAD_FOLDER = "uploads"
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB


def sanitize_filename(filename: str) -> str:
    filename = os.path.basename(filename)
    filename = filename.replace(" ", "_")
    filename = re.sub(r"[^a-zA-Z0-9_.-]", "", filename)
    return filename


def format_supported_extensions() -> str:
    return ", ".join(extension.lstrip(".").upper() for extension in SUPPORTED_EXTENSIONS)


def remove_file_safely(file_path: str) -> None:
    if not file_path or not os.path.exists(file_path):
        return

    try:
        os.remove(file_path)
    except OSError:
        pass


def remove_chunks_safely(document_id: str, user_id: str) -> None:
    """Best-effort cleanup if processing fails after Chroma storage."""
    try:
        delete_document_chunks(
            document_id=document_id,
            user_id=user_id,
        )
    except Exception as cleanup_error:
        print("CHROMA CLEANUP ERROR:", cleanup_error)


def flatten_extracted_text(extracted_content: Any) -> str:
    """
    Convert structured extraction output into one plain-text string for the
    MongoDB preview and text-length fields. Citation metadata remains attached
    to chunks and is not flattened.
    """
    if isinstance(extracted_content, str):
        return extracted_content.strip()

    if isinstance(extracted_content, dict):
        direct_text = (
            extracted_content.get("text")
            or extracted_content.get("content")
            or ""
        )

        nested_sections = (
            extracted_content.get("sections")
            or extracted_content.get("pages")
            or extracted_content.get("slides")
            or extracted_content.get("sheets")
            or []
        )

        parts: List[str] = []

        if isinstance(direct_text, str) and direct_text.strip():
            parts.append(direct_text.strip())

        if nested_sections:
            nested_text = flatten_extracted_text(nested_sections)
            if nested_text:
                parts.append(nested_text)

        return "\n\n".join(parts).strip()

    if isinstance(extracted_content, list):
        parts = []

        for item in extracted_content:
            item_text = flatten_extracted_text(item)
            if item_text:
                parts.append(item_text)

        return "\n\n".join(parts).strip()

    return ""


def extraction_uses_ocr(extracted_content: Any) -> bool:
    """Return True when at least one extracted source section used OCR."""
    if isinstance(extracted_content, list):
        return any(extraction_uses_ocr(item) for item in extracted_content)

    if not isinstance(extracted_content, dict):
        return False

    metadata = extracted_content.get("metadata")

    if isinstance(metadata, dict) and metadata.get("ocr_used") is True:
        return True

    nested_sections = (
        extracted_content.get("sections")
        or extracted_content.get("pages")
        or extracted_content.get("slides")
        or extracted_content.get("sheets")
        or []
    )

    return extraction_uses_ocr(nested_sections) if nested_sections else False


def normalize_chunks_for_storage(
    chunks: List[Any],
    file_name: str,
    file_extension: str,
) -> List[Dict[str, Any]]:
    """
    Normalize chunk-service output into citation-aware chunk objects.

    Plain strings remain supported as a fallback, while structured chunks keep
    page, slide, sheet, paragraph, table, image, and OCR metadata.
    """
    normalized_chunks: List[Dict[str, Any]] = []

    metadata_fields = (
        "source_type",
        "source_label",
        "page_number",
        "slide_number",
        "sheet_name",
        "row_start",
        "row_end",
        "line_start",
        "line_end",
        "paragraph_start",
        "paragraph_end",
        "table_number",
        "table_row_start",
        "table_row_end",
        "image_number",
        "extraction_method",
        "ocr_used",
    )

    for chunk in chunks:
        if isinstance(chunk, str):
            text = chunk.strip()
            metadata: Dict[str, Any] = {}
        elif isinstance(chunk, dict):
            text = str(
                chunk.get("text")
                or chunk.get("content")
                or ""
            ).strip()

            metadata = dict(chunk.get("metadata") or {})

            for field in metadata_fields:
                if field in chunk and field not in metadata:
                    metadata[field] = chunk.get(field)
        else:
            continue

        if not text:
            continue

        chunk_index = len(normalized_chunks)
        metadata.setdefault("chunk_index", chunk_index)
        metadata.setdefault(
            "source_type",
            file_extension.lstrip(".") or "document",
        )
        metadata.setdefault("file_name", file_name)

        if not metadata.get("source_label"):
            page_number = metadata.get("page_number")
            slide_number = metadata.get("slide_number")
            sheet_name = metadata.get("sheet_name")
            row_start = metadata.get("row_start")
            row_end = metadata.get("row_end")
            line_start = metadata.get("line_start")
            line_end = metadata.get("line_end")
            paragraph_start = metadata.get("paragraph_start")
            paragraph_end = metadata.get("paragraph_end")
            table_number = metadata.get("table_number")
            table_row_start = metadata.get("table_row_start")
            table_row_end = metadata.get("table_row_end")
            image_number = metadata.get("image_number")

            if page_number not in (None, ""):
                metadata["source_label"] = f"Page {page_number}"
            elif slide_number not in (None, ""):
                metadata["source_label"] = f"Slide {slide_number}"
            elif image_number not in (None, ""):
                metadata["source_label"] = (
                    "Image"
                    if str(image_number) == "1"
                    else f"Image {image_number}"
                )
            elif sheet_name:
                if row_start not in (None, "") and row_end not in (None, ""):
                    if str(row_start) == str(row_end):
                        metadata["source_label"] = (
                            f'Sheet "{sheet_name}", Row {row_start}'
                        )
                    else:
                        metadata["source_label"] = (
                            f'Sheet "{sheet_name}", Rows {row_start}-{row_end}'
                        )
                elif row_start not in (None, ""):
                    metadata["source_label"] = (
                        f'Sheet "{sheet_name}", Row {row_start}'
                    )
                else:
                    metadata["source_label"] = f'Sheet "{sheet_name}"'
            elif line_start not in (None, ""):
                metadata["source_label"] = (
                    f"Line {line_start}"
                    if line_end in (None, "") or str(line_start) == str(line_end)
                    else f"Lines {line_start}-{line_end}"
                )
            elif paragraph_start not in (None, ""):
                metadata["source_label"] = (
                    f"Paragraph {paragraph_start}"
                    if paragraph_end in (None, "")
                    or str(paragraph_start) == str(paragraph_end)
                    else f"Paragraphs {paragraph_start}-{paragraph_end}"
                )
            elif table_number not in (None, "") and table_row_start not in (None, ""):
                metadata["source_label"] = (
                    f"Table {table_number}, Row {table_row_start}"
                    if table_row_end in (None, "")
                    or str(table_row_start) == str(table_row_end)
                    else (
                        f"Table {table_number}, Rows "
                        f"{table_row_start}-{table_row_end}"
                    )
                )
            else:
                metadata["source_label"] = f"Chunk {chunk_index + 1}"

        normalized_chunks.append(
            {
                "text": text,
                "metadata": metadata,
            }
        )

    return normalized_chunks


@router.post("/upload")
@limiter.limit("10/minute")
def upload_document(
    request: Request,
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user),
):
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file selected.")

    user_id = current_user["_id"]

    if not is_supported_file(file.filename):
        raise HTTPException(
            status_code=400,
            detail=(
                "Unsupported file type. Allowed file types are: "
                f"{format_supported_extensions()}."
            ),
        )

    file.file.seek(0)
    content = file.file.read()

    if not content:
        raise HTTPException(
            status_code=400,
            detail="The selected file is empty.",
        )

    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=400,
            detail="File is too large. Maximum allowed size is 10MB.",
        )

    os.makedirs(UPLOAD_FOLDER, exist_ok=True)

    file_id = str(uuid.uuid4())
    file_extension = get_file_extension(file.filename)
    safe_file_name = sanitize_filename(file.filename)

    if not safe_file_name:
        safe_file_name = f"document{file_extension}"

    saved_file_name = f"{file_id}_{safe_file_name}"
    file_path = os.path.join(UPLOAD_FOLDER, saved_file_name)
    chunks_stored = False

    try:
        with open(file_path, "wb") as saved_file:
            saved_file.write(content)

        extracted_content = extract_text_from_document(
            file_path=file_path,
            file_name=file.filename,
        )

        extracted_text = flatten_extracted_text(extracted_content)

        if not extracted_text:
            raise HTTPException(
                status_code=400,
                detail="Could not extract readable text from this file.",
            )

        raw_chunks = chunk_text(extracted_content)
        normalized_chunks = normalize_chunks_for_storage(
            chunks=raw_chunks,
            file_name=file.filename,
            file_extension=file_extension,
        )

        if not normalized_chunks:
            raise HTTPException(
                status_code=400,
                detail="Could not split this file into searchable chunks.",
            )

        stored_count = store_chunks(
            document_id=file_id,
            user_id=user_id,
            chunks=normalized_chunks,
        )

        if stored_count <= 0:
            raise HTTPException(
                status_code=500,
                detail="Could not store searchable chunks for this file.",
            )

        chunks_stored = True
        ocr_used = extraction_uses_ocr(extracted_content)

        document_metadata = save_document_metadata(
            file_id=file_id,
            user_id=user_id,
            file_name=file.filename,
            saved_file_name=saved_file_name,
            file_type=file_extension,
            text_preview=extracted_text[:500],
            full_text_length=len(extracted_text),
            chunks_count=len(normalized_chunks),
        )

        return {
            "message": (
                "File uploaded, OCR-processed, and stored in the RAG system "
                "successfully."
                if ocr_used
                else (
                    "Document uploaded, processed, and stored in the RAG "
                    "system successfully."
                )
            ),
            "document": document_metadata,
            "text_preview": extracted_text[:500],
            "full_text_length": len(extracted_text),
            "chunks_count": len(normalized_chunks),
            "citation_ready": True,
            "ocr_used": ocr_used,
        }

    except HTTPException:
        if chunks_stored:
            remove_chunks_safely(file_id, user_id)
        remove_file_safely(file_path)
        raise

    except OCRUnavailableError as error:
        print("OCR CONFIGURATION ERROR:", error)
        if chunks_stored:
            remove_chunks_safely(file_id, user_id)
        remove_file_safely(file_path)
        raise HTTPException(
            status_code=503,
            detail=str(error),
        )

    except DocumentExtractionError as error:
        print("DOCUMENT EXTRACTION ERROR:", error)
        if chunks_stored:
            remove_chunks_safely(file_id, user_id)
        remove_file_safely(file_path)
        raise HTTPException(
            status_code=400,
            detail=str(error),
        )

    except Exception as error:
        print("UPLOAD ERROR:", error)
        if chunks_stored:
            remove_chunks_safely(file_id, user_id)
        remove_file_safely(file_path)
        raise HTTPException(
            status_code=500,
            detail="Something went wrong while processing the file.",
        )


@router.get("/documents")
@limiter.limit("60/minute")
def get_documents(
    request: Request,
    current_user: dict = Depends(get_current_user),
):
    return {
        "documents": get_documents_by_user(current_user["_id"])
    }


@router.get("/documents/detail/{document_id}")
@limiter.limit("60/minute")
def get_single_document(
    request: Request,
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
@limiter.limit("60/minute")
def get_user_documents(
    request: Request,
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