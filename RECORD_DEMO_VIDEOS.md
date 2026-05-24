# How to Record and Add Demo Videos to GitHub README

Step-by-step guide to create those professional demo videos you see on GitHub repos.


## What You Need

- Windows 11 built-in Screen Recorder (free, already installed)
- Your project running locally
- A GitHub repo


## PART 1: Record the Videos

You'll record 3 short clips (30-60 seconds each):


### Video 1: Ingestion Pipeline

**What to show:** Documents being loaded, chunked, embedded, and stored.

1. Open Terminal in VS Code
2. Start Windows screen recording:
   - Press `Win + Shift + R` (or open Snipping Tool → Record)
   - Select the VS Code window area
   - Click Record
3. Run these commands slowly (pause 2-3 seconds between each):
   ```
   cd backend
   python scripts/ingest.py
   ```
4. Wait for output showing:
   - "Found X document(s)"
   - "Created X chunks"
   - "Generating embeddings..."
   - "Successfully indexed"
   - "Ingestion complete"
5. Stop recording → saves as MP4 to your Videos folder


### Video 2: Starting the Server + Swagger Demo

**What to show:** Server starting, Swagger UI, asking a question.

1. Start recording
2. Run:
   ```
   uvicorn main:app --reload
   ```
3. Wait for "Uvicorn running on http://127.0.0.1:8000"
4. Open browser → go to `http://127.0.0.1:8000/docs`
5. Show the Swagger UI (pause 2 seconds so viewer can read)
6. Click on `POST /ask` → Click "Try it out"
7. Type this question:
   ```json
   {
     "question": "What are the data breach notification requirements under GDPR?"
   }
   ```
8. Click "Execute"
9. Scroll down to show the response (answer + sources)
10. Pause 3 seconds on the response
11. Stop recording


### Video 3: Multiple Questions Demo (optional)

**What to show:** Different types of questions working.

1. Start recording
2. In Swagger, ask these one by one (pause on each response):
   - "What is the right to be forgotten?"
   - "When is consent required for data processing?"
   - "What are the penalties for GDPR violations?"
3. Stop recording


## PART 2: Upload Videos to GitHub

GitHub hosts your videos for free. Here's how:

### Step 1: Go to GitHub Issues

1. Open your repo on GitHub
2. Click the **Issues** tab
3. Click **New Issue**

### Step 2: Upload the Video

1. In the issue text box, type: "Demo videos for README"
2. **Drag and drop** your MP4 file into the text box
3. Wait for upload (you'll see a progress bar)
4. GitHub converts it and gives you a URL like:
   ```
   https://github.com/user-attachments/assets/a1b2c3d4-e5f6-7890-abcd-ef1234567890
   ```
5. **Copy that full URL**
6. Repeat for each video
7. You can close the issue without submitting (or submit it, doesn't matter — the upload URL stays valid either way)

### Step 3: Note Down Your URLs

After uploading all videos, you'll have something like:
```
Video 1 (Ingestion):  https://github.com/user-attachments/assets/xxxx1
Video 2 (Swagger):    https://github.com/user-attachments/assets/xxxx2
Video 3 (Questions):  https://github.com/user-attachments/assets/xxxx3
```


## PART 3: Add Videos to README

Add this section to your README.md (replace URLs with your actual ones):

```markdown
## Demo

### Document Ingestion
Loading GDPR documents, chunking, generating embeddings, and storing in ChromaDB:

https://github.com/user-attachments/assets/PASTE_VIDEO_1_URL_HERE

### Querying the API
Asking compliance questions through Swagger UI and getting grounded answers with citations:

https://github.com/user-attachments/assets/PASTE_VIDEO_2_URL_HERE

### Sample Queries
Different types of compliance questions demonstrating the RAG pipeline:

https://github.com/user-attachments/assets/PASTE_VIDEO_3_URL_HERE
```

**Important:** Just paste the raw URL on its own line. Do NOT wrap it in markdown image/link syntax. GitHub auto-embeds it as a video player with play/pause controls.


## PART 4: Push to GitHub

```bash
git add README.md
git commit -m "Add demo videos to README"
git push
```


## Tips for Better Videos

- **Go slow.** Pause 2-3 seconds after each command output so viewers can read.
- **Use a large font.** In VS Code: `Ctrl + =` to zoom in before recording.
- **Clean terminal.** Run `cls` before starting to clear old output.
- **Close distractions.** Hide notifications, close other tabs.
- **Keep it short.** 30-60 seconds per video is ideal.
- **Resolution:** Record at 1080p minimum. GitHub compresses it.


## Recording Alternatives (if Win+Shift+R doesn't work)

| Tool | Free? | How |
|------|-------|-----|
| **Snipping Tool** | Yes (built-in) | Open → Click Record → Select area |
| **Xbox Game Bar** | Yes (built-in) | `Win + G` → Capture → Record |
| **OBS Studio** | Yes | Download from obsproject.com, most control |
| **ShareX** | Yes | Download from getsharex.com, lightweight |


## Checklist

- [ ] Record Video 1: Ingestion pipeline
- [ ] Record Video 2: Swagger UI demo
- [ ] Record Video 3: Multiple queries (optional)
- [ ] Upload all videos to GitHub Issues
- [ ] Copy the URLs
- [ ] Add URLs to README.md
- [ ] Push to GitHub
- [ ] Verify videos play on your repo page
