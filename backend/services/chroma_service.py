import os
import chromadb
from dotenv import load_dotenv

from services.embedding_service import get_embedding

load_dotenv()

CHROMA_API_KEY = os.getenv("CHROMA_API_KEY")
CHROMA_TENANT = os.getenv("CHROMA_TENANT")
CHROMA_DATABASE = os.getenv("CHROMA_DATABASE")

# Railway/local fallback path
CHROMA_PATH = os.getenv("CHROMA_PATH", "/tmp/chroma_db")


def get_chroma_client():
    """
    Try Chroma Cloud first.
    If Chroma Cloud credentials fail, fall back to local Chroma
    so the backend does not crash on Railway.
    """

    if CHROMA_API_KEY and CHROMA_TENANT and CHROMA_DATABASE:
        try:
            print("Trying Chroma Cloud connection...")

            return chromadb.CloudClient(
                api_key=CHROMA_API_KEY.strip(),
                tenant=CHROMA_TENANT.strip(),
                database=CHROMA_DATABASE.strip(),
            )

        except Exception as e:
            print("Chroma Cloud connection failed.")
            print(f"Reason: {e}")
            print("Falling back to local Chroma storage...")

    else:
        print("Chroma Cloud env variables missing.")
        print("Using local Chroma storage...")

    return chromadb.PersistentClient(path=CHROMA_PATH)


client = get_chroma_client()
collection = client.get_or_create_collection(name="documents")


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
        metadatas.append({
            "document_id": str(document_id),
            "user_id": str(user_id) if user_id else "",
            "chunk_index": i,
        })

    if ids:
        collection.add(
            ids=ids,
            embeddings=embeddings,
            documents=documents,
            metadatas=metadatas,
        )


def search_chunks(document_id: str, question: str, user_id: str | None = None):
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
        n_results=5,
        where=where_filter,
    )

    if not results or not results.get("documents"):
        return []

    return results["documents"][0]