# YouTube & Conference Video Analyzer

A comprehensive AI-powered video analysis application that generates intelligent summaries of YouTube videos and conference recordings using multiple AI model providers. Built with FastAPI, featuring real-time progress tracking, multi-provider AI model support, and advanced video processing capabilities.

## 🚀 Key Features

### Video Processing
- **YouTube Video Analysis**: Process any public YouTube video using yt-dlp with multiple retry strategies
- **Conference Video Support**: Download and analyze conference recordings (Zoom, Teams, WebEx, etc.)
- **Authentication Support**: Handle password-protected conference videos
- **Real-time Progress**: WebSocket-based progress tracking with detailed status updates
- **Intelligent Segmentation**: Automatic identification of key video segments using TF-IDF analysis
- **Robust Download Logic**: Multiple extraction strategies with exponential backoff for reliability

### AI Model Support
- **Multi-Provider Architecture**: Support for Ollama, OpenAI, and Anthropic models
- **Dynamic Model Selection**: Choose from any installed model via web interface
- **Real-time Provider Status**: Monitor availability of all AI providers
- **API Key Management**: Secure handling of external API keys with validation
- **Cost Optimization**: Automatic selection of free models when available

### Enhanced Summaries
- **Segment-Level Analysis**: Detailed summaries for each key segment with timestamps
- **Overall Video Summary**: Comprehensive 4-sentence summary explaining video purpose and value
- **Theme Extraction**: Automatic identification of main themes and topics
- **Key Takeaways**: Actionable insights and important conclusions
- **Importance Scoring**: Relevance scoring for each segment using TF-IDF analysis
- **Structured Output**: Consistent parsing of AI-generated summaries with fallback mechanisms

### Export & Integration
- **Multiple Export Formats**: Export summaries as text or JSON
- **Responsive Web Interface**: Clean, modern UI that works on all devices
- **Computer Use Integration**: Advanced automation capabilities for complex workflows
- **Docker Support**: Multiple deployment configurations for different use cases

## 🏗️ Architecture

### Core Components
- **Backend**: Python FastAPI with async processing and WebSocket support
- **Frontend**: Vanilla JavaScript with real-time WebSocket communication
- **Model Manager**: Unified interface for multiple AI providers (Ollama, OpenAI, Anthropic)
- **Video Services**: Specialized services for YouTube and conference video processing
- **Transcription**: OpenAI Whisper for high-quality speech-to-text conversion

### AI Model Providers
- **Ollama**: Local LLM inference (llama3.1, mistral, and other models)
- **OpenAI**: GPT-4, GPT-3.5-turbo, and other OpenAI models
- **Anthropic**: Claude 3.5 Sonnet, Claude 3 Haiku, and other Claude models

### Processing Pipeline
1. **Video Detection**: Automatic detection of video type (YouTube/Conference)
2. **Video Download**: Intelligent download with retry logic and anti-bot measures
3. **Audio Processing**: Segmentation and optimization for transcription
4. **Speech-to-Text**: High-quality transcription using OpenAI Whisper
5. **Content Analysis**: Key segment identification using TF-IDF and importance scoring
6. **AI Summarization**: Multi-provider summary generation with selected model
7. **Result Assembly**: Comprehensive results with timestamps, themes, and takeaways

## 🛠️ Installation

### Prerequisites
- Python 3.9+ (recommended: 3.11)
- FFmpeg
- 8GB+ RAM (for AI models)
- 10GB+ storage (for models and temporary files)

### Quick Start Options

#### Option 1: Docker (Recommended)
```bash
# Clone the repository
git clone https://github.com/Hydroxide538/Youtube-Analyzer.git
cd Youtube-Analyzer

# Run with Docker Compose
docker-compose up --build

# Access the application at http://localhost:8000
```

#### Option 2: Local Development
```bash
# Clone repository
git clone https://github.com/Hydroxide538/Youtube-Analyzer.git
cd Youtube-Analyzer

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install and setup Ollama (for local models)
curl -fsSL https://ollama.ai/install.sh | sh
ollama serve &
ollama pull llama3.1:8b

# Run the application
python scripts/run.py
```

#### Option 3: External Ollama Setup
If you already have Ollama running in a separate container:
```bash
# Use the external Ollama configuration
docker-compose -f docker-compose.external-ollama.yml up --build
```

