import os
import threading
from typing import Iterable, List

import torch
from sentence_transformers import SentenceTransformer


MODEL_NAME = os.getenv(
    "EMBEDDING_MODEL_NAME",
    "sentence-transformers/all-MiniLM-L6-v2",
)
EMBEDDING_BATCH_SIZE = max(
    1,
    min(int(os.getenv("EMBEDDING_BATCH_SIZE", "16")), 64),
)
TORCH_NUM_THREADS = max(
    1,
    min(int(os.getenv("TORCH_NUM_THREADS", "1")), 8),
)

# Railway commonly provides limited CPU. Restricting PyTorch threads avoids
# one embedding request consuming every available thread.
torch.set_num_threads(TORCH_NUM_THREADS)

_model: SentenceTransformer | None = None
_model_lock = threading.Lock()
_encode_lock = threading.Lock()


def _get_model() -> SentenceTransformer:
    """
    Load the embedding model only when embeddings are first needed.

    This keeps lightweight endpoints such as /documents responsive during
    startup and avoids loading the model while FastAPI imports route modules.
    """
    global _model

    if _model is not None:
        return _model

    with _model_lock:
        if _model is None:
            print(f"Loading embedding model: {MODEL_NAME}")
            _model = SentenceTransformer(MODEL_NAME, device="cpu")
            print("Embedding model loaded successfully.")

    return _model


def _clean_texts(texts: Iterable[str]) -> List[str]:
    cleaned: List[str] = []

    for text in texts:
        value = str(text or "").replace("\x00", "").strip()
        if value:
            cleaned.append(value)

    return cleaned


def get_embeddings(texts: Iterable[str]) -> List[List[float]]:
    """
    Encode multiple texts in one SentenceTransformer batch.

    Batch encoding is substantially faster than calling model.encode once per
    chunk and uses less repeated Python overhead.
    """
    cleaned_texts = _clean_texts(texts)

    if not cleaned_texts:
        return []

    model = _get_model()

    # Serialise model inference on a small Railway instance to avoid multiple
    # simultaneous requests competing for CPU and memory.
    with _encode_lock:
        vectors = model.encode(
            cleaned_texts,
            batch_size=min(EMBEDDING_BATCH_SIZE, len(cleaned_texts)),
            show_progress_bar=False,
            convert_to_numpy=True,
            normalize_embeddings=True,
        )

    return vectors.tolist()


def get_embedding(text: str) -> List[float]:
    """Encode one text while keeping the existing service API compatible."""
    embeddings = get_embeddings([text])

    if not embeddings:
        raise ValueError("Cannot create an embedding for empty text.")

    return embeddings[0]