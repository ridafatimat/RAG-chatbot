import os
from typing import Any, Dict, List, Optional

import chromadb
from dotenv import load_dotenv

from services.embedding_service import get_embedding, get_embeddings


load_dotenv()


# ---------------------------------------------------------------------------
# CHROMA CONFIGURATION
# ---------------------------------------------------------------------------

# Local development:
#   ./chroma_db
#
# Railway production:
#   CHROMA_PATH=/data/chroma_db
#
# /data must be the mount path of the Railway persistent volume.
CHROMA_PATH = os.getenv("CHROMA_PATH", "./chroma_db").strip()
COLLECTION_NAME = os.getenv("CHROMA_COLLECTION", "documents").strip()

MetadataValue = str | int | float | bool


def get_chroma_client():
    """
    Always use Chroma PersistentClient.

    On Railway, CHROMA_PATH should point to the attached persistent volume:
        /data/chroma_db

    This prevents vectors from disappearing after a restart or deployment.
    """
    if not CHROMA_PATH:
        raise RuntimeError("CHROMA_PATH cannot be empty.")

    os.makedirs(CHROMA_PATH, exist_ok=True)

    print(f"CHROMA STORAGE MODE: PersistentClient")
    print(f"CHROMA STORAGE PATH: {os.path.abspath(CHROMA_PATH)}")
    print(f"CHROMA COLLECTION: {COLLECTION_NAME}")

    return chromadb.PersistentClient(path=CHROMA_PATH)


client = get_chroma_client()
collection = client.get_or_create_collection(name=COLLECTION_NAME)


# ---------------------------------------------------------------------------
# HELPERS
# ---------------------------------------------------------------------------

def _clean_text(value: Any) -> str:
    """
    Convert extracted content into clean searchable text.
    """
    if value is None:
        return ""

    return str(value).replace("\x00", "").strip()


def _to_chroma_metadata(
    metadata: Dict[str, Any],
) -> Dict[str, MetadataValue]:
    """
    Convert metadata values into scalar types accepted by Chroma.
    """
    cleaned: Dict[str, MetadataValue] = {}

    for key, value in metadata.items():
        if value is None or value == "":
            continue

        if isinstance(value, (str, int, float, bool)):
            cleaned[str(key)] = value
        else:
            cleaned[str(key)] = str(value)

    return cleaned


def _normalise_chunk(
    chunk: Any,
    index: int,
) -> Optional[Dict[str, Any]]:
    """
    Convert either a plain string or citation-aware chunk dictionary into:

    {
        "text": "...",
        "metadata": {...}
    }
    """
    if isinstance(chunk, str):
        text = _clean_text(chunk)
        metadata: Dict[str, Any] = {}

    elif isinstance(chunk, dict):
        text = _clean_text(
            chunk.get("text")
            or chunk.get("document")
            or chunk.get("content")
        )

        metadata = dict(chunk.get("metadata") or {})

    else:
        return None

    if not text:
        return None

    metadata.setdefault("chunk_index", index)
    metadata.setdefault("source_label", f"Chunk {index + 1}")

    return {
        "text": text,
        "metadata": metadata,
    }


def _build_where_filter(
    document_id: str,
    user_id: str | None = None,
) -> Dict[str, Any]:
    """
    Build a secure Chroma filter.

    When user_id is available, both document ownership fields must match.
    """
    if user_id:
        return {
            "$and": [
                {"document_id": str(document_id)},
                {"user_id": str(user_id)},
            ]
        }

    return {
        "document_id": str(document_id)
    }


# ---------------------------------------------------------------------------
# STORE CHUNKS
# ---------------------------------------------------------------------------

def store_chunks(
    document_id: str,
    chunks: List[Any],
    user_id: str | None = None,
) -> int:
    """
    Store document chunks with batch-generated embeddings and citation metadata.

    `upsert` is used so retrying the same upload does not create duplicate IDs.
    """
    ids: List[str] = []
    documents: List[str] = []
    metadatas: List[Dict[str, MetadataValue]] = []

    for original_index, raw_chunk in enumerate(chunks):
        chunk = _normalise_chunk(
            chunk=raw_chunk,
            index=original_index,
        )

        if not chunk:
            continue

        chunk_index = len(ids)
        text = chunk["text"]
        metadata = dict(chunk["metadata"])

        metadata["document_id"] = str(document_id)
        metadata["user_id"] = str(user_id) if user_id else ""
        metadata["chunk_index"] = chunk_index

        metadata.setdefault(
            "source_label",
            f"Chunk {chunk_index + 1}",
        )

        ids.append(f"{document_id}_{chunk_index}")
        documents.append(text)
        metadatas.append(
            _to_chroma_metadata(metadata)
        )

    if not ids:
        return 0

    embeddings = get_embeddings(documents)

    if len(embeddings) != len(documents):
        raise RuntimeError(
            "Embedding count did not match the document chunk count."
        )

    collection.upsert(
        ids=ids,
        embeddings=embeddings,
        documents=documents,
        metadatas=metadatas,
    )

    stored_count = count_document_chunks(
        document_id=document_id,
        user_id=user_id,
    )

    print(
        f"CHROMA STORE COMPLETE: "
        f"document_id={document_id}, "
        f"uploaded_chunks={len(ids)}, "
        f"stored_chunks={stored_count}"
    )

    return len(ids)


