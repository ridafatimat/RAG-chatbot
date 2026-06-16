import chromadb

# Local folder mein save hoga
client = chromadb.PersistentClient(path="./chroma_db")

# Collection banao (jaise MongoDB mein collection hoti hai)
collection = client.get_or_create_collection(name="documents")

# Test data daalo
collection.add(
    documents=["Deadlock is a situation where processes are stuck waiting for each other."],
    ids=["test_1"]
)

# Search karo
results = collection.query(
    query_texts=["What is deadlock?"],
    n_results=1
)

print("✅ ChromaDB working!")
print("Result:", results["documents"][0][0])