# YouTube & Conference Video Analyzer - Setup Guide

## 🚀 Quick Start

### Option 1: Docker (Recommended)
The easiest way to get started with all features:

```bash
# Clone the repository
git clone https://github.com/Hydroxide538/Youtube-Analyzer.git
cd Youtube-Analyzer

# Run with Docker Compose
docker-compose up --build

# Access the application
open http://localhost:8000
```

### Option 2: Local Development
For development or customization:

```bash
# Clone repository
git clone https://github.com/Hydroxide538/Youtube-Analyzer.git
cd Youtube-Analyzer

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install and setup Ollama (for local AI models)
curl -fsSL https://ollama.ai/install.sh | sh
ollama serve &
ollama pull llama3.1:8b

# Run the application
python scripts/run.py
```

### Option 3: External Ollama Setup
If you already have Ollama running separately:

```bash
# Use external Ollama configuration
docker-compose -f docker-compose.external-ollama.yml up --build
```

## 📋 Prerequisites

### System Requirements
- **Operating System**: Linux, macOS, or Windows 10/11
- **Python**: 3.9+ (recommended: 3.11)
- **Memory**: 8GB+ RAM (16GB+ recommended for large models)
- **Storage**: 10GB+ free space (20GB+ recommended)
- **Network**: Internet connection for video downloads and cloud AI models

### Required Dependencies
- **FFmpeg**: Required for video/audio processing
- **Python packages**: Automatically installed via requirements.txt
- **Chrome/Chromium**: Required for conference video processing (automatically handled in Docker)

### AI Provider Options
Choose one or more AI providers:

1. **Ollama** (Local, Free)
   - Requires: Local installation, significant RAM
   - Models: llama3.1:8b, mistral:7b, and others
   - Cost: Free

2. **OpenAI** (Cloud, Paid)
   - Requires: API key, internet connection
   - Models: GPT-4, GPT-3.5-turbo, GPT-4-turbo
   - Cost: Pay per token

3. **Anthropic** (Cloud, Paid)
   - Requires: API key, internet connection
   - Models: Claude 3.5 Sonnet, Claude 3 Haiku, Claude 3 Opus
   - Cost: Pay per token

## 🔧 Installation Methods

### Docker Installation (Recommended)

#### Standard Docker Setup
```bash
# Clone and start with internal Ollama
git clone https://github.com/Hydroxide538/Youtube-Analyzer.git
cd Youtube-Analyzer
docker-compose up --build
```

#### External Ollama Setup
If you have Ollama running separately:
```bash
# Start with external Ollama connection
docker-compose -f docker-compose.external-ollama.yml up --build
```

#### Bridge Networking Setup
For complex network configurations:
```bash
# Use bridge networking
docker-compose -f docker-compose.bridge.yml up --build
```

#### Development Setup
For active development with live reload:
```bash
# Development mode with file watching
docker-compose -f docker-compose.dev.yml up --build
```

### Local Installation

#### 1. Install System Dependencies

**Ubuntu/Debian:**
```bash
sudo apt-get update
sudo apt-get install python3 python3-pip python3-venv ffmpeg wget curl
```

**macOS:**
```bash
# Install Homebrew if not already installed
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install dependencies
brew install python ffmpeg wget curl
```

**Windows:**
```bash
# Install using Chocolatey (run as administrator)
choco install python ffmpeg wget curl

# Or use winget
winget install Python.Python.3.11
winget install FFmpeg
```

#### 2. Install Ollama (for local AI models)
```bash
# Install Ollama
curl -fsSL https://ollama.ai/install.sh | sh

# Start Ollama service
ollama serve &

# Pull recommended models
ollama pull llama3.1:8b
ollama pull mistral:7b
```

#### 3. Setup Python Environment
```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
source venv/bin/activate  # Linux/macOS
# or
venv\Scripts\activate     # Windows

# Install Python dependencies
pip install -r requirements.txt
```

#### 4. Install Chrome/Chromium (for conference videos)
**Ubuntu/Debian:**
```bash
sudo apt-get install chromium-browser chromium-chromedriver
```

**macOS:**
```bash
brew install --cask google-chrome
brew install chromedriver
```

**Windows:**
```bash
choco install googlechrome chromedriver
```

