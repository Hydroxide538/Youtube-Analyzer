# YouTube Analyzer GPU Runner Script (PowerShell)
# This script builds and runs the YouTube Analyzer with GPU support

Write-Host "YouTube Analyzer - GPU Runner" -ForegroundColor Green
Write-Host "==============================" -ForegroundColor Green

# Check if Docker is running
try {
    docker info | Out-Null
    Write-Host "✅ Docker is running" -ForegroundColor Green
} catch {
    Write-Host "❌ Docker is not running. Please start Docker first." -ForegroundColor Red
    exit 1
}

# Check if NVIDIA GPU is available
$GPU_AVAILABLE = $false
try {
    if (Get-Command nvidia-smi -ErrorAction SilentlyContinue) {
        Write-Host "✅ NVIDIA GPU detected" -ForegroundColor Green
        nvidia-smi --query-gpu=name,memory.total --format=csv,noheader,nounits
        $GPU_AVAILABLE = $true
    } else {
        Write-Host "ℹ️  No NVIDIA GPU detected, will use CPU mode" -ForegroundColor Yellow
    }
} catch {
    Write-Host "ℹ️  No NVIDIA GPU detected, will use CPU mode" -ForegroundColor Yellow
}

# Build the Docker image
Write-Host ""
Write-Host "🔨 Building Docker image..." -ForegroundColor Blue
docker build -t youtube-summarizer .

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Docker build failed" -ForegroundColor Red
    exit 1
}

# Stop and remove existing container if it exists
Write-Host ""
Write-Host "🧹 Cleaning up existing container..." -ForegroundColor Blue
docker stop youtube-summarizer 2>$null
docker rm youtube-summarizer 2>$null

# Run the container with appropriate GPU settings
Write-Host ""
Write-Host "🚀 Starting YouTube Analyzer..." -ForegroundColor Blue

if ($GPU_AVAILABLE) {
    Write-Host "Using GPU acceleration..." -ForegroundColor Green
    docker run -d `
        --name youtube-summarizer `
        --gpus all `
        -p 8000:8000 `
        -e PYTHONPATH=/app `
        -e OLLAMA_HOST=host.docker.internal:11434 `
        -e NVIDIA_VISIBLE_DEVICES=all `
        -e NVIDIA_DRIVER_CAPABILITIES=compute,utility `
        --memory=4g `
        --add-host host.docker.internal:host-gateway `
        --restart unless-stopped `
        youtube-summarizer
} else {
    Write-Host "Using CPU mode..." -ForegroundColor Yellow
    docker run -d `
        --name youtube-summarizer `
        -p 8000:8000 `
        -e PYTHONPATH=/app `
        -e OLLAMA_HOST=host.docker.internal:11434 `
        -e FORCE_CPU=true `
        --memory=4g `
        --add-host host.docker.internal:host-gateway `
        --restart unless-stopped `
        youtube-summarizer
}

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "✅ YouTube Analyzer started successfully!" -ForegroundColor Green
    Write-Host "🌐 Access the web interface at: http://localhost:8000" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "📋 Useful commands:" -ForegroundColor Yellow
    Write-Host "  View logs: docker logs -f youtube-summarizer" -ForegroundColor Gray
    Write-Host "  Stop container: docker stop youtube-summarizer" -ForegroundColor Gray
    Write-Host "  Remove container: docker rm youtube-summarizer" -ForegroundColor Gray
    Write-Host ""
    Write-Host "🔍 Checking container status..." -ForegroundColor Blue
    Start-Sleep -Seconds 3
    docker ps --filter name=youtube-summarizer --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
} else {
    Write-Host "❌ Failed to start YouTube Analyzer" -ForegroundColor Red
    exit 1
}
