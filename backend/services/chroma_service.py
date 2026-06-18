import chromadb
from services.embedding_service import get_embedding

client = chromadb.PersistentClient(path="./chroma_db")

collection = client.get_or_create_collection(name="documents")


# -----------------------------
# STORE CHUNKS
# -----------------------------
def store_chunks(document_id, chunks):
    for i, chunk in enumerate(chunks):
        embedding = get_embedding(chunk)

        collection.add(
            ids=[f"{document_id}_{i}"],
            embeddings=[embedding],
            documents=[chunk],
            metadatas=[{
                "document_id": document_id
            }]
        )


# -----------------------------
# SEARCH CHUNKS (FILTERED RAG)
# -----------------------------
def search_chunks(document_id, question):
    results = collection.query(
        query_texts=[question],
        n_results=5,
        where={"document_id": document_id}
    )

    if not results or not results.get("documents"):
        return []

    return results["documents"][0]


def debug_document_chunks(document_id):
    results = collection.get(
        where={"document_id": document_id}
    )

    return {
        "count": len(results["ids"]),
        "ids": results["ids"][:5]
    }