# Troubleshooting Guide

## 🔍 Quick Diagnostics

### Step 1: Check Application Status
1. **Access the web interface**: http://localhost:8000
2. **Check provider status**: Click "Advanced Options" → View AI provider indicators
3. **Review console logs**: Check terminal output for error messages
4. **Test basic functionality**: Try analyzing a short YouTube video

### Step 2: Verify Dependencies
```bash
# Check Python version
python --version  # Should be 3.9+

# Check FFmpeg installation
ffmpeg -version

# Check Ollama (if using local models)
ollama --version
ollama list

# Check Docker (if using containers)
docker --version
docker-compose --version
```

### Step 3: Provider Connectivity Tests
```bash
# Test Ollama connection
curl http://localhost:11434/api/tags

# Test OpenAI API (if using)
curl -H "Authorization: Bearer YOUR_API_KEY" \
  https://api.openai.com/v1/models

# Test Anthropic API (if using)
curl -H "Authorization: Bearer YOUR_API_KEY" \
  https://api.anthropic.com/v1/messages
```

## 🚨 Common Issues and Solutions

### AI Provider Issues

#### Problem: "Ollama not available" or "No models available"
**Symptoms:**
- Provider status shows "Ollama: Unavailable"
- No models appear in dropdown
- Connection timeout errors

**Solutions:**
1. **Check if Ollama is running:**
   ```bash
   # Check if Ollama process is running
   ps aux | grep ollama
   
   # If not running, start Ollama
   ollama serve &
   
   # Wait a moment then test
   curl http://localhost:11434/api/tags
   ```

2. **Verify models are installed:**
   ```bash
   # List installed models
   ollama list
   
   # If no models, install default
   ollama pull llama3.1:8b
   ```

3. **Check Ollama host configuration:**
   ```bash
   # In Docker, check environment variable
   echo $OLLAMA_HOST
   
   # Should be localhost:11434 or ollama:11434
   ```

4. **Docker networking issues:**
   ```bash
   # Test connection from container
   docker exec -it youtube-analyzer curl http://ollama:11434/api/tags
   
   # If fails, check docker-compose network configuration
   ```

#### Problem: "OpenAI API key invalid" or "Rate limit exceeded"
**Symptoms:**
- API key validation fails
- "Invalid API key" error messages
- Rate limiting errors

**Solutions:**
1. **Verify API key format:**
   ```bash
   # OpenAI keys should start with 'sk-'
   echo $OPENAI_API_KEY | grep '^sk-'
   
   # Check key length (should be 50+ characters)
   echo $OPENAI_API_KEY | wc -c
   ```

2. **Test API key directly:**
   ```bash
   curl -H "Authorization: Bearer $OPENAI_API_KEY" \
     https://api.openai.com/v1/models
   ```

3. **Check usage limits:**
   - Visit https://platform.openai.com/usage
   - Verify account has credits
   - Check rate limits for your plan

4. **Rate limiting solutions:**
   - Wait and retry
   - Use different model (e.g., gpt-3.5-turbo instead of gpt-4)
   - Upgrade API plan for higher limits

#### Problem: "Anthropic API connection failed"
**Symptoms:**
- Cannot connect to Anthropic API
- Authentication errors
- Model not available

**Solutions:**
1. **Verify API key:**
   ```bash
   # Anthropic keys should start with 'sk-ant-'
   echo $ANTHROPIC_API_KEY | grep '^sk-ant-'
   ```

2. **Test API connection:**
   ```bash
   curl -H "Authorization: Bearer $ANTHROPIC_API_KEY" \
     -H "Content-Type: application/json" \
     -X POST https://api.anthropic.com/v1/messages \
     -d '{"model":"claude-3-haiku-20240307","max_tokens":10,"messages":[{"role":"user","content":"Hi"}]}'
   ```

3. **Check account status:**
   - Visit https://console.anthropic.com/
   - Verify account is active
   - Check usage limits

### Video Processing Issues

#### Problem: "YouTube video download failed" or "403 Forbidden"
**Symptoms:**
- "Failed to download video" error
- 403 Forbidden errors
- "Video not available" messages

**Solutions:**
1. **Check video accessibility:**
   ```bash
   # Test video URL manually
   curl -I "https://www.youtube.com/watch?v=YOUR_VIDEO_ID"
   
   # Check if video is public
   # Try opening in browser
   ```

2. **Common video restrictions:**
   - **Age-restricted videos**: May require authentication
   - **Private videos**: Cannot be downloaded
   - **Geo-blocked content**: VPN may be required
   - **Live streams**: May not be supported

3. **Update yt-dlp:**
   ```bash
   # Update to latest version
   pip install --upgrade yt-dlp
   
   # Test with updated version
   yt-dlp --version
   ```

