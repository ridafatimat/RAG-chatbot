import os
from typing import Any, Dict, List, Optional

import chromadb
from dotenv import load_dotenv

from services.embedding_service import get_embedding, get_embeddings


load_dotenv()

CHROMA_API_KEY = os.getenv("CHROMA_API_KEY")
CHROMA_TENANT = os.getenv("CHROMA_TENANT")
CHROMA_DATABASE = os.getenv("CHROMA_DATABASE")

# Railway/local fallback path
CHROMA_PATH = os.getenv("CHROMA_PATH", "/tmp/chroma_db")
COLLECTION_NAME = os.getenv("CHROMA_COLLECTION", "documents")


MetadataValue = str | int | float | bool


def get_chroma_client():
    """
    Try Chroma Cloud first. If credentials or connection fail, fall back to
    local persistent Chroma storage so the backend can still start.
    """
    if CHROMA_API_KEY and CHROMA_TENANT and CHROMA_DATABASE:
        try:
            print("Trying Chroma Cloud connection...")

            return chromadb.CloudClient(
                api_key=CHROMA_API_KEY.strip(),
                tenant=CHROMA_TENANT.strip(),
                database=CHROMA_DATABASE.strip(),
            )

        except Exception as error:
            print("Chroma Cloud connection failed.")
            print(f"Reason: {error}")
            print("Falling back to local Chroma storage...")

    else:
        print("Chroma Cloud env variables missing.")
        print("Using local Chroma storage...")

    os.makedirs(CHROMA_PATH, exist_ok=True)
    return chromadb.PersistentClient(path=CHROMA_PATH)


def _clean_text(value: Any) -> str:
    if value is None:
        return ""

    return str(value).replace("\x00", "").strip()


def _to_chroma_metadata(metadata: Dict[str, Any]) -> Dict[str, MetadataValue]:
    """Convert metadata into scalar values accepted by Chroma."""
    cleaned: Dict[str, MetadataValue] = {}

    for key, value in metadata.items():
        if value is None or value == "":
            continue

        if isinstance(value, (str, int, float, bool)):
            cleaned[str(key)] = value
        else:
            cleaned[str(key)] = str(value)

    return cleaned


def _normalise_chunk(chunk: Any, index: int) -> Optional[Dict[str, Any]]:
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


def get_collection():
    return client.get_or_create_collection(name=COLLECTION_NAME)


def store_chunks(
    document_id: str,
    chunks: List[Any],
    user_id: str | None = None,
) -> int:
    """
    Store chunk text, batch-generated embeddings, and citation metadata.

    All chunk embeddings are generated in one model.encode call rather than
    one model call per chunk.
    """
    ids: List[str] = []
    documents: List[str] = []
    metadatas: List[Dict[str, MetadataValue]] = []

    for index, raw_chunk in enumerate(chunks):
        chunk = _normalise_chunk(raw_chunk, index)

        if not chunk:
            continue

        text = chunk["text"]
        metadata = dict(chunk["metadata"])
        chunk_index = len(ids)

        metadata["document_id"] = str(document_id)
        metadata["user_id"] = str(user_id) if user_id else ""
        metadata["chunk_index"] = chunk_index

        ids.append(f"{document_id}_{chunk_index}")
        documents.append(text)
        metadatas.append(_to_chroma_metadata(metadata))

    if not ids:
        return 0

    embeddings = get_embeddings(documents)

    if len(embeddings) != len(documents):
        raise RuntimeError("Embedding count did not match the document chunk count.")

    # Upsert protects against duplicate IDs if processing is retried.
    collection.upsert(
        ids=ids,
        embeddings=embeddings,
        documents=documents,
        metadatas=metadatas,
    )

    return len(ids)


def search_chunks(
    document_id: str,
    question: str,
    user_id: str | None = None,
    n_results: int = 5,
) -> List[Dict[str, Any]]:
    """Retrieve citation-aware source chunks."""
    question = _clean_text(question)

    if not question:
        return []

    query_embedding = get_embedding(question)

    if user_id:
        where_filter = {
            "$and": [
                {"document_id": str(document_id)},
                {"user_id": str(user_id)},
            ]
        }
    else:
        where_filter = {"document_id": str(document_id)}

    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=max(1, int(n_results)),
        where=where_filter,
        include=["documents", "metadatas", "distances"],
    )

    if not results:
        return []

    document_groups = results.get("documents") or []
    metadata_groups = results.get("metadatas") or []
    distance_groups = results.get("distances") or []

    documents = document_groups[0] if document_groups else []
    metadatas = metadata_groups[0] if metadata_groups else []
    distances = distance_groups[0] if distance_groups else []

    sources: List[Dict[str, Any]] = []

    for index, document_text in enumerate(documents):
        text = _clean_text(document_text)

        if not text:
            continue

        metadata = (
            dict(metadatas[index])
            if index < len(metadatas) and metadatas[index]
            else {}
        )
        distance = distances[index] if index < len(distances) else None

        sources.append(
            {
                "text": text,
                "metadata": metadata,
                "distance": float(distance) if distance is not None else None,
            }
        )

    return sources


def delete_document_chunks(
    document_id: str,
    user_id: str | None = None,
) -> None:
    """Delete all Chroma chunks belonging to one document."""
    if user_id:
        where_filter = {
            "$and": [
                {"document_id": str(document_id)},
                {"user_id": str(user_id)},
            ]
        }
    else:
        where_filter = {"document_id": str(document_id)}

    collection.delete(where=where_filter)


client = get_chroma_client()
collection = get_collection()