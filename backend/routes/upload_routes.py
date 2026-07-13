from typing import Any, Dict, List

from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, Request
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
from services.rate_limiter import limiter

router = APIRouter()

UPLOAD_FOLDER = "uploads"
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB


def sanitize_filename(filename: str) -> str:
    filename = os.path.basename(filename)
    filename = filename.replace(" ", "_")
    filename = re.sub(r"[^a-zA-Z0-9_.-]", "", filename)
    return filename


def flatten_extracted_text(extracted_content: Any) -> str:
    """
    Convert structured extraction output into one plain-text string.

    The updated document_service may return:
    - a plain string, or
    - a list of source sections such as PDF pages, PPTX slides,
      DOCX paragraphs, or spreadsheet row groups.

    This helper is used only for document preview and text-length metadata.
    Citation metadata remains attached to the chunks themselves.
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

        parts = []

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


def normalize_chunks_for_storage(
    chunks: List[Any],
    file_name: str,
    file_extension: str,
) -> List[Dict[str, Any]]:
    """
    Normalize chunk_service output into citation-aware chunk objects.

    Expected final structure:
    {
        "text": "chunk content",
        "metadata": {
            "chunk_index": 0,
            "source_type": "pdf",
            "source_label": "Page 1",
            "page_number": 1
        }
    }

    Plain string chunks are accepted temporarily and receive a chunk-level
    fallback citation until detailed service-layer extraction is added.
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
        "paragraph_start",
        "paragraph_end",
    )

    for index, chunk in enumerate(chunks):
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

            # Accept citation fields at the top level as well.
            for field in metadata_fields:
                if field in chunk and field not in metadata:
                    metadata[field] = chunk.get(field)
        else:
            continue

        if not text:
            continue

        metadata.setdefault("chunk_index", len(normalized_chunks))
        metadata.setdefault("source_type", file_extension)
        metadata.setdefault("file_name", file_name)

        if not metadata.get("source_label"):
            if metadata.get("page_number") not in (None, ""):
                metadata["source_label"] = (
                    f"Page {metadata['page_number']}"
                )
            elif metadata.get("slide_number") not in (None, ""):
                metadata["source_label"] = (
                    f"Slide {metadata['slide_number']}"
                )
            elif metadata.get("sheet_name"):
                row_start = metadata.get("row_start")
                row_end = metadata.get("row_end")

                if row_start not in (None, "") and row_end not in (None, ""):
                    metadata["source_label"] = (
                        f'Sheet "{metadata["sheet_name"]}", '
                        f"Rows {row_start}-{row_end}"
                    )
                elif row_start not in (None, ""):
                    metadata["source_label"] = (
                        f'Sheet "{metadata["sheet_name"]}", '
                        f"Row {row_start}"
                    )
                else:
                    metadata["source_label"] = (
                        f'Sheet "{metadata["sheet_name"]}"'
                    )
            elif metadata.get("paragraph_start") not in (None, ""):
                paragraph_start = metadata.get("paragraph_start")
                paragraph_end = metadata.get("paragraph_end")

                if (
                    paragraph_end not in (None, "")
                    and str(paragraph_start) != str(paragraph_end)
                ):
                    metadata["source_label"] = (
                        f"Paragraphs {paragraph_start}-{paragraph_end}"
                    )
                else:
                    metadata["source_label"] = (
                        f"Paragraph {paragraph_start}"
                    )
            else:
                metadata["source_label"] = (
                    f"Chunk {len(normalized_chunks) + 1}"
                )

        normalized_chunks.append(
            {
                "text": text,
                "metadata": metadata,
            }
        )

    return normalized_chunks


@router.post("/upload")
@limiter.limit("10/minute")
async def upload_document(
    request: Request,
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user),
):
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file selected.")

    user_id = current_user["_id"]

    if not is_supported_file(file.filename):
        allowed_types = ", ".join(SUPPORTED_EXTENSIONS)
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type. Allowed file types are: {allowed_types}",
        )

    content = await file.read()

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
        safe_file_name = f"document.{file_extension}"

    saved_file_name = f"{file_id}_{safe_file_name}"
    file_path = os.path.join(UPLOAD_FOLDER, saved_file_name)

    try:
        with open(file_path, "wb") as saved_file:
            saved_file.write(content)

        extracted_content = extract_text_from_document(
            file_path,
            file.filename,
        )

        extracted_text = flatten_extracted_text(extracted_content)

        if not extracted_text:
            raise HTTPException(
                status_code=400,
                detail="Could not extract readable text from this document.",
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
                detail="Could not split this document into searchable chunks.",
            )

        store_chunks(
            document_id=file_id,
            user_id=user_id,
            chunks=normalized_chunks,
        )

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
                "Document uploaded, processed, and stored in the RAG "
                "system successfully."
            ),
            "document": document_metadata,
            "text_preview": extracted_text[:500],
            "full_text_length": len(extracted_text),
            "chunks_count": len(normalized_chunks),
            "citation_ready": True,
        }

    except HTTPException:
        # Remove an unusable upload so failed processing does not leave
        # orphaned files on the server.
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
            except OSError:
                pass

        raise

    except Exception as error:
        print("UPLOAD ERROR:", error)

        if os.path.exists(file_path):
            try:
                os.remove(file_path)
            except OSError:
                pass

        raise HTTPException(
            status_code=500,
            detail="Something went wrong while processing the document.",
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