### API Key Configuration (Optional)
To use OpenAI or Anthropic models, configure API keys:

1. **Through Environment Variables:**
   ```bash
   export OPENAI_API_KEY="sk-your-openai-key"
   export ANTHROPIC_API_KEY="sk-ant-your-anthropic-key"
   ```

2. **Through Web Interface:**
   - Click "Advanced Options" in the web interface
   - Enter your API keys in the provided fields
   - Click "Test API Keys" to verify connectivity
   - Click "Refresh Models" to load available models

## 🎯 Usage

### Basic Video Analysis
1. **Open Application**: Navigate to http://localhost:8000
2. **Select Video Type**: Choose YouTube, Conference, or Auto-detect
3. **Enter URL**: Paste video URL (YouTube or conference recording)
4. **Configure Options** (optional): 
   - Select AI model (Ollama, OpenAI, or Anthropic)
   - Adjust max segments (3-10)
   - Set segment length (30-120 seconds)
5. **Start Analysis**: Click "Analyze Video"
6. **Monitor Progress**: Watch real-time processing updates
7. **Review Results**: Examine summaries, themes, and key takeaways
8. **Export**: Download results as text or JSON

### Conference Video Analysis
1. **Select Conference Type**: Choose "Conference Video" from video type dropdown
2. **Enter Conference URL**: Paste Zoom, Teams, WebEx, or other conference URL
3. **Authentication** (if required):
   - Enter username/email
   - Enter password
4. **Start Analysis**: The system will authenticate and process the video

### Advanced Features
- **Model Selection**: Choose from any installed Ollama model or external API models
- **Provider Status**: Monitor real-time status of all AI providers
- **API Key Testing**: Validate API keys and test connectivity
- **Custom Segmentation**: Adjust segment length and maximum segments
- **Export Options**: Download summaries in multiple formats

## 📊 Model Provider Details

### Ollama (Local)
- **Advantages**: Free, private, offline capable
- **Models**: llama3.1:8b, mistral:7b, and any other installed models
- **Requirements**: Local installation, significant RAM usage
- **Cost**: Free

### OpenAI (Cloud)
- **Advantages**: High quality, fast processing, latest models
- **Models**: GPT-4, GPT-3.5-turbo, GPT-4-turbo
- **Requirements**: API key, internet connection
- **Cost**: Pay per token (varies by model)

### Anthropic (Cloud)
- **Advantages**: Excellent reasoning, safety-focused, high quality
- **Models**: Claude 3.5 Sonnet, Claude 3 Haiku, Claude 3 Opus
- **Requirements**: API key, internet connection
- **Cost**: Pay per token (varies by model)

## 🔧 Configuration

### Environment Variables
```bash
# AI Provider Configuration
OLLAMA_HOST=localhost:11434          # Ollama server host
OPENAI_API_KEY=sk-your-key          # OpenAI API key (optional)
ANTHROPIC_API_KEY=sk-ant-your-key   # Anthropic API key (optional)

# Application Configuration
PYTHONPATH=/app                      # Python path for imports
HOST=0.0.0.0                       # Server host
PORT=8000                           # Server port
```

### Docker Configurations
- **docker-compose.yml**: Standard configuration with internal Ollama
- **docker-compose.external-ollama.yml**: Connect to existing Ollama container
- **docker-compose.bridge.yml**: Bridge networking for complex setups
- **docker-compose.dev.yml**: Development configuration with live reload

### Processing Parameters
Adjust in web interface or modify `app/models/request_models.py`:
```python
max_segments: int = 5        # Maximum key segments to analyze
segment_length: int = 60     # Segment length in seconds
```

## 🚨 Troubleshooting

### Common Issues

#### Model Provider Issues
- **Ollama not available**: Ensure Ollama is running (`ollama serve`)
- **API key errors**: Verify API key format and test connectivity
- **No models available**: Check provider status and refresh models

#### Video Processing Issues
- **YouTube 403 errors**: Application includes anti-bot measures, but some videos may be restricted
- **Conference video authentication**: Ensure correct credentials and supported platform
- **FFmpeg errors**: Install FFmpeg for your operating system

