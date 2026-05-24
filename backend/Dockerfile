FROM python:3.11-slim

WORKDIR /app

# Install dependencies first (cached layer)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code (includes pre-built ChromaDB vector store)
COPY . .

# Expose port (Cloud Run sets PORT env var)
EXPOSE 8080

# Run with production settings
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
