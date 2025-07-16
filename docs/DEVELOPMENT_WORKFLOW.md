# Development Workflow Guide

## 🚀 Getting Started with Development

### Development Environment Setup

#### Prerequisites
- Python 3.9+ (recommended: 3.11)
- Git
- Docker and Docker Compose
- Code editor (VS Code recommended)
- Terminal/Command Line

#### Initial Setup
```bash
# Clone the repository
git clone https://github.com/Hydroxide538/Youtube-Analyzer.git
cd Youtube-Analyzer

# Create development branch
git checkout -b feature/your-feature-name

# Set up Python virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies with development extras
pip install -r requirements.txt
pip install -r requirements-dev.txt  # If exists, for development tools

# Install pre-commit hooks (if available)
pre-commit install
```

#### Development Configuration
```bash
# Create development environment file
cp .env.example .env

# Set development environment variables
echo "ENVIRONMENT=development" >> .env
echo "LOG_LEVEL=DEBUG" >> .env
echo "RELOAD=true" >> .env
```

## 🏗️ Project Architecture

### Directory Structure
```
youtube-analyzer/
├── app/                        # Main application package
│   ├── __init__.py
│   ├── main.py                # FastAPI application entry point
│   ├── models/                # Pydantic models
│   │   ├── __init__.py
│   │   └── request_models.py  # Request/response models
│   ├── services/              # Business logic services
│   │   ├── __init__.py
│   │   ├── base_model_provider.py     # Base class for AI providers
│   │   ├── model_manager.py           # Multi-provider model management
│   │   ├── youtube_service.py         # YouTube video processing
│   │   ├── conference_video_service.py # Conference video processing
│   │   ├── transcription_service.py   # Whisper transcription
│   │   ├── summarization_service.py   # AI summarization
│   │   ├── ollama_provider.py         # Ollama integration
│   │   ├── openai_provider.py         # OpenAI integration
│   │   └── anthropic_provider.py      # Anthropic integration
│   └── utils/                 # Utility functions
│       ├── __init__.py
│       └── websocket_manager.py       # WebSocket connection management
├── static/                    # Frontend static files
│   ├── css/
│   │   └── style.css         # Main stylesheet
│   └── js/
│       └── app.js            # Frontend JavaScript application
├── templates/                 # HTML templates
│   └── index.html            # Main web interface
├── docker/                    # Docker configurations
│   ├── Dockerfile            # Main application container
│   ├── Dockerfile.dev        # Development container
│   └── docker-compose.*.yml  # Various Docker Compose configurations
├── scripts/                   # Helper scripts
│   ├── run.py               # Local development server
│   ├── dev.py               # Development utilities
│   └── test_*.py            # Test scripts
├── docs/                      # Documentation
│   ├── README.md            # Main documentation
│   ├── SETUP.md             # Setup instructions
│   ├── TROUBLESHOOTING.md   # Troubleshooting guide
│   └── DEVELOPMENT_WORKFLOW.md # This file
├── computer_use/             # Computer use integration
├── build_notes/              # Build and change documentation
└── requirements.txt          # Python dependencies
```

### Key Components

#### 1. FastAPI Application (`app/main.py`)
- **Purpose**: Main application server with WebSocket support
- **Key Features**:
  - REST API endpoints for model management
  - WebSocket endpoint for real-time processing
  - Static file serving
  - CORS configuration

#### 2. Model Manager (`app/services/model_manager.py`)
- **Purpose**: Unified interface for multiple AI providers
- **Key Features**:
  - Multi-provider support (Ollama, OpenAI, Anthropic)
  - Dynamic model loading and selection
  - Provider availability monitoring
  - API key management

#### 3. Video Services
- **YouTube Service** (`app/services/youtube_service.py`):
  - YouTube video download with anti-bot measures
  - Audio extraction and segmentation
  - Metadata extraction
  
- **Conference Video Service** (`app/services/conference_video_service.py`):
  - Conference video download with authentication
  - Selenium-based automation
  - Multi-platform support (Zoom, Teams, WebEx)

