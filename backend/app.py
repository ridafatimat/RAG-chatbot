from flask import Flask, request, jsonify
from dotenv import load_dotenv
import os

# MongoDB
from pymongo import MongoClient

# ChromaDB
import chromadb
from chromadb.utils import embedding_functions

# Load env file
load_dotenv()

app = Flask(__name__)

# -----------------------------
# 1. MONGO DB SETUP
# -----------------------------
mongo_uri = os.getenv("MONGO_URI")

client = MongoClient(mongo_uri)
db = client["rag_db"]
chat_collection = db["chats"]

# -----------------------------
# 2. CHROMA DB SETUP
# -----------------------------
chroma_client = chromadb.PersistentClient(path="./chroma_db")

# Transformers embedding model
ef = embedding_functions.SentenceTransformerEmbeddingFunction(
    model_name="all-MiniLM-L6-v2"
)

collection = chroma_client.get_or_create_collection(
    name="documents",
    embedding_function=ef
)

# -----------------------------
# 3. TEST ROUTE
# -----------------------------
@app.route("/")
def home():
    return "Backend is running "

# -----------------------------
# 4. ADD DOCUMENT (ChromaDB)
# -----------------------------
@app.route("/add", methods=["POST"])
def add_document():
    data = request.json
    text = data.get("text")

    if not text:
        return jsonify({"error": "No text provided"}), 400

    doc_id = str(hash(text))

    collection.add(
        documents=[text],
        ids=[doc_id]
    )

    return jsonify({"message": "Document added", "id": doc_id})

# -----------------------------
# 5. SEARCH DOCUMENT (RAG style)
# -----------------------------
@app.route("/search", methods=["POST"])
def search():
    data = request.json
    query = data.get("query")

    results = collection.query(
        query_texts=[query],
        n_results=1
    )

    return jsonify({
        "query": query,
        "result": results["documents"][0][0]
    })

# -----------------------------
# 6. RUN SERVER
# -----------------------------
if __name__ == "__main__":
    app.run(debug=True, use_reloader=False, port=5000)