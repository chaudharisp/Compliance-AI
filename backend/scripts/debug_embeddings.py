"""
Debug script - inspect embeddings stored in ChromaDB.
Run from backend/:  python scripts/debug_embeddings.py
"""

import os
from dotenv import load_dotenv

load_dotenv()

import chromadb

CHROMA_DB_PATH = os.path.join(os.path.dirname(__file__), "..", "storage", "chroma_db")
COLLECTION_NAME = "compliance_docs"


def inspect_embeddings():
    if not os.path.exists(CHROMA_DB_PATH):
        print("Error: Vector DB not found. Run scripts/ingest.py first.")
        return

    client = chromadb.PersistentClient(path=CHROMA_DB_PATH)
    collection = client.get_collection(COLLECTION_NAME)

    print(f"Collection: {COLLECTION_NAME}")
    print(f"Total documents: {collection.count()}")
    print("=" * 50)

    results = collection.get(limit=3, include=["embeddings"])

    if results["embeddings"]:
        for i, embedding in enumerate(results["embeddings"]):
            print(f"\n--- Embedding {i + 1} ---")
            print(f"Dimensions: {len(embedding)}")
            print(f"First 10 values: {embedding[:10]}")
    else:
        print("No embeddings found.")


if __name__ == "__main__":
    inspect_embeddings()
