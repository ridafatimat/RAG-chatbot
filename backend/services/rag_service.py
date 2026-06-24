from services.chunk_service import chunk_text
from services.chroma_service import store_chunks, search_chunks


def process_document(document_text: str, document_id: str, user_id: str | None = None):
    chunks = chunk_text(document_text)

    store_chunks(
        document_id=document_id,
        user_id=user_id,
        chunks=chunks,
    )

    return {
        "document_id": document_id,
        "chunks_count": len(chunks),
    }


def retrieve_relevant_chunks(
    question: str,
    document_id: str,
    user_id: str | None = None,
):
    return search_chunks(
        document_id=document_id,
        question=question,
        user_id=user_id,
    )