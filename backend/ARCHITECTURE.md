```mermaid
flowchart TB
    subgraph INGESTION["📥 DOCUMENT INGESTION PIPELINE"]
        direction LR
        A["📄 GDPR / HIPAA\nDocuments\n(PDF / TXT)"] -->|Load| B["✂️ Sentence Splitter\nChunking\n(512 tokens, 50 overlap)"]
        B -->|Chunks| C["🧠 Google Gemini\nEmbeddings\n(embedding-001)"]
        C -->|Vectors| D["🗄️ ChromaDB\nVector Store\n(Persistent)"]
    end

    subgraph QUERY["🔍 QUERY PIPELINE (RAG)"]
        direction LR
        E["👤 User Query\nPOST /ask\n{'question': '...'}"] -->|HTTP| F["⚡ FastAPI\nBackend Server\n(uvicorn)"]
        F -->|Embed query| G["🧠 Google Gemini\nEmbed Query\n(embedding-001)"]
        G -->|Vector search| H["🗄️ ChromaDB\nSimilarity Search\n(Top-K = 5)"]
        H -->|Top chunks| I["🤖 Gemini 1.5 Flash\nLLM Generation\n(grounded answer)"]
        I -->|JSON| J["📋 Response\nanswer + sources\n+ citations"]
    end

    INGESTION ~~~ QUERY

    style INGESTION fill:#1a1a2e,stroke:#e63946,color:#fff
    style QUERY fill:#1a1a2e,stroke:#2a9d8f,color:#fff
    style A fill:#457b9d,stroke:#1d3557,color:#fff
    style B fill:#457b9d,stroke:#1d3557,color:#fff
    style C fill:#e76f51,stroke:#c4452d,color:#fff
    style D fill:#2a9d8f,stroke:#1a6b5f,color:#fff
    style E fill:#264653,stroke:#1a1a2e,color:#fff
    style F fill:#457b9d,stroke:#1d3557,color:#fff
    style G fill:#e76f51,stroke:#c4452d,color:#fff
    style H fill:#2a9d8f,stroke:#1a6b5f,color:#fff
    style I fill:#e76f51,stroke:#c4452d,color:#fff
    style J fill:#264653,stroke:#1a1a2e,color:#fff
```

---

## Tech Stack

| Component | Technology | Purpose |
|-----------|-----------|---------|
| 🐍 Backend | **FastAPI** + uvicorn | REST API server |
| 🧠 Embeddings | **Google Gemini** (embedding-001) | Convert text → vectors |
| 🤖 LLM | **Gemini 1.5 Flash** (free tier) | Generate grounded answers |
| 🗄️ Vector DB | **ChromaDB** (persistent) | Store & search embeddings |
| 📚 Framework | **LlamaIndex** | RAG orchestration |
| 📄 Documents | **GDPR regulation text** | Knowledge base |

---

## How It Works

### Ingestion (one-time setup)
```
scripts/ingest.py
```
1. Load GDPR documents from `data/` folder
2. Split into 512-token chunks with 50-token overlap
3. Generate vector embeddings via Gemini API
4. Store vectors in ChromaDB (persistent on disk)

### Query (runtime)
```
POST http://localhost:8000/ask
{"question": "What are the data breach notification rules?"}
```
1. User sends a natural language question
2. FastAPI receives the request
3. Question is embedded using the same Gemini model
4. ChromaDB finds the 5 most similar regulation chunks
5. Chunks + question are sent to Gemini 1.5 Flash LLM
6. LLM generates a grounded answer with article citations
7. Response returned as JSON with answer + source chunks

---

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/health` | Server health check |
| `GET` | `/debug-config` | Current config details |
| `POST` | `/ask` | Ask a compliance question |
