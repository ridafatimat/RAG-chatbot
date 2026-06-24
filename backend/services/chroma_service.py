import chromadb
from services.embedding_service import get_embedding

client = chromadb.PersistentClient(path="./chroma_db")

collection = client.get_or_create_collection(name="documents")


# -----------------------------
# STORE CHUNKS
# -----------------------------
def store_chunks(document_id: str, chunks: list[str], user_id: str | None = None):
    ids = []
    embeddings = []
    documents = []
    metadatas = []

    for i, chunk in enumerate(chunks):
        embedding = get_embedding(chunk)

        ids.append(f"{document_id}_{i}")
        embeddings.append(embedding)
        documents.append(chunk)
        metadatas.append(
            {
                "document_id": document_id,
                "user_id": str(user_id) if user_id else "",
                "chunk_index": i,
            }
        )

    if ids:
        collection.add(
            ids=ids,
            embeddings=embeddings,
            documents=documents,
            metadatas=metadatas,
        )


# -----------------------------
# SEARCH CHUNKS - DOCUMENT FILTERED
# -----------------------------
def search_chunks(document_id: str, question: str, user_id: str | None = None):
    where_filter = {
        "document_id": document_id
    }

    if user_id:
        where_filter = {
            "$and": [
                {"document_id": document_id},
                {"user_id": str(user_id)},
            ]
        }

    results = collection.query(
        query_texts=[question],
        n_results=5,
        where=where_filter,
    )

    if not results or not results.get("documents"):
        return []

    return results["documents"][0]


def debug_document_chunks(document_id: str, user_id: str | None = None):
    where_filter = {
        "document_id": document_id
    }

    if user_id:
        where_filter = {
            "$and": [
                {"document_id": document_id},
                {"user_id": str(user_id)},
            ]
        }

    results = collection.get(
        where=where_filter
    )

    return {
        "count": len(results.get("ids", [])),
        "ids": results.get("ids", [])[:5],
    }