## ⚙️ Configuration

### Environment Variables
Create a `.env` file in the project root:

```bash
# AI Provider Configuration (Optional)
OPENAI_API_KEY=sk-your-openai-key-here
ANTHROPIC_API_KEY=sk-ant-your-anthropic-key-here

# Ollama Configuration
OLLAMA_HOST=localhost:11434

# Application Configuration
HOST=0.0.0.0
PORT=8000
PYTHONPATH=/app

# Conference Video Configuration
CHROME_BINARY_PATH=/usr/bin/google-chrome
CHROMEDRIVER_PATH=/usr/bin/chromedriver
```

### AI Model Configuration

#### Ollama Models
```bash
# List available models
ollama list

# Pull additional models
ollama pull llama3.1:70b      # Larger, more capable model
ollama pull codellama:13b     # Code-focused model
ollama pull mistral:7b        # Smaller, faster model
```

#### OpenAI API Key Setup
1. Visit https://platform.openai.com/api-keys
2. Create a new API key
3. Set the environment variable or enter in web interface

#### Anthropic API Key Setup
1. Visit https://console.anthropic.com/
2. Create a new API key
3. Set the environment variable or enter in web interface

## 🎯 Usage Instructions

### Basic Setup Verification
1. **Start the application**:
   ```bash
   # Docker
   docker-compose up

   # Local
   python scripts/run.py
   ```

2. **Access the web interface**:
   Open http://localhost:8000

3. **Check provider status**:
   - Click "Advanced Options"
   - View provider status indicators
   - Test API keys if using cloud providers

