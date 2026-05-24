# Azure OpenAI – Cost Explainer for Compliance Policy AI

## Why Azure OpenAI?

This project supports **Azure OpenAI** as an alternative AI provider to Gemini.  
Azure OpenAI offers **pay-as-you-go** pricing with no daily quota limits — you only pay for what you use.

---

## Recommended Models for This App

### LLM (Chat / Completion)

| Model              | Input (per 1M tokens) | Output (per 1M tokens) | Best For                        |
|--------------------|----------------------|------------------------|---------------------------------|
| **GPT-4.1-nano**   | $0.10                | $0.40                  | Cheapest option, simple Q&A     |
| **GPT-4o-mini**    | $0.15                | $0.60                  | Best balance of cost & quality  |
| **GPT-4.1-mini**   | $0.40                | $1.60                  | Better reasoning capabilities   |
| **GPT-4o**         | $2.50                | $10.00                 | Full power (overkill for RAG)   |

### Embedding

| Model                      | Price (per 1M tokens) |
|----------------------------|-----------------------|
| **text-embedding-3-small** | $0.02                 |
| **text-embedding-3-large** | $0.13                 |

---

## Estimated Monthly Cost

A typical RAG query in this app uses **~2,000 input tokens** (question + retrieved context) and **~500 output tokens** (answer).

| Daily Usage       | GPT-4.1-nano | GPT-4o-mini | GPT-4.1-mini |
|--------------------|-------------|-------------|--------------|
| 10 queries/day     | ~$0.06/mo   | ~$0.18/mo   | ~$0.50/mo    |
| 100 queries/day    | ~$0.60/mo   | ~$1.80/mo   | ~$5.00/mo    |
| 1,000 queries/day  | ~$6.00/mo   | ~$18.00/mo  | ~$50.00/mo   |

> **For a portfolio/demo project with light usage, expect to spend pennies to a few dollars per month.**

---

## Free Credits

- **New Azure accounts** receive a **$200 free credit** valid for 30 days.
- Azure for Students provides **$100 free credit** (no credit card required).

---

## How to Switch This App to Azure OpenAI

1. Set `AI_PROVIDER=azure` in `backend/.env`
2. Fill in the Azure OpenAI environment variables:
   ```
   AZURE_OPENAI_API_KEY=your-key
   AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
   AZURE_OPENAI_DEPLOYMENT=gpt-4o-mini
   AZURE_OPENAI_EMBED_DEPLOYMENT=text-embedding-3-small
   AZURE_API_VERSION=2024-02-15-preview
   ```
3. Re-run ingestion: `python scripts/ingest.py`
4. Restart the server: `uvicorn main:app --reload`

---

## Gemini (Free Tier) vs Azure OpenAI Comparison

| Feature            | Gemini Free Tier        | Azure OpenAI (Pay-as-you-go) |
|--------------------|------------------------|-------------------------------|
| Cost               | Free                   | Pay per token                 |
| Daily quota        | 1,500 requests/day     | No daily limit                |
| Rate limit         | 15 requests/min        | Varies by tier                |
| Reliability        | Quota resets can block  | Always available              |
| Best for           | Development / demos    | Production / reliable access  |

---

*Pricing as of May 2026. See [Azure OpenAI Pricing](https://azure.microsoft.com/en-us/pricing/details/cognitive-services/openai-service/) for latest rates.*
