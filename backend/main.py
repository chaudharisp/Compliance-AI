"""
FastAPI backend for Compliance Policy AI.
Start with:  uvicorn main:app --reload
"""

import os
from dotenv import load_dotenv

load_dotenv()

import chromadb
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional
from pydantic import BaseModel
from llama_index.core import VectorStoreIndex
from llama_index.vector_stores.chroma import ChromaVectorStore
from llama_index.core import Settings as LlamaSettings
from usage_tracker import tracker, estimate_tokens

MAX_HISTORY_TURNS = 3  # Send last N Q&A pairs for context (controls token cost)

# Config
AI_PROVIDER = os.getenv("AI_PROVIDER", "gemini").lower()
CHROMA_DB_PATH = os.path.join(os.path.dirname(__file__), "storage", "chroma_db")
TOP_K = 5

# Map regulation names to ChromaDB collections
REGULATION_COLLECTIONS = {
    "hipaa": "hipaa_docs",
    "gdpr": "compliance_docs",
}
DEFAULT_REGULATION = "hipaa"

SYSTEM_PROMPT = (
    "You are a compliance and regulatory policy assistant. "
    "Answer questions based strictly on the provided context from official regulatory documents. "
    "If the context does not contain enough information, say so clearly. "
    "Cite relevant article or section numbers when available. "
    "Keep answers concise and actionable."
)

API_NOTICE = (
    "This application is running on a free tier. "
    "For extended access, please contact Priyanka."
)

RATE_LIMIT_MSG = (
    "The free tier limit has been reached. "
    "Access will be restored at 12:00 AM Pacific Time (PT). "
    "For more access, please contact Priyanka."
)

app = FastAPI(
    title="Compliance Policy AI",
    description="RAG-powered API for querying regulatory and compliance documents.",
    version="1.0.0",
)

# CORS - allow your Azure Static Web App to call this API
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "*").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=False if "*" in ALLOWED_ORIGINS else True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ChatMessage(BaseModel):
    role: str  # "user" or "assistant"
    content: str


class QuestionRequest(BaseModel):
    question: str
    regulation: Optional[str] = None
    chat_history: Optional[list[ChatMessage]] = None


@app.get("/health")
def health():
    return {"status": "ok", "notice": API_NOTICE}


@app.get("/debug-config")
def debug_config():
    return {
        "chroma_db_path": CHROMA_DB_PATH,
        "regulations": list(REGULATION_COLLECTIONS.keys()),
        "default_regulation": DEFAULT_REGULATION,
        "ai_provider": AI_PROVIDER,
        "google_key_present": bool(os.getenv("GOOGLE_API_KEY")),
        "azure_key_present": bool(os.getenv("AZURE_OPENAI_API_KEY")),
    }


@app.get("/usage")
def usage():
    """Current API usage stats against free tier limits."""
    return tracker.get_usage()


@app.get("/usage/history")
def usage_history(days: int = 30):
    """Historical daily usage for trend charts."""
    days = max(1, min(days, 90))
    return tracker.get_history(days=days)


@app.get("/status")
def status():
    """Lightweight status for UI status bar / model indicator."""
    from usage_tracker import MODEL_CHAIN
    u = tracker.get_usage()
    active = u["active_model"]
    active_info = u["models"][active]
    return {
        "active_model": active,
        "model_tier": active_info["tier"],
        "fallback_available": any(
            m["name"] != active and u["models"][m["name"]]["daily_requests"]["remaining"] > 0
            for m in MODEL_CHAIN
        ),
        "requests_used": u["summary"]["total_requests"],
        "requests_remaining": u["summary"]["total_remaining"],
        "quota_percent": u["summary"]["percent_used"],
        "models": [
            {
                "name": m["name"],
                "tier": m["tier"],
                "active": m["name"] == active,
                "requests_used": u["models"][m["name"]]["daily_requests"]["used"],
                "requests_limit": u["models"][m["name"]]["daily_requests"]["limit"],
            }
            for m in MODEL_CHAIN
        ],
    }


@app.get("/regulations")
def regulations():
    """List available regulations and the default."""
    return {
        "regulations": list(REGULATION_COLLECTIONS.keys()),
        "default": DEFAULT_REGULATION,
    }


