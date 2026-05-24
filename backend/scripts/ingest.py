"""
Ingestion script - loads compliance documents, chunks, embeds, and stores in ChromaDB.
Run this from inside the backend/ directory:
    python scripts/ingest.py              # ingest all regulations
    python scripts/ingest.py --regulation hipaa   # ingest HIPAA only
    python scripts/ingest.py --regulation gdpr    # ingest GDPR only
"""

import os
import sys
import argparse
from dotenv import load_dotenv

load_dotenv()

import chromadb
from llama_index.core import SimpleDirectoryReader, VectorStoreIndex, StorageContext
from llama_index.core.node_parser import SentenceSplitter
from llama_index.vector_stores.chroma import ChromaVectorStore
from llama_index.core import Settings as LlamaSettings

# Config
AI_PROVIDER = os.getenv("AI_PROVIDER", "gemini").lower()
BASE_DIR = os.path.join(os.path.dirname(__file__), "..")
DATA_DIR = os.path.join(BASE_DIR, "data")
CHROMA_DB_PATH = os.path.join(BASE_DIR, "storage", "chroma_db")
CHUNK_SIZE = 512
CHUNK_OVERLAP = 50

# Each regulation maps to a data file and a ChromaDB collection
REGULATIONS = {
    "gdpr": {
        "file": "gdpr_full_text.txt",
        "collection": "compliance_docs",  # keep existing collection name
        "label": "GDPR",
    },
    "hipaa": {
        "file": "hipaa_full_text.txt",
        "collection": "hipaa_docs",
        "label": "HIPAA",
    },
}


def get_embed_model():
    """Return the embedding model based on AI_PROVIDER config."""
    if AI_PROVIDER == "azure":
        from llama_index.embeddings.azure_openai import AzureOpenAIEmbedding
        return AzureOpenAIEmbedding(
            deployment_name=os.getenv("AZURE_OPENAI_EMBED_DEPLOYMENT"),
            azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
            api_key=os.getenv("AZURE_OPENAI_API_KEY"),
            api_version=os.getenv("AZURE_API_VERSION", "2024-02-15-preview"),
        )
    else:
        from llama_index.embeddings.google_genai import GoogleGenAIEmbedding
        return GoogleGenAIEmbedding(
            model_name="gemini-embedding-001",
            api_key=os.getenv("GOOGLE_API_KEY"),
        )


def load_documents(file_path):
    if not os.path.exists(file_path):
        print(f"Error: File not found at {file_path}")
        sys.exit(1)

    print(f"Loading: {file_path}")
    reader = SimpleDirectoryReader(input_files=[file_path])
    documents = reader.load_data()
    print(f"Loaded {len(documents)} page(s).")
    return documents


def chunk_documents(documents):
    splitter = SentenceSplitter(chunk_size=CHUNK_SIZE, chunk_overlap=CHUNK_OVERLAP)
    nodes = splitter.get_nodes_from_documents(documents)
    print(f"Created {len(nodes)} chunks (chunk_size={CHUNK_SIZE}, overlap={CHUNK_OVERLAP}).")
    return nodes


def build_vector_store(nodes, collection_name):
    os.makedirs(CHROMA_DB_PATH, exist_ok=True)

    chroma_client = chromadb.PersistentClient(path=CHROMA_DB_PATH)

    try:
        chroma_client.delete_collection(collection_name)
        print(f"Deleted existing collection: {collection_name}")
    except Exception:
        pass

    chroma_collection = chroma_client.get_or_create_collection(collection_name)
    vector_store = ChromaVectorStore(chroma_collection=chroma_collection)
    storage_context = StorageContext.from_defaults(vector_store=vector_store)

    LlamaSettings.embed_model = get_embed_model()

    print(f"Using AI provider: {AI_PROVIDER}")
    print("Generating embeddings and indexing...")
    index = VectorStoreIndex(nodes, storage_context=storage_context)

    print(f"Successfully indexed {len(nodes)} chunks into ChromaDB.")
    print(f"Database stored at: {CHROMA_DB_PATH}")
    return index


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Ingest compliance documents into ChromaDB.")
    parser.add_argument("--regulation", choices=list(REGULATIONS.keys()), help="Ingest a specific regulation only.")
    args = parser.parse_args()

    targets = [args.regulation] if args.regulation else list(REGULATIONS.keys())

    print("=" * 50)
    print("COMPLIANCE POLICY AI - Document Ingestion")
    print("=" * 50)

    for reg_key in targets:
        reg = REGULATIONS[reg_key]
        print(f"\n--- Ingesting {reg['label']} ---")
        file_path = os.path.join(DATA_DIR, reg["file"])
        documents = load_documents(file_path)
        nodes = chunk_documents(documents)
        build_vector_store(nodes, reg["collection"])

    print("\nIngestion complete. You can now start the API server.")
