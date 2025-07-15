# Troubleshooting Guide

## YouTube Download Issues

### Problem: HTTP Error 403: Forbidden

**Symptoms:**
- Error message: "Failed to download video: ERROR: unable to download video data: HTTP Error 403: Forbidden"
- Video processing fails during download step

**Common Causes & Solutions:**

### 1. Outdated yt-dlp Version
YouTube frequently updates their anti-bot measures. The app has been updated to use the latest yt-dlp version (2024.12.13).

**Solution:**
```bash
# Rebuild the container to get the latest yt-dlp
docker-compose down
docker-compose build --no-cache
docker-compose up
```

### 2. YouTube Rate Limiting
YouTube may temporarily block requests from your IP address.

**Solutions:**
- Wait 10-15 minutes before trying again
- Try a different video first
- Use a VPN if the issue persists

### 3. Video Restrictions
Some videos may have geographic restrictions or age gates.

**Solutions:**
- Try a different, publicly available video
- Ensure the video is not private or unlisted
- Check if the video is available in your region

### 4. Network Configuration
Corporate firewalls or network restrictions may block YouTube access.

**Solutions:**
- Test from a different network
- Check if YouTube is accessible in your browser
- Configure proxy settings if needed

### 5. Emergency Workaround
If the issue persists, you can test with a known working video:
```
https://www.youtube.com/watch?v=dQw4w9WgXcQ
```

## Frontend Not Loading Issues

### Problem: Container runs but frontend is not accessible

**Symptoms:**
- Docker container starts successfully
- Cannot access http://localhost:8000
- Browser shows connection refused or timeout

**Common Causes & Solutions:**

### 1. Network Configuration Issues

**Try Bridge Networking (Recommended):**
```bash
# Stop current container
docker-compose down

# Use bridge networking instead of host
docker-compose -f docker-compose.bridge.yml up --build
```

**Access at:** http://localhost:8000

### 2. Host Networking Issues

If you're using the default `docker-compose.yml` (host networking):
```bash
# Check if port 8000 is available
netstat -an | grep 8000

# On some systems, try:
# - Linux: http://localhost:8000
# - macOS: http://localhost:8000
# - Windows: http://localhost:8000 or http://127.0.0.1:8000
```

### 3. Ollama Connection Issues

**Check Ollama connectivity:**
```bash
# Test Ollama API
curl http://localhost:11434/api/tags

# Check if your Ollama container is running
docker ps | grep ollama
```

**If Ollama is not accessible:**
```bash
# Update OLLAMA_HOST in docker-compose.yml
environment:
  - OLLAMA_HOST=your-ollama-container-name:11434
```

### 4. Container Startup Issues

**Check container logs:**
```bash
# View application logs
docker logs youtube-summarizer

# Follow logs in real-time
docker logs -f youtube-summarizer
```

**Common log messages:**
- `Waiting for Ollama...` - Normal, waiting for Ollama to be ready
- `Ollama service is ready!` - Good, Ollama connected
- `Starting YouTube Summarizer...` - Application starting
- `Uvicorn running on http://0.0.0.0:8000` - Success!

### 5. Port Conflicts

**Check for port conflicts:**
```bash
# Check what's using port 8000
lsof -i :8000

# Kill conflicting processes if needed
sudo kill -9 <PID>
```

### 6. Docker Desktop Issues

**On Windows/macOS with Docker Desktop:**
- Ensure Docker Desktop is running
- Try restarting Docker Desktop
- Check Docker Desktop resources (memory > 4GB)

## Quick Diagnostic Steps

### Step 1: Test Basic Container
```bash
# Simple test without Ollama dependency
docker run -it --rm -p 8000:8000 python:3.11-slim bash -c "python -c 'import http.server; import socketserver; socketserver.TCPServer((\"\", 8000), http.server.SimpleHTTPRequestHandler).serve_forever()'"
```
Access http://localhost:8000 - if this works, Docker networking is fine.

### Step 2: Check Application Health
```bash
# Check health endpoint
curl http://localhost:8000/health

# Expected response:
# {"status":"healthy","message":"YouTube Summarizer API is running"}
```

### Step 3: Test Ollama Connection
```bash
# From within container
docker exec -it youtube-summarizer curl http://localhost:11434/api/tags

# Or test the configured host
docker exec -it youtube-summarizer curl http://$OLLAMA_HOST/api/tags
```

## Configuration Options

### Option 1: Bridge Networking (Recommended)
```bash
docker-compose -f docker-compose.bridge.yml up --build
```
- **Pros:** Standard Docker networking, port mapping works
- **Cons:** Requires host.docker.internal for Ollama access

### Option 2: Host Networking
```bash
docker-compose up --build
```
- **Pros:** Direct access to host services
- **Cons:** No port isolation, may conflict on some systems

### Option 3: External Ollama Network
```bash
docker-compose -f docker-compose.external-ollama.yml up --build
```
- **Pros:** Custom network configuration
- **Cons:** Requires network configuration

## Emergency Fallback

### Run Without Docker
```bash
# Install dependencies
pip install -r requirements.txt

# Start Ollama separately
ollama serve

# Run application
OLLAMA_HOST=localhost:11434 python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

## Getting Help

**Collect diagnostic information:**
```bash
# System info
docker --version
docker-compose --version

# Container status
docker ps -a

# Container logs
docker logs youtube-summarizer

# Network info
docker network ls
docker inspect youtube-summarizer
```

**Test URLs:**
- Main app: http://localhost:8000
- Health check: http://localhost:8000/health
- API docs: http://localhost:8000/docs
- Ollama API: http://localhost:11434/api/tags

If none of these solutions work, please share:
1. Docker logs output
2. Operating system
3. Which docker-compose file you're using
4. curl test results
