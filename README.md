# YouTube Video Summarizer

A lightweight, offline-capable application that generates AI-powered summaries of YouTube videos using local processing. Built with FastAPI, Whisper for transcription, and Ollama for local LLM summarization.

## Features

- **Offline Processing**: No external APIs required - everything runs locally
- **Real-time Progress**: WebSocket-based progress tracking
- **Key Segment Analysis**: Identifies and summarizes the most important parts of videos
- **Multiple Export Formats**: Export summaries as text or JSON
- **Responsive Web Interface**: Clean, modern UI that works on desktop and mobile
- **Docker Support**: Easy deployment with Docker containers

## Architecture

- **Backend**: Python FastAPI with async processing
- **Frontend**: Vanilla JavaScript with WebSocket communication
- **Transcription**: OpenAI Whisper for speech-to-text
- **Summarization**: Ollama with Llama 3.1 for local AI processing
- **Video Processing**: yt-dlp for YouTube downloads, pydub for audio processing

## Prerequisites

### For Local Development
- Python 3.9+ (recommended: 3.11)
- FFmpeg
- Ollama installed and running
- 8GB+ RAM (for AI model)
- 10GB+ storage (for models)

### For Docker Deployment
- Docker and Docker Compose
- 8GB+ RAM
- 10GB+ storage

## Installation

### Option 1: Local Development Setup

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd youtube-analyzer
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Install and setup Ollama**
   ```bash
   # Install Ollama (visit https://ollama.ai for platform-specific instructions)
   curl -fsSL https://ollama.ai/install.sh | sh
   
   # Start Ollama service
   ollama serve
   
   # In another terminal, pull the model
   ollama pull llama3.1:8b
   ```

5. **Run the application**
   ```bash
   python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
   ```

6. **Access the application**
   Open your browser and go to `http://localhost:8000`

### Option 2: Docker Deployment

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd youtube-analyzer
   ```

2. **Build and run with Docker Compose**
   ```bash
   docker-compose up --build
   ```

3. **Access the application**
   Open your browser and go to `http://localhost:8000`

## Usage

1. **Enter YouTube URL**: Paste any YouTube video URL into the input field
2. **Configure Options** (optional): Click "Advanced Options" to adjust:
   - Maximum number of key segments (3-10)
   - Segment length (30-120 seconds)
3. **Start Processing**: Click "Analyze Video" to begin
4. **Monitor Progress**: Watch real-time progress through the processing pipeline:
   - Download video
   - Process audio
   - Transcribe speech
   - Analyze content
   - Generate summaries
5. **View Results**: Review the generated summaries with timestamps and key points
6. **Export**: Download results as text or JSON format

## Processing Pipeline

1. **Video Download**: Downloads audio track from YouTube using yt-dlp
2. **Audio Segmentation**: Splits audio into manageable chunks (30-120 seconds)
3. **Transcription**: Converts audio to text using Whisper
4. **Content Analysis**: Identifies key segments using TF-IDF and importance scoring
5. **AI Summarization**: Generates summaries using local Ollama LLM
6. **Result Assembly**: Combines summaries with timestamps and metadata

## Configuration

### Environment Variables

- `PYTHONPATH`: Set to `/app` for proper module imports
- `OLLAMA_HOST`: Ollama server host (default: `0.0.0.0:11434`)

### Model Configuration

The application now supports dynamic model selection! Users can choose from any installed Ollama models via the web interface. The Docker container comes pre-installed with:

- **llama3.1:8b** (Default - balanced performance)
- **mistral:7b** (Faster, smaller model)

To add more models to the Docker container, modify the Dockerfile:

```dockerfile
RUN ollama serve & \
    sleep 10 && \
    ollama pull llama3.1:8b && \
    ollama pull mistral:7b && \
    ollama pull your-model-here && \
    pkill ollama
```

Or install models at runtime:
```bash
docker exec -it youtube-summarizer ollama pull model-name
```

### Processing Parameters

Adjust processing parameters in the frontend or modify defaults in `app/models/request_models.py`:

```python
class VideoRequest(BaseModel):
    max_segments: Optional[int] = 5
    segment_length: Optional[int] = 60  # seconds
```

## Performance

### Expected Processing Times
- **Small video (5-10 min)**: 2-3 minutes
- **Medium video (20-30 min)**: 5-8 minutes  
- **Large video (60+ min)**: 10-15 minutes

### System Requirements
- **Minimum**: 4GB RAM, 2 CPU cores
- **Recommended**: 8GB+ RAM, 4+ CPU cores
- **Storage**: 10GB+ for models and temporary files

## Troubleshooting

### Common Issues

1. **Ollama Connection Failed**
   - Ensure Ollama is running: `ollama serve`
   - Check if model is installed: `ollama list`
   - Pull model if missing: `ollama pull llama3.1:8b`

2. **FFmpeg Not Found**
   - Install FFmpeg: `apt-get install ffmpeg` (Linux) or `brew install ffmpeg` (macOS)

3. **Memory Issues**
   - Reduce segment length in advanced options
   - Use smaller Ollama model (e.g., `llama3.1:7b`)
   - Increase Docker memory limits

4. **YouTube Download Fails**
   - Check internet connection
   - Verify YouTube URL format
   - Some videos may be restricted

### Logs and Debugging

- Application logs are available in the console
- WebSocket connection status is shown in browser developer tools
- Docker logs: `docker-compose logs -f youtube-summarizer`

## Development

### Project Structure
```
youtube-analyzer/
├── app/
│   ├── main.py                 # FastAPI application
│   ├── models/                 # Pydantic models
│   ├── services/               # Business logic services
│   └── utils/                  # Utility functions
├── static/
│   ├── css/                    # Stylesheets
│   └── js/                     # JavaScript files
├── templates/                  # HTML templates
├── requirements.txt            # Python dependencies
├── Dockerfile                  # Docker configuration
├── docker-compose.yml          # Docker Compose setup
└── README.md                   # This file
```

### Adding New Features

1. **Backend**: Add new endpoints in `app/main.py`
2. **Services**: Extend functionality in `app/services/`
3. **Frontend**: Modify `static/js/app.js` and `templates/index.html`
4. **Styling**: Update `static/css/style.css`

### Testing

Run the application locally and test with various YouTube videos:
- Short videos (< 5 minutes)
- Medium videos (5-30 minutes)
- Long videos (> 30 minutes)
- Different content types (educational, entertainment, etc.)

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

This project is open source and available under the MIT License.

## Acknowledgments

- [OpenAI Whisper](https://github.com/openai/whisper) for speech recognition
- [Ollama](https://ollama.ai) for local LLM inference
- [yt-dlp](https://github.com/yt-dlp/yt-dlp) for YouTube video downloading
- [FastAPI](https://fastapi.tiangolo.com) for the web framework

## Support

For issues and questions:
1. Check the troubleshooting section above
2. Review application logs
3. Create an issue in the repository

---

**Note**: This application is designed for educational and personal use. Please respect YouTube's terms of service and content creators' rights when using this tool.
