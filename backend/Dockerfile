FROM python:3.11-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    TOKENIZERS_PARALLELISM=false \
    OMP_NUM_THREADS=1 \
    MKL_NUM_THREADS=1 \
    TORCH_NUM_THREADS=1 \
    EMBEDDING_BATCH_SIZE=16 \
    SENTENCE_TRANSFORMERS_HOME=/app/models \
    OCR_LANGUAGE=eng \
    OCR_DPI=180 \
    OCR_TIMEOUT_SECONDS=15 \
    OCR_NATIVE_TEXT_MIN_CHARS=40 \
    MAX_OCR_PAGES=10 \
    MAX_IMAGE_PIXELS=25000000

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        tesseract-ocr \
        tesseract-ocr-eng \
        libgomp1 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt ./requirements.txt

RUN python -m pip install --upgrade pip setuptools wheel \
    && pip install -r requirements.txt

# Cache the embedding model in the Docker image. The service can then start
# without downloading model files from Hugging Face at runtime.
RUN mkdir -p /app/models \
    && python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2', device='cpu')"

COPY . .

RUN mkdir -p /app/uploads /tmp/chroma_db

EXPOSE 5000

CMD ["sh", "-c", "exec uvicorn app:app --host 0.0.0.0 --port ${PORT:-5000} --workers 1"]