4. **Try different video formats:**
   - Use different YouTube URLs (youtube.com vs youtu.be)
   - Try videos from different channels
   - Test with shorter videos first

#### Problem: "Conference video authentication failed"
**Symptoms:**
- Cannot access conference recordings
- Authentication errors
- "Invalid credentials" messages

**Solutions:**
1. **Verify credentials:**
   - Check username/email format
   - Verify password is correct
   - Test login on conference platform directly

2. **Check video access:**
   - Ensure you have permission to view the recording
   - Check if video is publicly accessible
   - Verify meeting recording is available

3. **Platform-specific issues:**
   - **Zoom**: Ensure recording is processed and available
   - **Teams**: Check if recording is in OneDrive/SharePoint
   - **WebEx**: Verify recording is not password-protected

4. **Network and firewall issues:**
   - Check if corporate firewall blocks access
   - Try from different network
   - Verify proxy settings if applicable

#### Problem: "FFmpeg not found" or "Audio processing failed"
**Symptoms:**
- "FFmpeg not found" error
- Audio extraction failures
- Transcription preprocessing errors

**Solutions:**
1. **Install FFmpeg:**
   ```bash
   # Ubuntu/Debian
   sudo apt-get update
   sudo apt-get install ffmpeg
   
   # macOS
   brew install ffmpeg
   
   # Windows
   choco install ffmpeg
   ```

2. **Verify installation:**
   ```bash
   # Test FFmpeg
   ffmpeg -version
   
   # Check if accessible from Python
   python -c "import subprocess; subprocess.run(['ffmpeg', '-version'])"
   ```

3. **Path issues:**
   ```bash
   # Add to PATH if necessary
   export PATH=$PATH:/usr/local/bin
   
   # Or specify full path in environment
   export FFMPEG_PATH=/usr/local/bin/ffmpeg
   ```

### Performance Issues

#### Problem: "Processing is very slow"
**Symptoms:**
- Long processing times
- High CPU/memory usage
- System becomes unresponsive

**Solutions:**
1. **Optimize processing parameters:**
   - Reduce segment length (30-60 seconds)
   - Limit max segments (3-5)
   - Use smaller models (mistral:7b instead of llama3.1:70b)

2. **System optimization:**
   ```bash
   # Check system resources
   htop
   free -h
   df -h
   
   # Close unnecessary applications
   # Increase available RAM
   ```

3. **Model optimization:**
   - Use cloud models for faster processing
   - Switch to smaller local models
   - Consider GPU acceleration if available

4. **Video optimization:**
   - Test with shorter videos first
   - Use lower quality audio extraction
   - Process videos in smaller chunks

#### Problem: "Out of memory" errors
**Symptoms:**
- Application crashes
- "Out of memory" errors
- System becomes unresponsive

**Solutions:**
1. **Reduce memory usage:**
   ```bash
   # Use smaller models
   ollama pull llama3.1:7b  # Instead of 70b
   
   # Reduce segment length
   export DEFAULT_SEGMENT_LENGTH=30
   ```

2. **Increase available memory:**
   ```bash
   # Check current memory usage
   free -h
   
   # Close other applications
   # Add swap space if needed
   sudo fallocate -l 4G /swapfile
   sudo chmod 600 /swapfile
   sudo mkswap /swapfile
   sudo swapon /swapfile
   ```

3. **Docker memory limits:**
   ```yaml
   # docker-compose.override.yml
   services:
     youtube-summarizer:
       mem_limit: 8g
       memswap_limit: 8g
   ```

### Docker Issues

#### Problem: "Container won't start" or "Port already in use"
**Symptoms:**
- Docker container fails to start
- Port conflict errors
- Service unavailable

**Solutions:**
1. **Check port usage:**
   ```bash
   # Check what's using port 8000
   lsof -i :8000
   netstat -tulpn | grep :8000
   
   # Kill conflicting process or change port
   ```

2. **Change application port:**
   ```yaml
   # docker-compose.override.yml
   services:
     youtube-summarizer:
       ports:
         - "8001:8000"  # Use different port
   ```

3. **Clean up Docker resources:**
   ```bash
   # Stop all containers
   docker-compose down
   
   # Remove unused resources
   docker system prune -a
   
   # Restart with clean state
   docker-compose up --build
   ```

#### Problem: "Network connectivity issues" between containers
**Symptoms:**
- Cannot connect to Ollama from app container
- DNS resolution failures
- Network timeout errors

**Solutions:**
1. **Check Docker network:**
   ```bash
   # List Docker networks
   docker network ls
   
   # Inspect network configuration
   docker network inspect youtube-analyzer_default
   ```

