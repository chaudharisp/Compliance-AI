# Integrating Compliance Policy AI with Azure Static Web App

Copy this guide into your Azure Static Web App repository.
It explains how to connect your frontend to the backend API deployed on Google Cloud Run.


## Your Setup

```
Azure Static Web App (frontend)          Google Cloud Run (backend)
┌─────────────────────────┐              ┌─────────────────────────┐
│  Your Website            │  ──POST──>  │  Compliance Policy AI   │
│  HTML / CSS / JS         │  <──JSON──  │  FastAPI + ChromaDB     │
│  *.azurestaticapps.net   │             │  *.run.app              │
└─────────────────────────┘              └─────────────────────────┘
```


## Step 1: Set the Backend URL

In your frontend project, create or update a config file:

```javascript
// src/config.js
const config = {
  API_BASE_URL: "https://compliance-policy-ai-abc123-uc.a.run.app",
  // Replace with your actual Google Cloud Run URL
};

export default config;
```


## Step 2: Create the API Service

Add this file to your frontend project:

```javascript
// src/services/complianceApi.js

import config from "../config.js";

const API_URL = config.API_BASE_URL;

/**
 * Ask a compliance question to the RAG backend.
 * @param {string} question - The user's question
 * @returns {Promise<object>} - { question, answer, sources, notice }
 */
export async function askQuestion(question) {
  const response = await fetch(`${API_URL}/ask`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ question }),
  });

  if (response.status === 429) {
    // Free tier limit reached
    const error = await response.json();
    throw new Error(error.detail || "Rate limit reached. Please try again later.");
  }

  if (!response.ok) {
    throw new Error(`API error: ${response.status}`);
  }

  return response.json();
}

/**
 * Check if the backend is running.
 * @returns {Promise<object>} - { status, notice }
 */
export async function checkHealth() {
  const response = await fetch(`${API_URL}/health`);
  return response.json();
}
```


## Step 3: Add the Search UI Component

Add this to your website's HTML (or integrate into your existing page):