@app.post("/ask")
def ask(request: QuestionRequest):
    if not request.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty.")

    if not os.path.exists(CHROMA_DB_PATH):
        raise HTTPException(status_code=503, detail="Vector DB not found. Run scripts/ingest.py first.")

    # Determine which regulation collection to query
    regulation = (request.regulation or DEFAULT_REGULATION).lower()
    if regulation not in REGULATION_COLLECTIONS:
        raise HTTPException(status_code=400, detail=f"Unknown regulation: {regulation}. Available: {', '.join(REGULATION_COLLECTIONS.keys())}")
    collection_name = REGULATION_COLLECTIONS[regulation]

    # Setup LLM and embeddings based on AI_PROVIDER
    if AI_PROVIDER == "azure":
        from llama_index.embeddings.azure_openai import AzureOpenAIEmbedding
        from llama_index.llms.azure_openai import AzureOpenAI
        LlamaSettings.embed_model = AzureOpenAIEmbedding(
            deployment_name=os.getenv("AZURE_OPENAI_EMBED_DEPLOYMENT"),
            azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
            api_key=os.getenv("AZURE_OPENAI_API_KEY"),
            api_version=os.getenv("AZURE_API_VERSION", "2024-02-15-preview"),
        )
        LlamaSettings.llm = AzureOpenAI(
            deployment_name=os.getenv("AZURE_OPENAI_DEPLOYMENT"),
            azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
            api_key=os.getenv("AZURE_OPENAI_API_KEY"),
            api_version=os.getenv("AZURE_API_VERSION", "2024-02-15-preview"),
            system_prompt=SYSTEM_PROMPT,
        )
    else:
        from llama_index.embeddings.google_genai import GoogleGenAIEmbedding
        from llama_index.llms.google_genai import GoogleGenAI

        active_model = tracker.get_active_model()

        LlamaSettings.embed_model = GoogleGenAIEmbedding(
            model_name="gemini-embedding-001",
            api_key=os.getenv("GOOGLE_API_KEY"),
        )
        LlamaSettings.llm = GoogleGenAI(
            model=active_model,
            api_key=os.getenv("GOOGLE_API_KEY"),
            system_prompt=SYSTEM_PROMPT,
        )

    # Load vector store for selected regulation
    chroma_client = chromadb.PersistentClient(path=CHROMA_DB_PATH)
    chroma_collection = chroma_client.get_collection(collection_name)
    vector_store = ChromaVectorStore(chroma_collection=chroma_collection)

    # Build context-aware query if chat history is provided
    query_text = request.question
    if request.chat_history:
        recent = request.chat_history[-(MAX_HISTORY_TURNS * 2):]
        context_lines = []
        for msg in recent:
            prefix = "User" if msg.role == "user" else "Assistant"
            context_lines.append(f"{prefix}: {msg.content[:500]}")
        query_text = (
            "Previous conversation:\n"
            + "\n".join(context_lines)
            + f"\n\nCurrent question: {request.question}"
        )

    # Query with automatic model fallback on rate limit
    index = VectorStoreIndex.from_vector_store(vector_store)
    query_engine = index.as_query_engine(similarity_top_k=TOP_K)

    used_model = active_model if AI_PROVIDER != "azure" else "azure-openai"
    fallback_used = False

    try:
        response = query_engine.query(query_text)
    except Exception as e:
        err_str = str(e).lower()
        is_rate_limit = "429" in str(e) or "quota" in err_str or ("rate" in err_str and "limit" in err_str)

        # Try fallback to next model if rate-limited and using Gemini
        if is_rate_limit and AI_PROVIDER != "azure":
            from llama_index.llms.google_genai import GoogleGenAI as _GoogleGenAI
            from usage_tracker import MODEL_CHAIN

            tracker.record_error()
            tracker.exhaust_model(used_model)  # Don't retry this model today
            # Find next model after the one that failed
            fallback_model = None
            found_current = False
            for m in MODEL_CHAIN:
                if m["name"] == used_model:
                    found_current = True
                    continue
                if found_current:
                    fallback_model = m["name"]
                    break

            if fallback_model:
                tracker.record_fallback()
                LlamaSettings.llm = _GoogleGenAI(
                    model=fallback_model,
                    api_key=os.getenv("GOOGLE_API_KEY"),
                    system_prompt=SYSTEM_PROMPT,
                )
                used_model = fallback_model
                fallback_used = True
                query_engine = index.as_query_engine(similarity_top_k=TOP_K)
                try:
                    response = query_engine.query(query_text)
                except Exception as e2:
                    tracker.record_error()
                    tracker.exhaust_model(fallback_model)
                    raise HTTPException(status_code=429, detail=RATE_LIMIT_MSG)
            else:
                raise HTTPException(status_code=429, detail=RATE_LIMIT_MSG)
        else:
            tracker.record_error()
            if is_rate_limit:
                raise HTTPException(status_code=429, detail=RATE_LIMIT_MSG)
            raise HTTPException(status_code=500, detail=f"Query failed: {str(e)}")

    answer_text = str(response)

    # Estimate tokens for tracking
    input_tokens = estimate_tokens(query_text) + sum(
        estimate_tokens(node.node.get_content()) for node in response.source_nodes
    )
    output_tokens = estimate_tokens(answer_text)
    tracker.record_request(model=used_model, input_tokens=input_tokens, output_tokens=output_tokens)

    # Format sources
    sources = []
    for node in response.source_nodes:
        sources.append({
            "text": node.node.get_content()[:300],
            "score": round(node.score, 4) if node.score else None,
            "metadata": node.node.metadata,
        })

    usage = tracker.get_usage()

    return {
        "question": request.question,
        "regulation": regulation,
        "answer": answer_text,
        "model_used": used_model,
        "fallback_used": fallback_used,
        "sources": sources,
        "usage": {
            "requests_today": usage["summary"]["total_requests"],
            "requests_remaining": usage["summary"]["total_remaining"],
            "percent_used": usage["summary"]["percent_used"],
            "active_model": usage["active_model"],
        },
        "notice": API_NOTICE,
    }
