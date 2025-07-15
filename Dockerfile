# Multi-stage build for YouTube Video Summarizer
FROM python:3.11-slim as base

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV DEBIAN_FRONTEND=noninteractive

# Install system dependencies
RUN apt-get update && apt-get install -y \
    ffmpeg \
    curl \
    wget \
    git \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Create app directory
WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p /app/temp /app/logs

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Create startup script
RUN echo '#!/bin/bash\n\
# Wait for external Ollama service to be ready\n\
echo "Waiting for external Ollama service..."\n\
OLLAMA_HOST=${OLLAMA_HOST:-ollama:11434}\n\
echo "Checking Ollama at $OLLAMA_HOST"\n\
\n\
# Wait for Ollama to be available\n\
for i in {1..30}; do\n\
    if curl -s http://$OLLAMA_HOST/api/tags > /dev/null 2>&1; then\n\
        echo "Ollama service is ready!"\n\
        break\n\
    fi\n\
    echo "Waiting for Ollama... ($i/30)"\n\
    sleep 5\n\
done\n\
\n\
# Start the FastAPI application\n\
echo "Starting YouTube Summarizer..."\n\
cd /app\n\
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000\n\
' > /app/start.sh && chmod +x /app/start.sh

# Run the startup script
CMD ["/app/start.sh"]