2. **Test connectivity:**
   ```bash
   # Test from app container
   docker exec -it youtube-analyzer ping ollama
   docker exec -it youtube-analyzer curl http://ollama:11434/api/tags
   ```

3. **Network configuration fixes:**
   ```yaml
   # Use bridge networking
   docker-compose -f docker-compose.bridge.yml up
   
   # Or use host networking
   network_mode: host
   ```

### Chrome/Selenium Issues (Conference Videos)

#### Problem: "Chrome driver not found" or "Selenium errors"
**Symptoms:**
- Cannot process conference videos
- Chrome/Selenium errors
- WebDriver failures

**Solutions:**
1. **Install Chrome and ChromeDriver:**
   ```bash
   # Ubuntu/Debian
   sudo apt-get install google-chrome-stable chromium-chromedriver
   
   # macOS
   brew install --cask google-chrome
   brew install chromedriver
   
   # Windows
   choco install googlechrome chromedriver
   ```

2. **Verify installation:**
   ```bash
   # Check Chrome version
   google-chrome --version
   
   # Check ChromeDriver version
   chromedriver --version
   ```

3. **Docker Chrome setup:**
   ```dockerfile
   # Dockerfile should include
   RUN apt-get update && apt-get install -y \
       google-chrome-stable \
       chromium-chromedriver
   ```

4. **Configuration issues:**
   ```bash
   # Set correct paths
   export CHROME_BINARY_PATH=/usr/bin/google-chrome
   export CHROMEDRIVER_PATH=/usr/bin/chromedriver
   ```

## 🔧 Advanced Debugging

### Enable Debug Logging
```bash
# Enable debug logging
export LOG_LEVEL=DEBUG

# Run with verbose output
python -m uvicorn app.main:app --log-level debug
```

### Application Diagnostics
```bash
# Check application health
curl http://localhost:8000/health

# Check model availability
curl http://localhost:8000/api/models

# Monitor WebSocket connections
# Use browser developer tools to inspect WebSocket traffic
```

### System Diagnostics
```bash
# Check system resources
htop
iostat -x 1
vmstat 1

# Check disk space
df -h
du -sh /tmp/*

# Check network connectivity
ping google.com
nslookup youtube.com
```

### Database and Storage Issues
```bash
# Clean up temporary files
rm -rf /tmp/youtube_*
rm -rf /tmp/conference_*

# Check disk space
df -h

# Monitor file operations
lsof | grep youtube
```

## 📋 Diagnostic Checklist

### Before Reporting Issues
- [ ] Check all provider status indicators
- [ ] Test with a simple YouTube video
- [ ] Review console logs for errors
- [ ] Verify all dependencies are installed
- [ ] Test API keys independently
- [ ] Check system resources (CPU, memory, disk)
- [ ] Try different video URLs
- [ ] Test with different AI models

### Information to Include in Bug Reports
1. **System information:**
   - Operating system and version
   - Python version
   - Docker version (if using)
   - Available RAM and storage

2. **Configuration:**
   - Installation method (Docker/local)
   - AI providers being used
   - Model selection
   - Environment variables

3. **Error details:**
   - Complete error messages
   - Console logs
   - Steps to reproduce
   - Expected vs actual behavior

4. **Video information:**
   - Video URL (if shareable)
   - Video length and type
   - Processing settings used

## 🆘 Emergency Recovery

### Complete Reset
```bash
# Stop all services
docker-compose down

# Clean up everything
docker system prune -a
docker volume prune

# Remove application data
rm -rf /tmp/youtube_*
rm -rf ~/.ollama  # Only if you want to reset Ollama

# Fresh start
git pull origin main
docker-compose up --build
```

### Backup Important Data
```bash
# Backup configuration
cp docker-compose.yml docker-compose.yml.backup
cp .env .env.backup

# Backup any custom models or data
# (Application doesn't store permanent data by default)
```

## 📞 Getting Additional Help

### Self-Service Resources
1. **Check the FAQ**: Review README.md for common questions
2. **Search existing issues**: Check GitHub issues for similar problems
3. **Documentation**: Review all documentation files
4. **Community support**: Search for similar issues online

### Reporting Issues
When reporting issues:
1. **Use the diagnostic checklist** above
2. **Include system information** and error logs
3. **Provide steps to reproduce** the issue
4. **Test with minimal configuration** first
5. **Be specific** about expected vs actual behavior

### Development and Contribution
- Fork the repository for custom modifications
- Review the development documentation
- Test thoroughly before submitting changes
- Follow the project's coding standards

---

**Remember**: Most issues can be resolved by checking provider status, verifying dependencies, and reviewing the logs. Start with the quick diagnostics and work through the solutions systematically.