# ---------------------------------------------------------------------------
# SEARCH CHUNKS
# ---------------------------------------------------------------------------

def search_chunks(
    document_id: str,
    question: str,
    user_id: str | None = None,
    n_results: int = 5,
) -> List[Dict[str, Any]]:
    """
    Retrieve citation-aware chunks belonging only to the requested document
    and, when supplied, the authenticated user.
    """
    question = _clean_text(question)

    if not question:
        return []

    stored_count = count_document_chunks(
        document_id=document_id,
        user_id=user_id,
    )

    if stored_count == 0:
        print(
            f"CHROMA SEARCH: no stored chunks found for "
            f"document_id={document_id}, user_id={user_id}"
        )
        return []

    query_embedding = get_embedding(question)

    requested_results = max(1, int(n_results))
    safe_result_count = min(
        requested_results,
        stored_count,
    )

    where_filter = _build_where_filter(
        document_id=document_id,
        user_id=user_id,
    )

    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=safe_result_count,
        where=where_filter,
        include=[
            "documents",
            "metadatas",
            "distances",
        ],
    )

    if not results:
        return []

    document_groups = results.get("documents") or []
    metadata_groups = results.get("metadatas") or []
    distance_groups = results.get("distances") or []

    documents = (
        document_groups[0]
        if document_groups
        else []
    )

    metadatas = (
        metadata_groups[0]
        if metadata_groups
        else []
    )

    distances = (
        distance_groups[0]
        if distance_groups
        else []
    )

    sources: List[Dict[str, Any]] = []

    for index, document_text in enumerate(documents):
        text = _clean_text(document_text)

        if not text:
            continue

        metadata = (
            dict(metadatas[index])
            if (
                index < len(metadatas)
                and metadatas[index]
            )
            else {}
        )

        distance = (
            distances[index]
            if index < len(distances)
            else None
        )

        sources.append(
            {
                "text": text,
                "metadata": metadata,
                "distance": (
                    float(distance)
                    if distance is not None
                    else None
                ),
            }
        )

    print(
        f"CHROMA SEARCH COMPLETE: "
        f"document_id={document_id}, "
        f"stored_chunks={stored_count}, "
        f"returned_chunks={len(sources)}"
    )

    return sources


# ---------------------------------------------------------------------------
# COUNT / VERIFY CHUNKS
# ---------------------------------------------------------------------------

def count_document_chunks(
    document_id: str,
    user_id: str | None = None,
) -> int:
    """
    Count vectors currently stored for a document.

    This is useful for confirming that Railway volume persistence is working.
    """
    where_filter = _build_where_filter(
        document_id=document_id,
        user_id=user_id,
    )

    try:
        results = collection.get(
            where=where_filter,
            include=[],
        )
    except Exception as error:
        print(
            f"CHROMA COUNT ERROR: "
            f"document_id={document_id}, "
            f"reason={error}"
        )
        return 0

    ids = results.get("ids") or []

    return len(ids)


def document_chunks_exist(
    document_id: str,
    user_id: str | None = None,
) -> bool:
    """
    Return True when at least one stored vector exists for the document.
    """
    return (
        count_document_chunks(
            document_id=document_id,
            user_id=user_id,
        )
        > 0
    )


# ---------------------------------------------------------------------------
# DELETE CHUNKS
# ---------------------------------------------------------------------------

def delete_document_chunks(
    document_id: str,
    user_id: str | None = None,
) -> int:
    """
    Delete all Chroma chunks belonging to one document.

    Returns the number of chunks that existed before deletion.
    """
    existing_count = count_document_chunks(
        document_id=document_id,
        user_id=user_id,
    )

    if existing_count == 0:
        return 0

    where_filter = _build_where_filter(
        document_id=document_id,
        user_id=user_id,
    )

    collection.delete(where=where_filter)

    print(
        f"CHROMA DELETE COMPLETE: "
        f"document_id={document_id}, "
        f"deleted_chunks={existing_count}"
    )

    return existing_count