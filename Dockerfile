# Multi-stage build for YouTube Video Summarizer with GPU support
FROM python:3.11-slim as base

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV DEBIAN_FRONTEND=noninteractive
ENV PIP_DEFAULT_TIMEOUT=600
ENV PIP_RETRIES=10
ENV PIP_TIMEOUT=600

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

# Upgrade pip and install build tools
RUN pip install --no-cache-dir --upgrade pip setuptools wheel

# Copy requirements files
COPY requirements.txt requirements.txt.gpu ./

# Create a smart installation script that tries GPU first, then falls back to CPU
RUN echo '#!/bin/bash\n\
set -e\n\
\n\
echo "Attempting to install GPU-enabled PyTorch..."\n\
\n\
# Try to install GPU version first\n\
if pip install --no-cache-dir --timeout=600 --retries=10 torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121; then\n\
    echo "Successfully installed GPU-enabled PyTorch"\n\
    GPU_AVAILABLE=true\n\
else\n\
    echo "GPU installation failed, falling back to CPU version..."\n\
    pip install --no-cache-dir --timeout=600 --retries=10 torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu\n\
    GPU_AVAILABLE=false\n\
fi\n\
\n\
# Install remaining dependencies with extended timeout\n\
echo "Installing remaining dependencies..."\n\
pip install --no-cache-dir --timeout=600 --retries=10 -r requirements.txt\n\
\n\
# Create a runtime script that detects GPU availability\n\
cat > /app/gpu_detect.py << EOF\n\
import torch\n\
import sys\n\
import os\n\
\n\
def detect_gpu():\n\
    try:\n\
        if torch.cuda.is_available():\n\
            device_count = torch.cuda.device_count()\n\
            device_name = torch.cuda.get_device_name(0) if device_count > 0 else "Unknown"\n\
            print(f"GPU acceleration available: {device_name} ({device_count} device(s))")\n\
            return True\n\
        else:\n\
            print("No GPU acceleration available, using CPU")\n\
            return False\n\
    except Exception as e:\n\
        print(f"Error detecting GPU: {e}, falling back to CPU")\n\
        return False\n\
\n\
if __name__ == "__main__":\n\
    gpu_available = detect_gpu()\n\
    # Set environment variable for the application\n\
    os.environ["GPU_AVAILABLE"] = str(gpu_available)\n\
    print(f"GPU_AVAILABLE={gpu_available}")\n\
EOF\n\
\n\
echo "PyTorch installation completed successfully"\n\
' > /app/install_pytorch.sh && chmod +x /app/install_pytorch.sh

# Run the installation script
RUN /app/install_pytorch.sh

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p /app/temp /app/logs

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Create startup script with GPU detection
RUN echo '#!/bin/bash\n\
set -e\n\
\n\
# Detect GPU capabilities\n\
echo "Detecting GPU capabilities..."\n\
python /app/gpu_detect.py\n\
\n\
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
