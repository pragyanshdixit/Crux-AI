# Crux AI Production Dockerfile
FROM python:3.11-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PORT=8000

# Install system dependencies: FFmpeg (audio conversion) and Node.js (YouTube challenge solving)
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    nodejs \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Install Python dependencies first for efficient layer caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY . .

# Create required runtime directories
RUN mkdir -p /app/downloads /app/chroma_db

# Expose server port
EXPOSE 8000

# Start FastAPI application with dynamic port binding
CMD uvicorn app:app --host 0.0.0.0 --port ${PORT:-8000}