```html
<!-- compliance-search.html -->
<!-- Add this wherever you want the search box to appear -->

<div id="compliance-search" style="max-width: 700px; margin: 40px auto; font-family: Arial, sans-serif;">

  <h2>Compliance Policy Assistant</h2>
  <p style="color: #666;">Ask questions about GDPR, HIPAA, and other regulations.</p>

  <div style="display: flex; gap: 8px; margin-bottom: 20px;">
    <input
      type="text"
      id="question-input"
      placeholder="e.g. What are the data breach notification requirements?"
      style="flex: 1; padding: 12px; border: 1px solid #ddd; border-radius: 6px; font-size: 14px;"
    />
    <button
      id="ask-btn"
      onclick="submitQuestion()"
      style="padding: 12px 24px; background: #2a9d8f; color: white; border: none; border-radius: 6px; cursor: pointer; font-size: 14px;"
    >
      Ask
    </button>
  </div>

  <div id="loading" style="display: none; color: #888;">
    Searching regulations...
  </div>

  <div id="answer-box" style="display: none; background: #f8f9fa; padding: 20px; border-radius: 8px; border-left: 4px solid #2a9d8f;">
    <h3 style="margin-top: 0;">Answer</h3>
    <p id="answer-text"></p>

    <details style="margin-top: 16px;">
      <summary style="cursor: pointer; color: #457b9d; font-weight: bold;">Sources</summary>
      <div id="sources-list" style="margin-top: 10px;"></div>
    </details>
  </div>

  <div id="error-box" style="display: none; background: #fff3f3; padding: 16px; border-radius: 8px; border-left: 4px solid #e63946; color: #c0392b;">
  </div>

  <p id="notice-text" style="font-size: 12px; color: #999; margin-top: 12px;"></p>

</div>

<script>
  // ===== CONFIGURATION =====
  // Replace with your actual Google Cloud Run URL
  const API_URL = "https://compliance-policy-ai-abc123-uc.a.run.app";
  // ==========================

  async function submitQuestion() {
    const input = document.getElementById("question-input");
    const question = input.value.trim();
    if (!question) return;

    const loading = document.getElementById("loading");
    const answerBox = document.getElementById("answer-box");
    const errorBox = document.getElementById("error-box");

    loading.style.display = "block";
    answerBox.style.display = "none";
    errorBox.style.display = "none";

    try {
      const response = await fetch(`${API_URL}/ask`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question }),
      });

      if (response.status === 429) {
        const err = await response.json();
        throw new Error(err.detail || "Rate limit reached. Please try again later.");
      }

      if (!response.ok) {
        throw new Error("Something went wrong. Please try again.");
      }

      const data = await response.json();

      // Show answer
      document.getElementById("answer-text").textContent = data.answer;

      // Show sources
      const sourcesList = document.getElementById("sources-list");
      sourcesList.innerHTML = "";
      if (data.sources && data.sources.length > 0) {
        data.sources.forEach((src, i) => {
          const div = document.createElement("div");
          div.style.cssText = "padding: 10px; margin: 6px 0; background: white; border-radius: 4px; border: 1px solid #eee; font-size: 13px;";
          div.innerHTML = `
            <strong>Source ${i + 1}</strong>
            ${src.score ? `<span style="color: #2a9d8f;"> (relevance: ${(src.score * 100).toFixed(1)}%)</span>` : ""}
            <br/>
            <span style="color: #555;">${src.text}</span>
          `;
          sourcesList.appendChild(div);
        });
      }

      // Show notice
      if (data.notice) {
        document.getElementById("notice-text").textContent = data.notice;
      }

      answerBox.style.display = "block";

    } catch (err) {
      errorBox.textContent = err.message;
      errorBox.style.display = "block";
    } finally {
      loading.style.display = "none";
    }
  }

  // Allow Enter key to submit
  document.getElementById("question-input").addEventListener("keypress", function (e) {
    if (e.key === "Enter") submitQuestion();
  });
</script>
```


## Step 4: Deploy to Azure Static Web App

If you already have an Azure Static Web App set up:

1. Add the HTML/JS files above to your repo
2. Push to your connected branch:
```bash
git add .
git commit -m "Add compliance search integration"
git push
```
3. Azure will auto-deploy via GitHub Actions


## Step 5: Update Backend CORS

Make sure the Google Cloud Run backend allows your Azure domain.
Run this once (replace with your actual URL):

```bash
gcloud run services update compliance-policy-ai \
  --region us-central1 \
  --update-env-vars="ALLOWED_ORIGINS=https://your-app.azurestaticapps.net"
```


## Testing the Integration

1. Open your Azure Static Web App in a browser
2. Navigate to the page with the search component
3. Type: "What is the right to erasure under GDPR?"
4. You should see a grounded answer with article citations

If you see a CORS error in the browser console:
- Double check the `ALLOWED_ORIGINS` value on Cloud Run matches your exact Azure URL
- No trailing slash
- Must include `https://`


## Sample Questions to Test

| Question | Expected Source |
|----------|---------------|
| What are the GDPR data breach notification rules? | Article 33, 34 |
| When is consent required for data processing? | Article 6, 7 |
| What is the right to be forgotten? | Article 17 |
| What are the penalties for GDPR violations? | Article 83 |
| What is data protection by design? | Article 25 |
| How long can personal data be stored? | Article 5(1)(e) |


## Environment Summary

| Component | Where | URL |
|-----------|-------|-----|
| Frontend | Azure Static Web App | `https://your-app.azurestaticapps.net` |
| Backend API | Google Cloud Run | `https://compliance-policy-ai-xxx.a.run.app` |
| Swagger Docs | Google Cloud Run | `https://compliance-policy-ai-xxx.a.run.app/docs` |
| AI Provider | Google Gemini | Free tier (1,500 req/day) |