#### 4. AI Provider Integration
- **Base Provider** (`app/services/base_model_provider.py`):
  - Abstract base class for all AI providers
  - Standardized interface for summarization
  - Connection testing and validation

- **Provider Implementations**:
  - `ollama_provider.py`: Local Ollama models
  - `openai_provider.py`: OpenAI GPT models
  - `anthropic_provider.py`: Anthropic Claude models

#### 5. Frontend (`static/js/app.js`)
- **Purpose**: Single-page application for user interface
- **Key Features**:
  - WebSocket communication
  - Real-time progress tracking
  - Dynamic model selection
  - Export functionality

## 🔧 Development Tasks

### Adding New AI Providers

#### 1. Create Provider Class
```python
# app/services/your_provider.py
from typing import List, Dict, Any
from .base_model_provider import BaseModelProvider

class YourProvider(BaseModelProvider):
    def __init__(self, api_key: str):
        super().__init__()
        self.api_key = api_key
        self.base_url = "https://api.yourprovider.com"
        self.model_name = "your-default-model"
    
    async def check_availability(self) -> bool:
        """Check if the provider is available"""
        try:
            # Implement availability check
            return True
        except Exception:
            return False
    
    async def list_models(self) -> List[Dict[str, Any]]:
        """List available models"""
        # Implement model listing
        return []
    
    async def generate_summary(self, prompt: str, max_tokens: int = 300) -> str:
        """Generate summary using the provider"""
        # Implement summary generation
        return ""
    
    async def test_connection(self) -> Dict[str, Any]:
        """Test connection to the provider"""
        # Implement connection test
        return {"status": "success", "provider": "YourProvider"}
```

#### 2. Register Provider in Model Manager
```python
# app/services/model_manager.py
from .your_provider import YourProvider

class ModelManager:
    async def initialize(self, your_api_key: str = None, ...):
        # Add your provider initialization
        if your_api_key:
            your_provider = YourProvider(api_key=your_api_key)
            self.providers["YourProvider"] = your_provider
```

#### 3. Update Frontend
```javascript
// static/js/app.js
// Add provider status element in HTML
// Update provider status handling in JavaScript
updateProviderStatusFromResponse(providers) {
    // Add your provider status handling
    if (providers.YourProvider) {
        const status = providers.YourProvider.available ? 'available' : 'unavailable';
        // Update UI accordingly
    }
}
```

### Adding New Video Sources

#### 1. Create Video Service
```python
# app/services/your_video_service.py
import asyncio
from typing import Dict, List, Any

class YourVideoService:
    def __init__(self):
        # Initialize service
        pass
    
    async def download_video(self, url: str, **kwargs) -> Dict[str, Any]:
        """Download video from your platform"""
        # Implement video download
        return {
            'title': 'Video Title',
            'duration': 3600,
            'audio_path': '/path/to/audio.wav',
            'video_url': url,
            'description': 'Video description'
        }
    
    async def extract_audio_segments(self, audio_path: str, segment_length: int = 60) -> List[Dict[str, Any]]:
        """Extract audio segments"""
        # Implement audio segmentation
        return []
    
    def is_valid_url(self, url: str) -> bool:
        """Validate URL format"""
        # Implement URL validation
        return True
```

#### 2. Integrate with Main Application
```python
# app/main.py
from .services.your_video_service import YourVideoService

# Initialize service
your_video_service = YourVideoService()

# Add to processing pipeline
async def process_video_pipeline(websocket: WebSocket, url: str, ...):
    # Add video type detection
    if your_video_service.is_valid_url(url):
        video_type = "your_platform"
    
    # Add processing logic
    if video_type == "your_platform":
        video_info = await your_video_service.download_video(url)
        service_to_use = your_video_service
```

### Frontend Development

#### Adding New Features
1. **HTML Structure**: Update `templates/index.html`
2. **Styling**: Modify `static/css/style.css`
3. **JavaScript**: Extend `static/js/app.js`

#### JavaScript Architecture
```javascript
// static/js/app.js
class YouTubeSummarizer {
    constructor() {
        this.initializeElements();
        this.bindEvents();
        this.initializeWebSocket();
    }
    
    // Add new methods
    handleNewFeature() {
        // Implement new feature
    }
    
    // Update existing methods
    handleWebSocketMessage(data) {
        // Add new message types
        switch (data.status) {
            case 'your_new_status':
                this.handleNewStatus(data);
                break;
            // ... existing cases
        }
    }
}
```