### First Video Analysis
1. **Select video type**: Choose "YouTube" for YouTube videos
2. **Enter video URL**: Paste a YouTube URL (e.g., https://www.youtube.com/watch?v=dQw4w9WgXcQ)
3. **Configure options** (optional):
   - Select AI model from dropdown
   - Adjust max segments (3-10)
   - Set segment length (30-120 seconds)
4. **Start analysis**: Click "Analyze Video"
5. **Monitor progress**: Watch real-time processing updates
6. **Review results**: Examine generated summaries and insights

### Conference Video Setup
1. **Select conference type**: Choose "Conference Video"
2. **Enter conference URL**: Paste Zoom, Teams, or WebEx URL
3. **Add authentication** (if required):
   - Enter username/email
   - Enter password
4. **Start analysis**: System will authenticate and process

### AI Model Management
1. **View available models**: Check the model dropdown in advanced options
2. **Test API keys**: Use "Test API Keys" button to verify connectivity
3. **Refresh models**: Click "Refresh Models" to update available options
4. **Monitor costs**: Cloud models show cost information in the interface

## 🛠️ Advanced Configuration

### Docker Configurations

#### Custom Ollama Host
```yaml
# docker-compose.override.yml
version: '3.8'
services:
  youtube-summarizer:
    environment:
      - OLLAMA_HOST=your-ollama-host:11434
```

#### GPU Support
```yaml
# docker-compose.gpu.yml
version: '3.8'
services:
  youtube-summarizer:
    runtime: nvidia
    environment:
      - NVIDIA_VISIBLE_DEVICES=all
```

#### Memory Limits
```yaml
# docker-compose.override.yml
version: '3.8'
services:
  youtube-summarizer:
    mem_limit: 8g
    memswap_limit: 8g
```

### Custom Model Providers
To add new AI providers, extend the `ModelManager` class:

```python
# app/services/your_provider.py
from .base_model_provider import BaseModelProvider

class YourProvider(BaseModelProvider):
    def __init__(self, api_key: str):
        super().__init__()
        self.api_key = api_key
        self.model_name = "your-model"
    
    async def generate_summary(self, prompt: str, max_tokens: int = 300) -> str:
        # Implement your provider logic
        pass
```

### Performance Optimization

#### Memory Optimization
```bash
# Reduce segment length to use less memory
export DEFAULT_SEGMENT_LENGTH=30

# Use smaller models
ollama pull llama3.1:7b
```

#### Processing Speed
```bash
# Use cloud models for faster processing
export PREFERRED_PROVIDER=openai

# Increase worker processes
export WORKER_COUNT=4
```

## 🔍 Troubleshooting

### Common Setup Issues

#### Ollama Not Running
```bash
# Check if Ollama is running
ps aux | grep ollama

# Start Ollama service
ollama serve &

# Test connection
curl http://localhost:11434/api/tags
```

#### FFmpeg Not Found
```bash
# Test FFmpeg installation
ffmpeg -version

# Install FFmpeg
sudo apt-get install ffmpeg  # Ubuntu/Debian
brew install ffmpeg         # macOS
choco install ffmpeg        # Windows
```

#### Python Dependencies
```bash
# Reinstall dependencies
pip install --upgrade pip
pip install -r requirements.txt --force-reinstall
```

#### Chrome/Chromium Issues
```bash
# Install Chrome for conference videos
sudo apt-get install google-chrome-stable chromium-chromedriver

# Test Chrome installation
google-chrome --version
chromedriver --version
```

### Docker Issues

#### Port Already in Use
```bash
# Change port in docker-compose.yml
ports:
  - "8001:8000"  # Use port 8001 instead
```

#### Container Memory Issues
```bash
# Increase Docker memory limits
docker-compose down
docker system prune -a
docker-compose up --build
```

#### Network Connectivity
```bash
# Test network connectivity
docker exec -it youtube-analyzer ping ollama
docker exec -it youtube-analyzer curl http://ollama:11434/api/tags
```

### Performance Issues

#### Slow Processing
- Use cloud models (OpenAI/Anthropic) for faster processing
- Reduce segment length and max segments
- Use smaller Ollama models (mistral:7b instead of llama3.1:70b)

#### Memory Issues
- Reduce segment length to 30-60 seconds
- Use smaller models
- Increase system RAM or Docker memory limits

#### Storage Issues
- Clean up temporary files regularly
- Use smaller models
- Monitor disk space usage

## 📱 Usage Examples

### YouTube Video Analysis
```bash
# Example URLs to test
https://www.youtube.com/watch?v=dQw4w9WgXcQ
https://www.youtube.com/watch?v=jNQXAC9IVRw
https://www.youtube.com/watch?v=9bZkp7q19f0
```

### Conference Video Analysis
```bash
# Example conference platforms supported
- Zoom: https://zoom.us/rec/...
- Microsoft Teams: https://teams.microsoft.com/...
- WebEx: https://webex.com/...
- Google Meet: https://meet.google.com/...
```

### API Key Testing
```bash
# Test OpenAI API key
curl -H "Authorization: Bearer sk-your-key" \
  https://api.openai.com/v1/models

# Test Anthropic API key
curl -H "Authorization: Bearer sk-ant-your-key" \
  https://api.anthropic.com/v1/messages
```

## 🔄 Updates and Maintenance

### Updating the Application
```bash
# Pull latest changes
git pull origin main

# Rebuild Docker containers
docker-compose down
docker-compose up --build

# Update Python dependencies
pip install -r requirements.txt --upgrade
```

### Updating Models
```bash
# Update Ollama models
ollama pull llama3.1:8b
ollama pull mistral:7b

# Clean up old models
ollama rm old-model-name
```

### System Maintenance
```bash
# Clean up Docker resources
docker system prune -a

# Clean up temporary files
rm -rf /tmp/youtube_*

# Monitor disk usage
df -h
```

## 📞 Getting Help

### Self-Diagnosis
1. Check the web interface provider status
2. Review console logs for error messages
3. Test with simple YouTube videos first
4. Verify all dependencies are installed

### Documentation
- [README.md](README.md) - Complete feature overview
- [TROUBLESHOOTING.md](TROUBLESHOOTING.md) - Detailed troubleshooting
- [DOCKER_USAGE.md](DOCKER_USAGE.md) - Docker-specific guidance

### Support Resources
- GitHub Issues: Report bugs and request features
- Application logs: Check console output for detailed errors
- Provider documentation: Refer to Ollama, OpenAI, and Anthropic docs

---

**Success Indicators**: After setup, you should be able to:
- ✅ Access the web interface at http://localhost:8000
- ✅ See at least one AI provider as "Available" in advanced options
- ✅ Successfully analyze a short YouTube video
- ✅ Export results in text or JSON format
- ✅ View detailed summaries with timestamps and key points
