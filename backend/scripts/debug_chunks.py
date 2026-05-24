"""
Debug script - inspect stored chunks in ChromaDB.
Run from backend/:  python scripts/debug_chunks.py
"""

import os
from dotenv import load_dotenv

load_dotenv()

import chromadb

CHROMA_DB_PATH = os.path.join(os.path.dirname(__file__), "..", "storage", "chroma_db")
COLLECTION_NAME = "compliance_docs"


def inspect_chunks():
    if not os.path.exists(CHROMA_DB_PATH):
        print("Error: Vector DB not found. Run scripts/ingest.py first.")
        return

    client = chromadb.PersistentClient(path=CHROMA_DB_PATH)
    collection = client.get_collection(COLLECTION_NAME)

    count = collection.count()
    print(f"Collection: {COLLECTION_NAME}")
    print(f"Total chunks stored: {count}")
    print("=" * 50)

    results = collection.peek(limit=5)
    for i, doc in enumerate(results["documents"]):
        print(f"\n--- Chunk {i + 1} ---")
        print(f"Text: {doc[:200]}...")
        if results["metadatas"][i]:
            print(f"Metadata: {results['metadatas'][i]}")


if __name__ == "__main__":
    inspect_chunks()
