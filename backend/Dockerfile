FROM python:3.11-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    OCR_LANGUAGE=eng \
    OCR_DPI=300 \
    OCR_TIMEOUT_SECONDS=30 \
    OCR_NATIVE_TEXT_MIN_CHARS=40 \
    MAX_OCR_PAGES=30 \
    MAX_IMAGE_PIXELS=25000000

WORKDIR /app

# Tesseract is a system application, not only a Python package.
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        tesseract-ocr \
        tesseract-ocr-eng \
        libgomp1 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt ./requirements.txt

RUN python -m pip install --upgrade pip setuptools wheel \
    && pip install -r requirements.txt

COPY . .

RUN mkdir -p /app/uploads /tmp/chroma_db

EXPOSE 5000

CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${PORT:-5000}"]
