import os
import chromadb
from chromadb.auth.token_authn import TokenTransportHeader
from services.embedding_service import get_embedding

client = chromadb.HttpClient(
    ssl=True,
    host="api.trychroma.com",
    tenant=os.getenv("CHROMA_TENANT"),
    database=os.getenv("CHROMA_DATABASE"),
    headers={
        "x-chroma-token": os.getenv("CHROMA_API_KEY"),
    },
)

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
            "document_id": document_id,
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

    where_filter = {"document_id": document_id}

    if user_id:
        where_filter = {
            "$and": [
                {"document_id": document_id},
                {"user_id": str(user_id)},
            ]
        }

    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=5,
        where=where_filter,
    )

    if not results or not results.get("documents"):
        return []

    return results["documents"][0]