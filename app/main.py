from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi import Request
import asyncio
import json
import logging
from typing import Dict, Any, List
import os
import subprocess

from .services.youtube_service import YouTubeService
from .services.transcription_service import TranscriptionService
from .services.summarization_service import SummarizationService
from .models.request_models import VideoRequest
from .utils.websocket_manager import WebSocketManager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="YouTube Video Summarizer", version="1.0.0")

# Mount static files and templates
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Initialize services
youtube_service = YouTubeService()
transcription_service = TranscriptionService()
summarization_service = SummarizationService()
websocket_manager = WebSocketManager()

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    """Serve the main page"""
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/api/models")
async def get_available_models():
    """Get list of available Ollama models"""
    try:
        # Get Ollama host from environment variable
        ollama_host = os.getenv('OLLAMA_HOST', 'localhost:11434')
        
        # Use curl to get models from Ollama API instead of ollama CLI
        result = subprocess.run(['curl', '-s', f'http://{ollama_host}/api/tags'], 
                              capture_output=True, text=True, timeout=10)
        
        if result.returncode != 0:
            logger.error(f"Ollama API request failed: {result.stderr}")
            raise HTTPException(status_code=500, detail="Failed to fetch models from Ollama")
        
        # Parse the JSON response from Ollama API
        try:
            ollama_response = json.loads(result.stdout)
            models = []
            
            if 'models' in ollama_response:
                for model in ollama_response['models']:
                    model_name = model.get('name', 'Unknown')
                    model_size = model.get('size', 0)
                    
                    # Convert size to human readable format
                    if model_size > 0:
                        if model_size > 1024**3:  # GB
                            size_str = f"{model_size / (1024**3):.1f}GB"
                        elif model_size > 1024**2:  # MB
                            size_str = f"{model_size / (1024**2):.1f}MB"
                        else:
                            size_str = f"{model_size}B"
                    else:
                        size_str = "Unknown"
                    
                    models.append({
                        "name": model_name,
                        "id": model.get('digest', ''),
                        "size": size_str,
                        "modified": model.get('modified_at', ''),
                        "display_name": f"{model_name} ({size_str})"
                    })
            
            if not models:
                # Return a default model if none found
                models.append({
                    "name": "llama3.1:8b",
                    "id": "",
                    "size": "4.7GB",
                    "modified": "",
                    "display_name": "llama3.1:8b (4.7GB)"
                })
            
            return {"models": models}
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse Ollama API response: {e}")
            raise HTTPException(status_code=500, detail="Invalid response from Ollama API")
    
    except subprocess.TimeoutExpired:
        logger.error("Ollama list command timed out")
        raise HTTPException(status_code=500, detail="Ollama service is not responding")
    except Exception as e:
        logger.error(f"Error fetching models: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error fetching models: {str(e)}")

@app.post("/api/summarize")
async def summarize_video(video_request: VideoRequest):
    """
    Main endpoint to process and summarize a YouTube video
    """
    try:
        # Validate YouTube URL
        if not youtube_service.is_valid_youtube_url(video_request.url):
            raise HTTPException(status_code=400, detail="Invalid YouTube URL")
        
        # Start processing (this will be handled via WebSocket for real-time updates)
        return {"message": "Processing started", "status": "accepted"}
    
    except Exception as e:
        logger.error(f"Error in summarize_video: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint for real-time processing updates
    """
    await websocket_manager.connect(websocket)
    try:
        while True:
            # Wait for video URL from client
            data = await websocket.receive_text()
            request_data = json.loads(data)
            
            if request_data.get("action") == "process_video":
                url = request_data.get("url")
                selected_model = request_data.get("model", "llama3.1:8b")
                max_segments = request_data.get("max_segments", 5)
                segment_length = request_data.get("segment_length", 60)
                
                await process_video_pipeline(websocket, url, selected_model, max_segments, segment_length)
            
    except WebSocketDisconnect:
        websocket_manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {str(e)}")
        await websocket.send_text(json.dumps({
            "status": "error",
            "message": str(e)
        }))

async def process_video_pipeline(websocket: WebSocket, url: str, selected_model: str = "llama3.1:8b", max_segments: int = 5, segment_length: int = 60):
    """
    Main processing pipeline for video summarization
    """
    try:
        # Create a new summarization service instance with the selected model
        custom_summarization_service = SummarizationService(model_name=selected_model)
        
        # Validate that the selected model is available
        model_available = await custom_summarization_service.check_ollama_connection()
        if not model_available:
            await websocket.send_text(json.dumps({
                "status": "error",
                "message": f"Selected model '{selected_model}' is not available. Please ensure it's installed.",
                "progress": 0
            }))
            return
        
        # Step 1: Download video
        await websocket.send_text(json.dumps({
            "status": "downloading",
            "message": "Downloading video...",
            "progress": 10
        }))
        
        video_info = await youtube_service.download_video(url)
        
        # Step 2: Extract and segment audio
        await websocket.send_text(json.dumps({
            "status": "processing_audio",
            "message": "Processing audio...",
            "progress": 30
        }))
        
        audio_segments = await youtube_service.extract_audio_segments(video_info["audio_path"], segment_length)
        
        # Step 3: Transcribe audio segments
        await websocket.send_text(json.dumps({
            "status": "transcribing",
            "message": "Transcribing audio...",
            "progress": 50
        }))
        
        transcriptions = await transcription_service.transcribe_segments(audio_segments)
        
        # Step 4: Identify key segments
        await websocket.send_text(json.dumps({
            "status": "analyzing",
            "message": "Analyzing content...",
            "progress": 70
        }))
        
        key_segments = await transcription_service.identify_key_segments(transcriptions, max_segments)
        
        # Step 5: Generate summaries using selected model
        await websocket.send_text(json.dumps({
            "status": "summarizing",
            "message": f"Generating summaries using {selected_model}...",
            "progress": 90
        }))
        
        summaries = await custom_summarization_service.summarize_segments(key_segments)
        
        # Step 6: Send final result
        await websocket.send_text(json.dumps({
            "status": "completed",
            "message": "Processing completed!",
            "progress": 100,
            "result": {
                "video_title": video_info["title"],
                "video_duration": video_info["duration"],
                "summaries": summaries,
                "model_used": selected_model,
                "processing_settings": {
                    "max_segments": max_segments,
                    "segment_length": segment_length
                }
            }
        }))
        
        # Cleanup temporary files
        await youtube_service.cleanup_files(video_info["audio_path"])
        
    except Exception as e:
        logger.error(f"Pipeline error: {str(e)}")
        await websocket.send_text(json.dumps({
            "status": "error",
            "message": f"Processing failed: {str(e)}",
            "progress": 0
        }))

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "message": "YouTube Summarizer API is running"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
