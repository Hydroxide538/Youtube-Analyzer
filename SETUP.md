# Quick Setup Guide

## Prerequisites
- Python 3.9+ (recommended: 3.11)
- FFmpeg installed
- 8GB+ RAM
- 10GB+ storage

## Quick Start (Recommended)

### Option 1: Docker (Easiest)
```bash
# Clone and run with Docker
git clone <repository-url>
cd youtube-analyzer
docker-compose up --build
```
Access at: http://localhost:8000

### Option 2: Local Development
```bash
# Clone repository
git clone <repository-url>
cd youtube-analyzer

# Install and start Ollama
curl -fsSL https://ollama.ai/install.sh | sh
ollama serve &
ollama pull llama3.1:8b

# Run the application
python run.py
```
Access at: http://localhost:8000

## Manual Setup (Advanced)

1. **Install system dependencies:**
   ```bash
   # Ubuntu/Debian
   sudo apt-get update
   sudo apt-get install python3 python3-pip ffmpeg
   
   # macOS
   brew install python ffmpeg
   ```

2. **Install Ollama:**
   ```bash
   curl -fsSL https://ollama.ai/install.sh | sh
   ollama serve
   ollama pull llama3.1:8b
   ```

3. **Setup Python environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

4. **Run application:**
   ```bash
   python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
   ```

## Verification

1. Open http://localhost:8000
2. Enter a YouTube URL (e.g., https://www.youtube.com/watch?v=dQw4w9WgXcQ)
3. (Optional) Click "Advanced Options" to select AI model and adjust settings
4. Click "Analyze Video"
5. Watch the progress and review results

## New Features

### Dynamic Model Selection
- The application now supports choosing from any installed Ollama models
- Access via "Advanced Options" → "AI Model" dropdown
- Docker container comes with llama3.1:8b and mistral:7b pre-installed
- Model information shows size and modification date to help with selection

## Troubleshooting

- **Ollama not found**: Ensure Ollama is installed and running (`ollama serve`)
- **FFmpeg error**: Install FFmpeg for your system
- **Memory issues**: Use smaller videos or increase system RAM
- **Port conflicts**: Change port in docker-compose.yml or uvicorn command

For detailed troubleshooting, see README.md