## 🧪 Testing

### Manual Testing

#### Local Development Testing
```bash
# Start development server
python scripts/dev.py

# Test with different video types
python scripts/test_static_files.py

# Test GPU setup (if available)
python scripts/test_gpu_setup.py
```

#### Docker Testing
```bash
# Test with different Docker configurations
docker-compose -f docker-compose.dev.yml up --build

# Test external Ollama setup
docker-compose -f docker-compose.external-ollama.yml up --build

# Test GPU support
docker-compose -f docker-compose.gpu.yml up --build
```

### Automated Testing (Future Enhancement)

#### Unit Tests
```python
# tests/test_model_manager.py
import pytest
from app.services.model_manager import ModelManager

@pytest.mark.asyncio
async def test_model_manager_initialization():
    manager = ModelManager()
    await manager.initialize()
    assert manager.initialized

@pytest.mark.asyncio
async def test_provider_availability():
    manager = ModelManager()
    await manager.initialize()
    providers = manager.get_provider_status()
    assert "initialized" in providers
```

#### Integration Tests
```python
# tests/test_video_processing.py
import pytest
from app.services.youtube_service import YouTubeService

@pytest.mark.asyncio
async def test_youtube_video_download():
    service = YouTubeService()
    url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
    
    if service.is_valid_youtube_url(url):
        info = await service.download_video(url)
        assert info["title"]
        assert info["duration"] > 0
```

### Performance Testing

#### Load Testing
```bash
# Test with multiple concurrent requests
# Use tools like Apache Bench or wrk

# Test memory usage with large videos
python scripts/test_memory_usage.py

# Test processing time with different models
python scripts/benchmark_models.py
```

## 📦 Build and Deployment

### Docker Build Process

#### Development Build
```bash
# Build development image
docker build -f docker/Dockerfile.dev -t youtube-analyzer:dev .

# Run development container
docker run -it --rm -p 8000:8000 -v $(pwd):/app youtube-analyzer:dev
```

#### Production Build
```bash
# Build production image
docker build -f docker/Dockerfile -t youtube-analyzer:latest .

# Multi-stage build optimization
docker build --target production -t youtube-analyzer:prod .
```

### Environment-Specific Configurations

#### Development Environment
```yaml
# docker-compose.dev.yml
version: '3.8'
services:
  youtube-summarizer:
    build:
      context: .
      dockerfile: docker/Dockerfile.dev
    environment:
      - ENVIRONMENT=development
      - LOG_LEVEL=DEBUG
      - RELOAD=true
    volumes:
      - .:/app
      - /app/venv  # Exclude virtual environment
```

#### Production Environment
```yaml
# docker-compose.prod.yml
version: '3.8'
services:
  youtube-summarizer:
    build:
      context: .
      dockerfile: docker/Dockerfile
    environment:
      - ENVIRONMENT=production
      - LOG_LEVEL=INFO
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
```

## 🔍 Debugging and Monitoring

### Development Debugging

#### Enable Debug Mode
```bash
# Set environment variables
export LOG_LEVEL=DEBUG
export ENVIRONMENT=development

# Run with debug logging
python -m uvicorn app.main:app --log-level debug --reload
```

#### WebSocket Debugging
```javascript
// In browser console
const ws = new WebSocket('ws://localhost:8000/ws');
ws.onmessage = (event) => {
    console.log('WebSocket message:', JSON.parse(event.data));
};
```

#### API Debugging
```bash
# Test API endpoints
curl -X GET http://localhost:8000/api/models
curl -X GET http://localhost:8000/health

# Test WebSocket connection
wscat -c ws://localhost:8000/ws
```

### Performance Monitoring

#### Resource Usage
```bash
# Monitor container resources
docker stats youtube-analyzer

# Monitor system resources
htop
iotop
```

