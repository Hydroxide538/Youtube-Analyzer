#!/bin/bash

echo "🔍 YouTube Summarizer - Setup Verification"
echo "============================================"

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker first."
    exit 1
fi

echo "✅ Docker is running"

# Check if container is running
if docker ps | grep -q youtube-summarizer; then
    echo "✅ Container is running"
    
    # Check port binding
    PORT_BINDING=$(docker ps --format "table {{.Names}}\t{{.Ports}}" | grep youtube-summarizer | awk '{print $2}')
    if [[ "$PORT_BINDING" == *"8000"* ]]; then
        echo "✅ Port 8000 is properly bound: $PORT_BINDING"
    else
        echo "❌ Port 8000 is not bound. Current binding: $PORT_BINDING"
        echo "   This might be the issue with the frontend not loading."
    fi
else
    echo "❌ Container is not running"
    echo "   Run: docker-compose up --build"
    exit 1
fi

# Test if application is responding
echo ""
echo "🌐 Testing application endpoints..."

# Test health endpoint
if curl -s -f http://localhost:8000/health > /dev/null 2>&1; then
    echo "✅ Health endpoint is responding"
    HEALTH_RESPONSE=$(curl -s http://localhost:8000/health)
    echo "   Response: $HEALTH_RESPONSE"
else
    echo "❌ Health endpoint is not responding"
    echo "   Expected: http://localhost:8000/health"
    echo "   This confirms the frontend loading issue."
fi

# Test main page
if curl -s -f http://localhost:8000 > /dev/null 2>&1; then
    echo "✅ Main page is responding"
else
    echo "❌ Main page is not responding"
    echo "   Expected: http://localhost:8000"
fi

# Test if Ollama is accessible
echo ""
echo "🤖 Testing Ollama connection..."

if curl -s -f http://localhost:11434/api/tags > /dev/null 2>&1; then
    echo "✅ Ollama is accessible at localhost:11434"
    MODELS=$(curl -s http://localhost:11434/api/tags | jq -r '.models[].name' 2>/dev/null || echo "Could not parse models")
    echo "   Available models: $MODELS"
else
    echo "❌ Ollama is not accessible at localhost:11434"
    echo "   Make sure your Ollama container is running"
fi

echo ""
echo "📋 Docker Container Status:"
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" | grep -E "(NAMES|youtube-summarizer)"

echo ""
echo "📝 Container logs (last 10 lines):"
docker logs --tail 10 youtube-summarizer 2>/dev/null || echo "Could not get logs"

echo ""
echo "🎯 Quick Tests:"
echo "1. Check if port is bound: docker ps | grep youtube-summarizer"
echo "2. Test health endpoint: curl http://localhost:8000/health"
echo "3. Test main page: curl http://localhost:8000"
echo "4. Check container logs: docker logs youtube-summarizer"

echo ""
echo "🚀 If all tests pass, open: http://localhost:8000"
