# Deploying Compliance Policy AI on Google Cloud Run

Step-by-step guide to deploy the FastAPI backend on Google Cloud Run (free tier).

## Architecture

- **Backend**: FastAPI + LlamaIndex RAG pipeline → Google Cloud Run
- **Frontend**: Static HTML/CSS/JS → Azure Static Web Apps
- **LLM**: Gemini API (3-model fallback: Pro → Flash → Flash-Lite)
- **Vector DB**: ChromaDB (pre-built, baked into Docker image)
- **Regulations**: HIPAA + GDPR


## Prerequisites

- Google account (Gmail)
- Google Cloud CLI installed: https://cloud.google.com/sdk/docs/install
- Your `GOOGLE_API_KEY` from https://aistudio.google.com/apikey
- ChromaDB already ingested locally (both HIPAA and GDPR collections)


## Step 1: Create a Google Cloud Project

1. Go to https://console.cloud.google.com
2. Click **Select a project** → **New Project**
3. Name it: `compliance-policy-ai`
4. Click **Create**
5. Note your **Project ID** (e.g. `compliance-policy-ai-12345`)


## Step 2: Enable Required APIs

```bash
gcloud auth login
gcloud config set project YOUR_PROJECT_ID

gcloud services enable run.googleapis.com
gcloud services enable cloudbuild.googleapis.com
gcloud services enable artifactregistry.googleapis.com
```


## Step 3: Verify Local Setup

Before deploying, make sure your local ChromaDB has both collections:

```bash
cd backend
python -c "import chromadb; c=chromadb.PersistentClient('storage/chroma_db'); print([col.name for col in c.list_collections()])"
```

You should see: `['compliance_docs', 'hipaa_docs']`

If not, run ingestion first:

```bash
python scripts/ingest.py --regulation gdpr
python scripts/ingest.py --regulation hipaa
```


## Step 4: Dockerfile (already created)

The Dockerfile at `backend/Dockerfile` uses Option 1 — the pre-built ChromaDB is
copied into the Docker image. No ingestion runs during build, and no API key is
needed at build time.

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 8080
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
```

The `.dockerignore` excludes `.env`, `.venv`, `tests/`, and usage tracking JSON
files — but includes `storage/chroma_db/` so the vector data ships with the image.


## Step 5: Deploy to Cloud Run

From the `backend/` directory:

```bash
cd backend

gcloud run deploy compliance-policy-ai \
  --source . \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars="AI_PROVIDER=gemini,GOOGLE_API_KEY=YOUR_KEY_HERE,ALLOWED_ORIGINS=*" \
  --memory=1Gi \
  --cpu=1 \
  --min-instances=0 \
  --max-instances=1
```

When prompted:
- **Allow unauthenticated invocations?** → Yes
- **Region?** → us-central1

> **Note**: `ALLOWED_ORIGINS=*` is fine initially. Once your Azure frontend is live,
> update it to the exact URL (Step 8).


## Step 6: Verify Deployment

You'll get a URL like: `https://compliance-policy-ai-abc123-uc.a.run.app`

```bash
# Health check
curl https://YOUR_CLOUD_RUN_URL/health

# Test HIPAA question
curl -X POST https://YOUR_CLOUD_RUN_URL/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "What is Protected Health Information?", "regulation": "hipaa"}'

# Test GDPR question
curl -X POST https://YOUR_CLOUD_RUN_URL/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "What are the GDPR breach notification rules?", "regulation": "gdpr"}'

# Check usage tracking
curl https://YOUR_CLOUD_RUN_URL/usage
```

Open Swagger docs: `https://YOUR_CLOUD_RUN_URL/docs`


## Step 7: Update Frontend API Base URL

In the frontend, `app.js` and `dashboard.html` already detect production vs local:

```javascript
const API_BASE = window.location.hostname === "localhost"
  ? "http://127.0.0.1:8000"
  : "/api";
```

For Azure Static Web Apps, you'll configure a proxy route so `/api/*` forwards to
your Cloud Run URL. See `INTEGRATE_AZURE_STATIC_APP.md` for details.

Alternatively, you can hardcode the Cloud Run URL directly:

```javascript
const API_BASE = window.location.hostname === "localhost"
  ? "http://127.0.0.1:8000"
  : "https://compliance-policy-ai-abc123-uc.a.run.app";
```


## Step 8: Lock Down CORS

Once your Azure Static Web App is live, restrict CORS to just that origin:

```bash
gcloud run services update compliance-policy-ai \
  --region us-central1 \
  --update-env-vars="ALLOWED_ORIGINS=https://your-app.azurestaticapps.net"
```


## Free Tier Limits

| Resource | Free Allowance |
|----------|---------------|
| Cloud Run requests | 2 million/month |
| CPU | 180,000 vCPU-seconds/month |
| Memory | 360,000 GiB-seconds/month |
| Networking | 1 GB outbound/month |
| Builds | 120 build-minutes/day |
| Gemini API (combined) | 4,525 requests/day (25 Pro + 1,500 Flash + 3,000 Flash-Lite) |

With `min-instances=0`, Cloud Run scales to zero when idle — you only use resources when someone sends a request.


## Redeploying After Changes

```bash
cd backend
gcloud run deploy compliance-policy-ai --source . --region us-central1
```

If you updated the regulatory documents, re-run ingestion locally first:

```bash
python scripts/ingest.py --regulation hipaa
python scripts/ingest.py --regulation gdpr
gcloud run deploy compliance-policy-ai --source . --region us-central1
```


## Usage Tracking & Persistence

Usage stats (`usage_stats.json`) and history (`usage_history.json`) are stored on
the container's local filesystem. They persist as long as the container lives, but
reset if Cloud Run recycles the container.

For persistent history across container restarts, add a Cloud Storage volume mount:

```bash
# Create a bucket (one-time)
gsutil mb gs://compliance-policy-ai-storage

# Redeploy with volume mount
gcloud run services update compliance-policy-ai \
  --region us-central1 \
  --add-volume=name=storage,type=cloud-storage,bucket=compliance-policy-ai-storage \
  --add-volume-mount=volume=storage,mount-path=/app/storage
```

No code changes needed — the app reads/writes to `/app/storage/` as normal.


## Troubleshooting

**CORS errors from frontend:**
- Verify `ALLOWED_ORIGINS` matches your exact Azure URL (include `https://`, no trailing slash)
- Check browser dev tools Network tab for the preflight OPTIONS request

**Cold start slow (~10-15s):**
- Normal for free tier with `min-instances=0`
- Set `--min-instances=1` to keep warm (costs ~$5/month)

**ChromaDB collection not found:**
- Verify `storage/chroma_db/` exists locally before deploying
- Check `.dockerignore` isn't excluding it

**View logs:**
```bash
gcloud run services logs read compliance-policy-ai --region us-central1 --limit=50
```
