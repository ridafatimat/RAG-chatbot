import chromadb
from services.embedding_service import get_embedding

client = chromadb.PersistentClient(path="./chroma_db")

collection = client.get_or_create_collection(name="documents")

def store_chunks(doc_id, chunks):
    for i, chunk in enumerate(chunks):
        embedding = get_embedding(chunk)

        collection.add(
            ids=[f"{doc_id}_{i}"],
            embeddings=[embedding],
            documents=[chunk],
            metadatas=[{"doc_id": doc_id}]
        )

def search_chunks(query, top_k=3):
    query_embedding = get_embedding(query)

    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=top_k
    )

    return results["documents"][0]