# Multi-stage build for YouTube Video Summarizer with CPU support
FROM python:3.11-slim as base

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV DEBIAN_FRONTEND=noninteractive
ENV PIP_DEFAULT_TIMEOUT=300
ENV PIP_RETRIES=3
ENV PIP_TIMEOUT=300

# Install system dependencies including Chrome and computer use tools
RUN apt-get update && apt-get install -y \
    ffmpeg \
    curl \
    wget \
    git \
    build-essential \
    gnupg \
    ca-certificates \
    unzip \
    xvfb \
    xauth \
    x11-apps \
    x11-utils \
    x11-xserver-utils \
    scrot \
    xdotool \
    fluxbox \
    dbus-x11 \
    libgtk-3-0 \
    libxss1 \
    libgconf-2-4 \
    libnss3 \
    libxrandr2 \
    libasound2 \
    libpangocairo-1.0-0 \
    libatk1.0-0 \
    libcairo-gobject2 \
    libgtk-3-0 \
    libgdk-pixbuf2.0-0 \
    libxcomposite1 \
    libxcursor1 \
    libxdamage1 \
    libxi6 \
    libxtst6 \
    libnss3 \
    libcups2 \
    libxss1 \
    libxrandr2 \
    libasound2 \
    libpangocairo-1.0-0 \
    libatk1.0-0 \
    libcairo-gobject2 \
    libdrm2 \
    libxkbcommon0 \
    libatspi2.0-0 \
    && wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add - \
    && echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google.list \
    && apt-get update \
    && apt-get install -y google-chrome-stable \
    && rm -rf /var/lib/apt/lists/*

# Install chromedriver using the new Chrome for Testing API
RUN CHROME_VERSION=$(google-chrome --version | cut -d " " -f3) \
    && echo "Chrome version: $CHROME_VERSION" \
    && CHROMEDRIVER_VERSION=$(curl -s "https://googlechromelabs.github.io/chrome-for-testing/LATEST_RELEASE_${CHROME_VERSION%%.*}" 2>/dev/null || echo "131.0.6778.85") \
    && echo "ChromeDriver version: $CHROMEDRIVER_VERSION" \
    && wget -O /tmp/chromedriver.zip "https://storage.googleapis.com/chrome-for-testing-public/${CHROMEDRIVER_VERSION}/linux64/chromedriver-linux64.zip" \
    && unzip /tmp/chromedriver.zip -d /tmp \
    && mv /tmp/chromedriver-linux64/chromedriver /usr/local/bin/chromedriver \
    && chmod +x /usr/local/bin/chromedriver \
    && rm -rf /tmp/chromedriver.zip /tmp/chromedriver-linux64 \
    && chromedriver --version

# Create app directory
WORKDIR /app

# Upgrade pip and install build tools
RUN pip install --no-cache-dir --upgrade pip setuptools wheel

# Copy requirements files first for better caching
COPY requirements.txt ./

# Install PyTorch with CUDA support first, fallback to CPU if needed
RUN pip install --no-cache-dir --timeout=300 --retries=3 \
    torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118 || \
    pip install --no-cache-dir --timeout=300 --retries=3 \
    torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu

# Install remaining dependencies
RUN pip install --no-cache-dir --timeout=300 --retries=3 -r requirements.txt

# Create GPU detection script
RUN echo 'import torch\n\
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
    os.environ["GPU_AVAILABLE"] = str(gpu_available)\n\
    print(f"GPU_AVAILABLE={gpu_available}")' > /app/gpu_detect.py

# Copy application code
COPY . .

# Validate static and templates directories are properly copied
RUN echo "Validating static and templates directories..." && \
    ls -la /app/static || (echo "ERROR: Static directory missing!" && exit 1) && \
    ls -la /app/templates || (echo "ERROR: Templates directory missing!" && exit 1) && \
    ls -la /app/static/css/style.css || (echo "ERROR: CSS file missing!" && exit 1) && \
    ls -la /app/static/js/app.js || (echo "ERROR: JS file missing!" && exit 1) && \
    ls -la /app/templates/index.html || (echo "ERROR: HTML template missing!" && exit 1) && \
    echo "All static files and templates validated successfully!"

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
# Validate static file serving\n\
echo "Validating static file serving..."\n\
cd /app\n\
echo "Current working directory: $(pwd)"\n\
echo "Listing contents of /app:"\n\
ls -la /app/\n\
echo "Checking static directory:"\n\
ls -la /app/static/ || echo "Static directory not found"\n\
echo "Checking templates directory:"\n\
ls -la /app/templates/ || echo "Templates directory not found"\n\
echo "Checking app directory:"\n\
ls -la /app/app/ || echo "App directory not found"\n\
\n\
# Test that Python can access the static files\n\
echo "Testing Python access to static files..."\n\
python -c "import os; print('"'"'Static files accessible:'"'"', os.path.exists('"'"'/app/static/css/style.css'"'"'), os.path.exists('"'"'/app/static/js/app.js'"'"'))"\n\
python -c "import os; print('"'"'Templates accessible:'"'"', os.path.exists('"'"'/app/templates/index.html'"'"'))"\n\
\n\
# Start the FastAPI application\n\
echo "Starting YouTube Summarizer..."\n\
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000\n\
' > /app/start.sh && chmod +x /app/start.sh

# Run the startup script
CMD ["/app/start.sh"]
