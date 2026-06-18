FROM python:3.11-slim

# Install system dependencies needed for FAISS, SQLite, and Python compilation
RUN apt-get update && apt-get install -y \
    build-essential \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Pre-cache/download SentenceTransformer model during build to minimize boot time
RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')"

# Copy backend source code
COPY . /app/backend

# Set Python Path
ENV PYTHONPATH=/app

# Expose server port
EXPOSE 8000

# Start FastAPI server binding to all interfaces
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