#### Application Metrics
```python
# app/utils/metrics.py
import time
import psutil
from functools import wraps

def monitor_performance(func):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        start_time = time.time()
        start_memory = psutil.Process().memory_info().rss
        
        result = await func(*args, **kwargs)
        
        end_time = time.time()
        end_memory = psutil.Process().memory_info().rss
        
        print(f"{func.__name__} took {end_time - start_time:.2f}s")
        print(f"Memory change: {(end_memory - start_memory) / 1024 / 1024:.2f}MB")
        
        return result
    return wrapper
```

## 🚀 Deployment Strategies

### Local Deployment
```bash
# Simple local deployment
python scripts/run.py

# With process manager (PM2)
pm2 start scripts/run.py --name youtube-analyzer
```

### Docker Deployment
```bash
# Single container deployment
docker run -d -p 8000:8000 youtube-analyzer:latest

# Multi-container deployment
docker-compose -f docker-compose.prod.yml up -d
```

### Cloud Deployment

#### Docker Cloud Platforms
```yaml
# docker-compose.cloud.yml
version: '3.8'
services:
  youtube-summarizer:
    image: your-registry/youtube-analyzer:latest
    environment:
      - OLLAMA_HOST=your-ollama-service:11434
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
    deploy:
      replicas: 2
      resources:
        limits:
          memory: 4G
        reservations:
          memory: 2G
```

## 🔄 Continuous Integration/Deployment

### GitHub Actions (Future Enhancement)
```yaml
# .github/workflows/ci.yml
name: CI/CD Pipeline

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: 3.11
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
      - name: Run tests
        run: |
          pytest tests/
      - name: Build Docker image
        run: |
          docker build -t youtube-analyzer:${{ github.sha }} .
```

## 📝 Code Standards

### Python Code Standards
```python
# Follow PEP 8 style guide
# Use type hints
from typing import Dict, List, Optional, Any

async def process_video(
    url: str,
    model: str = "llama3.1:8b",
    max_segments: int = 5
) -> Dict[str, Any]:
    """
    Process video with comprehensive type hints and documentation.
    
    Args:
        url: Video URL to process
        model: AI model to use for summarization
        max_segments: Maximum number of segments to analyze
        
    Returns:
        Dictionary containing processed video information
        
    Raises:
        ValueError: If URL is invalid
        Exception: If processing fails
    """
    pass
```

### JavaScript Code Standards
```javascript
// Use ES6+ features
// Follow consistent naming conventions
// Add JSDoc comments

/**
 * Handle WebSocket message processing
 * @param {Object} data - WebSocket message data
 * @param {string} data.status - Message status
 * @param {string} data.message - Message content
 * @param {number} data.progress - Progress percentage
 */
handleWebSocketMessage(data) {
    const { status, message, progress } = data;
    
    switch (status) {
        case 'processing':
            this.updateProgress(progress, message);
            break;
        default:
            console.warn('Unknown message status:', status);
    }
}
```

## 📚 Documentation Standards

### Code Documentation
- **Python**: Use docstrings with Google style
- **JavaScript**: Use JSDoc comments
- **API**: Document all endpoints with OpenAPI/Swagger
- **Configuration**: Document all environment variables

### File Documentation
- **README.md**: Comprehensive overview
- **SETUP.md**: Installation and setup
- **TROUBLESHOOTING.md**: Common issues and solutions
- **DEVELOPMENT_WORKFLOW.md**: Development guidelines (this file)

## 🤝 Contributing Guidelines

### Pull Request Process
1. **Fork the repository**
2. **Create feature branch**: `git checkout -b feature/your-feature`
3. **Make changes** with proper testing
4. **Update documentation** as needed
5. **Submit pull request** with clear description

### Code Review Checklist
- [ ] Code follows style guidelines
- [ ] Tests are included and passing
- [ ] Documentation is updated
- [ ] No breaking changes without discussion
- [ ] Performance impact is considered
- [ ] Security implications are reviewed

### Issue Reporting
- **Use issue templates** when available
- **Include system information** and logs
- **Provide reproduction steps**
- **Add labels** for categorization

---

**Remember**: This is a living document. Update it as the project evolves and new patterns emerge. Focus on maintainability, scalability, and developer experience.
