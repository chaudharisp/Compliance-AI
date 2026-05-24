# Compliance Policy AI - Project Plan

## Overview
RAG-based AI assistant for querying compliance and regulatory documents (GDPR, HIPAA, SOX).
Built with FastAPI, LlamaIndex, ChromaDB, and OpenAI.

## Project Structure
```
compliance-policy-ai/
├── backend/
│   ├── data/
│   │   └── gdpr_full_text.txt
│   ├── scripts/
│   │   ├── ingest.py
│   │   ├── debug_chunks.py
│   │   └── debug_embeddings.py
│   ├── storage/
│   │   └── chroma_db/
│   ├── .env
│   ├── .gitignore
│   ├── main.py
│   └── requirements.txt
├── PLAN.md
└── README.md
```

## Steps

### Step 1: Project Structure & Config (DONE)
- [x] requirements.txt with all dependencies
- [x] .env file for OpenAI API key
- [x] .gitignore to exclude secrets and storage

### Step 2: Ingestion Script (DONE)
- [x] scripts/ingest.py - loads PDFs/TXT from data/, chunks them, embeds, stores in ChromaDB

### Step 3: Debug Scripts (DONE)
- [x] scripts/debug_chunks.py - inspect stored text chunks
- [x] scripts/debug_embeddings.py - inspect stored embeddings

### Step 4: FastAPI Backend (DONE)
- [x] main.py with endpoints:
  - GET /health - server status
  - GET /debug-config - current config
  - POST /ask - query the RAG pipeline

### Step 5: Sample GDPR Data (TODO)
- [ ] Add GDPR regulation text to backend/data/
- [ ] Source: publicly available GDPR articles (gdpr-info.eu)

### Step 6: Install Dependencies & Test (TODO)
- [ ] Create virtual environment
- [ ] pip install -r requirements.txt
- [ ] Add OpenAI API key to .env
- [ ] Run: python scripts/ingest.py
- [ ] Run: uvicorn main:app --reload
- [ ] Test: POST /ask with sample question

### Step 7: README (TODO)
- [ ] Project description, setup instructions, API docs

## Tech Stack
- Python 3.11
- FastAPI
- LlamaIndex
- OpenAI Embeddings + LLM
- ChromaDB
- PyPDF

## API Endpoints
| Method | Endpoint      | Description                        |
|--------|---------------|------------------------------------|
| GET    | /health       | Server health check                |
| GET    | /debug-config | Current backend config             |
| POST   | /ask          | Ask a compliance question (RAG)    |

## Sample Queries
- "What is the right to erasure under GDPR?"
- "What are the data breach notification requirements?"
- "When is consent required for data processing?"
- "What are the penalties for GDPR non-compliance?"
