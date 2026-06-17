from services.chunk_service import chunk_text
from services.embedding_service import get_embedding
from services.chroma_service import store_chunk, search_chunks


def process_document(document_text, document_id):
    chunks = chunk_text(document_text)

    for i, chunk in enumerate(chunks):
        embedding = get_embedding(chunk)

        store_chunk(
            chunk_id=f"{document_id}_{i}",
            text=chunk,
            embedding=embedding,
            metadata={"document_id": document_id}
        )


def retrieve_relevant_chunks(question):
    query_embedding = get_embedding(question)
    results = search_chunks(query_embedding)

    chunks = results["documents"][0]
    return chunks