#### Performance Issues
- **Memory usage**: Reduce segment length or use smaller models
- **Slow processing**: Consider using cloud models for faster processing
- **Storage space**: Clean up temporary files regularly

### Diagnostic Steps
1. **Check Provider Status**: View real-time provider availability in web interface
2. **Test API Keys**: Use built-in API key testing functionality
3. **Review Logs**: Check console output for detailed error messages
4. **Verify Dependencies**: Ensure FFmpeg and Python dependencies are installed

For detailed troubleshooting, see [TROUBLESHOOTING.md](TROUBLESHOOTING.md).

## 📈 Performance

### Expected Processing Times
- **Short video (5-10 min)**: 1-3 minutes
- **Medium video (20-30 min)**: 3-8 minutes
- **Long video (60+ min)**: 8-15 minutes

*Times vary based on selected model and system specifications*

### System Requirements
- **Minimum**: 4GB RAM, 2 CPU cores, 5GB storage
- **Recommended**: 8GB+ RAM, 4+ CPU cores, 10GB+ storage
- **Optimal**: 16GB+ RAM, 8+ CPU cores, 20GB+ storage

## 🔒 Security & Privacy

### Data Handling
- **Local Processing**: Transcription and analysis can be performed entirely locally
- **Temporary Files**: Automatically cleaned up after processing
- **API Keys**: Securely handled with optional environment variable storage
- **No Data Retention**: No video content or summaries are permanently stored

### Conference Video Security
- **Authentication**: Secure handling of conference credentials
- **Encrypted Downloads**: Support for password-protected content
- **Session Management**: Proper cleanup of authentication sessions

## 🛠️ Development

### Project Structure
```
youtube-analyzer/
├── app/
│   ├── main.py                 # FastAPI application
│   ├── models/                 # Pydantic models
│   ├── services/               # Business logic services
│   │   ├── model_manager.py    # Multi-provider model management
│   │   ├── youtube_service.py  # YouTube video processing
│   │   ├── conference_video_service.py  # Conference video processing
│   │   ├── transcription_service.py     # Whisper transcription
│   │   └── summarization_service.py     # AI summarization
│   └── utils/                  # Utility functions
├── static/                     # Frontend assets
├── templates/                  # HTML templates
├── docker/                     # Docker configurations
├── scripts/                    # Helper scripts
└── docs/                       # Documentation
```

### Adding New Features
1. **Backend**: Add new endpoints in `app/main.py`
2. **Services**: Extend functionality in `app/services/`
3. **Models**: Add new Pydantic models in `app/models/`
4. **Frontend**: Modify `static/js/app.js` and `templates/index.html`

### Testing
```bash
# Run the application locally
python scripts/run.py

# Test with various video types
python scripts/test_static_files.py

# Test GPU setup (if available)
python scripts/test_gpu_setup.py
```

## 📚 Additional Documentation

- [SETUP.md](SETUP.md) - Quick setup guide
- [TROUBLESHOOTING.md](TROUBLESHOOTING.md) - Detailed troubleshooting
- [DOCKER_USAGE.md](DOCKER_USAGE.md) - Docker deployment guide
- [DEVELOPMENT_WORKFLOW.md](DEVELOPMENT_WORKFLOW.md) - Development guidelines
- [EXTERNAL_OLLAMA_SETUP.md](EXTERNAL_OLLAMA_SETUP.md) - External Ollama configuration

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly with different video types and models
5. Submit a pull request

## 📄 License

This project is open source and available under the MIT License.

## 🙏 Acknowledgments

- [OpenAI Whisper](https://github.com/openai/whisper) for speech recognition
- [Ollama](https://ollama.ai) for local LLM inference
- [OpenAI](https://openai.com) for GPT models
- [Anthropic](https://anthropic.com) for Claude models
- [yt-dlp](https://github.com/yt-dlp/yt-dlp) for YouTube video downloading
- [FastAPI](https://fastapi.tiangolo.com) for the web framework
- [Selenium](https://selenium.dev) for conference video automation

## 📞 Support

For issues and questions:
1. Check the [troubleshooting guide](TROUBLESHOOTING.md)
2. Review application logs for error details
3. Test with different models and video types
4. Create an issue in the repository with detailed information

---

**Note**: This application is designed for educational and personal use. Please respect content creators' rights and platform terms of service when using this tool.
