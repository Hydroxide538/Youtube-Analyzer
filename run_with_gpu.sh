#!/bin/bash

# YouTube Analyzer GPU Runner Script
# This script builds and runs the YouTube Analyzer with GPU support

echo "YouTube Analyzer - GPU Runner"
echo "=============================="

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker first."
    exit 1
fi

# Check if NVIDIA GPU is available
if command -v nvidia-smi &> /dev/null; then
    echo "✅ NVIDIA GPU detected"
    nvidia-smi --query-gpu=name,memory.total --format=csv,noheader,nounits
    GPU_AVAILABLE=true
else
    echo "ℹ️  No NVIDIA GPU detected, will use CPU mode"
    GPU_AVAILABLE=false
fi

# Build the Docker image
echo ""
echo "🔨 Building Docker image..."
docker build -t youtube-summarizer .

if [ $? -ne 0 ]; then
    echo "❌ Docker build failed"
    exit 1
fi

# Stop and remove existing container if it exists
echo ""
echo "🧹 Cleaning up existing container..."
docker stop youtube-summarizer 2>/dev/null || true
docker rm youtube-summarizer 2>/dev/null || true

# Run the container with appropriate GPU settings
echo ""
echo "🚀 Starting YouTube Analyzer..."

if [ "$GPU_AVAILABLE" = true ]; then
    echo "Using GPU acceleration..."
    docker run -d \
        --name youtube-summarizer \
        --gpus all \
        -p 8000:8000 \
        -e PYTHONPATH=/app \
        -e OLLAMA_HOST=host.docker.internal:11434 \
        -e NVIDIA_VISIBLE_DEVICES=all \
        -e NVIDIA_DRIVER_CAPABILITIES=compute,utility \
        --memory=4g \
        --add-host host.docker.internal:host-gateway \
        --restart unless-stopped \
        youtube-summarizer
else
    echo "Using CPU mode..."
    docker run -d \
        --name youtube-summarizer \
        -p 8000:8000 \
        -e PYTHONPATH=/app \
        -e OLLAMA_HOST=host.docker.internal:11434 \
        -e FORCE_CPU=true \
        --memory=4g \
        --add-host host.docker.internal:host-gateway \
        --restart unless-stopped \
        youtube-summarizer
fi

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ YouTube Analyzer started successfully!"
    echo "🌐 Access the web interface at: http://localhost:8000"
    echo ""
    echo "📋 Useful commands:"
    echo "  View logs: docker logs -f youtube-summarizer"
    echo "  Stop container: docker stop youtube-summarizer"
    echo "  Remove container: docker rm youtube-summarizer"
    echo ""
    echo "🔍 Checking container status..."
    sleep 3
    docker ps --filter name=youtube-summarizer --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
else
    echo "❌ Failed to start YouTube Analyzer"
    exit 1
fi
