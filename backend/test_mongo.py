from pymongo import MongoClient
from dotenv import load_dotenv
import os

load_dotenv()

client = MongoClient(os.getenv("MONGO_URI"))
db = client["rag_chatbot"]

# Test insert
db.test.insert_one({"message": "MongoDB connected!"})
print("✅ MongoDB Atlas connected successfully!")