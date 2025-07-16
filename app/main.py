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
from .services.conference_video_service import ConferenceVideoService
from .services.transcription_service import TranscriptionService
from .services.model_manager import ModelManager
from .models.request_models import VideoRequest, ConferenceVideoRequest
from .utils.websocket_manager import WebSocketManager
from .config import config

# Configure logging based on config
logging.basicConfig(level=getattr(logging, config.server.log_level))
logger = logging.getLogger(__name__)

# Log configuration on startup
config.log_configuration()

app = FastAPI(title="YouTube Video Summarizer", version="1.0.0")

# Mount static files and templates - use absolute paths for Docker container
app.mount("/static", StaticFiles(directory="/app/static"), name="static")
templates = Jinja2Templates(directory="/app/templates")

# Initialize services
youtube_service = YouTubeService(config.computer_use.__dict__)
conference_video_service = ConferenceVideoService()
transcription_service = TranscriptionService()
websocket_manager = WebSocketManager()
model_manager = ModelManager()

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    """Serve the main page"""
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/api/models")
async def get_available_models():
    """Get list of available models from all providers"""
    try:
        # Initialize model manager if not already done
        if not model_manager.initialized:
            await model_manager.initialize(
                openai_api_key=config.openai.api_key,
                anthropic_api_key=config.anthropic.api_key,
                ollama_host=config.ollama.host
            )
        
        # Get all available models
        models = await model_manager.get_all_models()
        
        # Get detailed provider status with real-time checks
        provider_status = await model_manager.get_detailed_provider_status()
        
        if not models:
            # Return a default model if none found
            models = [{
                "name": "llama3.1:8b",
                "id": "",
                "size": "4.7GB",
                "modified": "",
                "display_name": "llama3.1:8b (4.7GB) - Ollama",
                "provider": "Ollama",
                "description": "Default Ollama model",
                "cost_per_token": 0.0
            }]
        
        return {
            "models": models,
            "providers": provider_status["providers"]
        }
        
    except Exception as e:
        logger.error(f"Error fetching models: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error loading models. Please check if providers are running: {str(e)}")

@app.post("/api/models")
async def get_available_models_with_keys(request: dict):
    """Get list of available models with provided API keys"""
    try:
        # Extract API keys from request
        openai_key = request.get('openai_api_key')
        anthropic_key = request.get('anthropic_api_key')
        test_only = request.get('test_only', False)
        
        # Use configuration as fallback
        openai_key = openai_key or config.openai.api_key
        anthropic_key = anthropic_key or config.anthropic.api_key
        
        # Create a new model manager instance with the provided keys
        temp_model_manager = ModelManager()
        await temp_model_manager.initialize(
            openai_api_key=openai_key,
            anthropic_api_key=anthropic_key,
            ollama_host=config.ollama.host
        )
        
        # Get all available models
        models = await temp_model_manager.get_all_models()
        
        if not models:
            # Return a default model if none found
            models = [{
                "name": "llama3.1:8b",
                "id": "",
                "size": "4.7GB",
                "modified": "",
                "display_name": "llama3.1:8b (4.7GB) - Ollama",
                "provider": "Ollama",
                "description": "Default Ollama model",
                "cost_per_token": 0.0
            }]
        
        # Get provider status
        provider_status = temp_model_manager.get_provider_status()
        
        # If this is just a test, also run connection tests
        if test_only:
            connection_tests = await temp_model_manager.test_all_connections()
            return {
                "models": models,
                "providers": provider_status,
                "connection_tests": connection_tests
            }
        
        # Update the global model manager if successful
        global model_manager
        model_manager = temp_model_manager
        
        return {
            "models": models,
            "providers": provider_status
        }
        
    except Exception as e:
        logger.error(f"Error fetching models with API keys: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error loading models with API keys: {str(e)}")

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
                video_type = request_data.get("video_type", "auto")
                username = request_data.get("username")
                password = request_data.get("password")
                
                await process_video_pipeline(websocket, url, selected_model, max_segments, segment_length, video_type, username, password)
            
    except WebSocketDisconnect:
        websocket_manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {str(e)}")
        await websocket.send_text(json.dumps({
            "status": "error",
            "message": str(e)
        }))

async def process_video_pipeline(websocket: WebSocket, url: str, selected_model: str = "llama3.1:8b", max_segments: int = 5, segment_length: int = 60, video_type: str = "auto", username: str = None, password: str = None):
    """
    Main processing pipeline for video summarization
    """
    try:
        # Initialize model manager if not already done
        if not model_manager.initialized:
            await model_manager.initialize(
                openai_api_key=config.openai.api_key,
                anthropic_api_key=config.anthropic.api_key,
                ollama_host=config.ollama.host
            )
        
        # Validate that the selected model is available
        model_info = model_manager.get_model_info(selected_model)
        if not model_info:
            await websocket.send_text(json.dumps({
                "status": "error",
                "message": f"Selected model '{selected_model}' is not available. Please check that the provider is running.",
                "progress": 0
            }))
            return
        
        provider_name = model_info.get('provider', 'Unknown')
        await websocket.send_text(json.dumps({
            "status": "initializing",
            "message": f"Using {selected_model} from {provider_name}",
            "progress": 5
        }))
        
        # Determine video type if auto
        if video_type == "auto":
            if youtube_service.is_valid_youtube_url(url):
                video_type = "youtube"
            elif conference_video_service.is_valid_conference_url(url):
                video_type = "conference"
            else:
                raise Exception("Unable to determine video type. Please specify video type manually.")
        
        # Step 1: Download video
        await websocket.send_text(json.dumps({
            "status": "downloading",
            "message": f"Downloading {video_type} video...",
            "progress": 10
        }))
        
        if video_type == "youtube":
            video_info = await youtube_service.download_video(url)
            service_to_use = youtube_service
        elif video_type == "conference":
            video_info = await conference_video_service.download_conference_video(url, username, password)
            service_to_use = conference_video_service
        else:
            raise Exception(f"Unsupported video type: {video_type}")
        
        # Step 2: Extract and segment audio
        await websocket.send_text(json.dumps({
            "status": "processing_audio",
            "message": "Processing audio...",
            "progress": 30
        }))
        
        # Ensure we have a valid audio path
        if not video_info.get("audio_path") or not os.path.exists(video_info["audio_path"]):
            raise Exception("Audio file not found or invalid")
        
        audio_segments = await service_to_use.extract_audio_segments(video_info["audio_path"], segment_length)
        
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
            "progress": 80
        }))
        
        summaries = await generate_summaries_with_model_manager(key_segments, selected_model)
        
        # Step 6: Generate overall summary
        await websocket.send_text(json.dumps({
            "status": "overall_summary",
            "message": "Generating overall summary...",
            "progress": 95
        }))
        
        overall_summary = await generate_overall_summary_with_model_manager(
            summaries, video_info["title"], video_info["duration"], selected_model
        )
        
        # Step 7: Send final result
        await websocket.send_text(json.dumps({
            "status": "completed",
            "message": "Processing completed!",
            "progress": 100,
            "result": {
                "video_title": video_info["title"],
                "video_duration": video_info["duration"],
                "summaries": summaries,
                "overall_summary": overall_summary,
                "model_used": selected_model,
                "video_type": video_type,
                "source_url": url,
                "processing_settings": {
                    "max_segments": max_segments,
                    "segment_length": segment_length
                }
            }
        }))
        
        # Cleanup temporary files
        await service_to_use.cleanup_files(video_info["audio_path"])
        
    except Exception as e:
        logger.error(f"Pipeline error: {str(e)}")
        await websocket.send_text(json.dumps({
            "status": "error",
            "message": f"Processing failed: {str(e)}",
            "progress": 0
        }))

async def generate_summaries_with_model_manager(key_segments: List[Dict[str, Any]], selected_model: str) -> List[Dict[str, Any]]:
    """Generate summaries for key segments using the model manager"""
    summaries = []
    
    for i, segment in enumerate(key_segments):
        try:
            logger.info(f"Summarizing segment {i+1}/{len(key_segments)}")
            
            # Generate summary for this segment
            summary_data = await generate_segment_summary_with_model_manager(segment, selected_model)
            
            summaries.append({
                'start_time': segment['start_time'],
                'end_time': segment['end_time'],
                'timestamp': format_timestamp(segment['start_time']),
                'duration': segment['duration'],
                'original_transcript': segment['transcript'],
                'summary': summary_data['summary'],
                'key_points': summary_data['key_points'],
                'importance_score': segment.get('importance_score', 0.0),
                'confidence': segment.get('confidence', 0.0)
            })
            
        except Exception as e:
            logger.error(f"Error summarizing segment {i}: {str(e)}")
            # Add fallback summary
            summaries.append({
                'start_time': segment['start_time'],
                'end_time': segment['end_time'],
                'timestamp': format_timestamp(segment['start_time']),
                'duration': segment['duration'],
                'original_transcript': segment['transcript'],
                'summary': f"Summary unavailable. Original transcript: {segment['transcript'][:200]}...",
                'key_points': [],
                'importance_score': segment.get('importance_score', 0.0),
                'confidence': 0.0
            })
    
    return summaries

async def generate_segment_summary_with_model_manager(segment: Dict[str, Any], selected_model: str) -> Dict[str, Any]:
    """Generate summary and key points for a single segment using model manager"""
    transcript = segment['transcript']
    
    if not transcript.strip():
        return {
            'summary': "No content available for this segment.",
            'key_points': []
        }
    
    # Create prompt for summarization
    prompt = create_summarization_prompt(transcript, segment)
    
    try:
        # Call model manager to generate summary
        content = await model_manager.generate_summary(selected_model, prompt, max_tokens=300)
        return parse_summary_response(content)
        
    except Exception as e:
        logger.error(f"Error calling model manager for summary: {str(e)}")
        # Fallback to simple extractive summary
        return create_fallback_summary(transcript)

async def generate_overall_summary_with_model_manager(segment_summaries: List[Dict[str, Any]], video_title: str, video_duration: float, selected_model: str) -> Dict[str, Any]:
    """Generate an enhanced overall summary of the entire video using model manager"""
    try:
        # Combine all segment summaries with better context
        combined_content = []
        all_key_points = []
        
        for i, segment in enumerate(segment_summaries):
            combined_content.append(f"Segment {i+1} ({segment['timestamp']}): {segment['summary']}")
            if segment.get('key_points'):
                all_key_points.extend(segment['key_points'])
        
        combined_text = '\n\n'.join(combined_content)
        key_points_text = '\n'.join([f"• {point}" for point in all_key_points[:10]])  # Top 10 key points
        
        # Enhanced prompt for better overall summary
        prompt = f"""
You are analyzing a YouTube video titled "{video_title}" (Duration: {format_timestamp(video_duration)}).

SEGMENT SUMMARIES:
{combined_text}

ALL KEY POINTS FROM VIDEO:
{key_points_text}

Your task is to create a comprehensive analysis that answers: "What is this video about?"

Please provide:

1. OVERALL_SUMMARY: Write exactly 4 sentences that clearly explain:
   - What the video is about (main topic/subject)
   - Who the target audience is or what the purpose is
   - The key message or main argument being made
   - The value or outcome viewers can expect

2. MAIN_THEMES: List 3-5 main themes or topics covered (single words or short phrases)

3. KEY_TAKEAWAYS: List 3-5 most important actionable insights or conclusions

Focus on creating a summary that someone who hasn't watched the video would understand. Be specific about what makes this video unique or valuable.

Format your response as:
OVERALL_SUMMARY: [Your 4-sentence summary here]
MAIN_THEMES: [List of main themes]
KEY_TAKEAWAYS: [List of key takeaways]
"""
        
        content = await model_manager.generate_summary(selected_model, prompt, max_tokens=500)
        return parse_overall_summary(content)
        
    except Exception as e:
        logger.error(f"Error generating overall summary: {str(e)}")
        return create_fallback_overall_summary(segment_summaries, video_title, video_duration)

def create_summarization_prompt(transcript: str, segment: Dict[str, Any]) -> str:
    """Create a prompt for the summarization model"""
    duration = segment.get('duration', 0)
    start_time = format_timestamp(segment.get('start_time', 0))
    
    prompt = f"""
Please analyze and summarize the following video transcript segment:

**Segment Info:**
- Timestamp: {start_time}
- Duration: {duration:.1f} seconds
- Word count: {len(transcript.split())} words

**Transcript:**
{transcript}

**Instructions:**
1. Create a concise summary (2-3 sentences) that captures the main points
2. Extract 3-5 key points or insights from this segment
3. Focus on actionable information, important concepts, or significant statements

**Response Format:**
SUMMARY: [Your 2-3 sentence summary here]

KEY_POINTS:
- [Key point 1]
- [Key point 2]
- [Key point 3]
- [Additional points if relevant]

Keep the summary clear, informative, and focused on the most valuable content from this segment.
"""
    return prompt

def parse_summary_response(content: str) -> Dict[str, Any]:
    """Parse the model's response to extract summary and key points"""
    import re
    
    try:
        # Extract summary
        summary_match = re.search(r'SUMMARY:\s*(.*?)(?=KEY_POINTS:|$)', content, re.DOTALL | re.IGNORECASE)
        summary = summary_match.group(1).strip() if summary_match else ""
        
        # Extract key points
        key_points_match = re.search(r'KEY_POINTS:\s*(.*)', content, re.DOTALL | re.IGNORECASE)
        key_points_text = key_points_match.group(1).strip() if key_points_match else ""
        
        # Parse key points (look for bullet points or numbered lists)
        key_points = []
        if key_points_text:
            lines = key_points_text.split('\n')
            for line in lines:
                line = line.strip()
                # Remove bullet points, numbers, or dashes
                line = re.sub(r'^[-•*\d+\.)\s]+', '', line).strip()
                if line and len(line) > 10:  # Minimum length for a key point
                    key_points.append(line)
        
        # Fallback if parsing failed
        if not summary:
            summary = content[:200] + "..." if len(content) > 200 else content
        
        if not key_points:
            # Try to extract sentences as key points
            sentences = re.split(r'[.!?]+', content)
            key_points = [s.strip() for s in sentences if len(s.strip()) > 20][:3]
        
        return {
            'summary': summary,
            'key_points': key_points[:5]  # Limit to 5 key points
        }
        
    except Exception as e:
        logger.error(f"Error parsing summary response: {str(e)}")
        return create_fallback_summary(content)

def parse_overall_summary(content: str) -> Dict[str, Any]:
    """Parse the overall summary response"""
    import re
    
    try:
        # Extract overall summary
        summary_match = re.search(r'OVERALL_SUMMARY:\s*(.*?)(?=MAIN_THEMES:|$)', content, re.DOTALL | re.IGNORECASE)
        overall_summary = summary_match.group(1).strip() if summary_match else ""
        
        # Extract main themes
        themes_match = re.search(r'MAIN_THEMES:\s*(.*?)(?=KEY_TAKEAWAYS:|$)', content, re.DOTALL | re.IGNORECASE)
        themes_text = themes_match.group(1).strip() if themes_match else ""
        
        # Extract key takeaways
        takeaways_match = re.search(r'KEY_TAKEAWAYS:\s*(.*)', content, re.DOTALL | re.IGNORECASE)
        takeaways_text = takeaways_match.group(1).strip() if takeaways_match else ""
        
        # Parse lists
        main_themes = parse_list_items(themes_text)
        key_takeaways = parse_list_items(takeaways_text)
        
        return {
            'overall_summary': overall_summary or content[:300],
            'main_themes': main_themes,
            'key_takeaways': key_takeaways
        }
        
    except Exception as e:
        logger.error(f"Error parsing overall summary: {str(e)}")
        return {
            'overall_summary': content[:300] if content else "Summary unavailable",
            'main_themes': [],
            'key_takeaways': []
        }

def parse_list_items(text: str) -> List[str]:
    """Parse list items from text"""
    import re
    
    if not text:
        return []
    
    lines = text.split('\n')
    items = []
    
    for line in lines:
        line = line.strip()
        # Remove bullet points, numbers, or dashes
        line = re.sub(r'^[-•*\d+\.)\s]+', '', line).strip()
        if line and len(line) > 5:
            items.append(line)
    
    return items[:5]  # Limit to 5 items

def create_fallback_summary(text: str) -> Dict[str, Any]:
    """Create a simple extractive summary as fallback"""
    import re
    
    try:
        # Split into sentences
        sentences = re.split(r'[.!?]+', text)
        sentences = [s.strip() for s in sentences if len(s.strip()) > 10]
        
        # Take first few sentences as summary
        summary_sentences = sentences[:2] if len(sentences) >= 2 else sentences
        summary = '. '.join(summary_sentences) + '.'
        
        # Use remaining sentences as key points
        key_points = sentences[2:5] if len(sentences) > 2 else sentences[1:4]
        key_points = [point + '.' for point in key_points if point]
        
        return {
            'summary': summary,
            'key_points': key_points
        }
        
    except Exception as e:
        logger.error(f"Error creating fallback summary: {str(e)}")
        return {
            'summary': text[:200] + "..." if len(text) > 200 else text,
            'key_points': []
        }

def create_fallback_overall_summary(segment_summaries: List[Dict[str, Any]], video_title: str, video_duration: float) -> Dict[str, Any]:
    """Create a fallback overall summary when AI generation fails"""
    try:
        # Extract main topics from segment summaries
        all_summaries = [seg['summary'] for seg in segment_summaries if seg.get('summary')]
        all_key_points = []
        for seg in segment_summaries:
            if seg.get('key_points'):
                all_key_points.extend(seg['key_points'])
        
        # Create a basic overall summary
        segment_count = len(segment_summaries)
        duration_str = format_timestamp(video_duration)
        
        overall_summary = f"This video titled '{video_title}' is a {duration_str} long content covering {segment_count} key segments. "
        overall_summary += f"The video provides insights and information across multiple topics. "
        overall_summary += f"Key segments were identified based on content analysis and importance scoring. "
        overall_summary += f"The content is structured to deliver valuable information to viewers interested in the subject matter."
        
        # Extract basic themes from summaries
        common_words = ['technology', 'business', 'education', 'tutorial', 'guide', 'tips', 'strategy', 'development', 'review', 'analysis']
        themes = []
        combined_text = ' '.join(all_summaries).lower()
        
        for word in common_words:
            if word in combined_text:
                themes.append(word.capitalize())
        
        # If no themes found, use generic ones
        if not themes:
            themes = ['Information', 'Education', 'Content']
        
        # Use top key points as takeaways
        takeaways = all_key_points[:5] if all_key_points else ['Video provides informative content', 'Content is structured in segments', 'Multiple topics are covered']
        
        return {
            'overall_summary': overall_summary,
            'main_themes': themes[:5],
            'key_takeaways': takeaways
        }
        
    except Exception as e:
        logger.error(f"Error creating fallback overall summary: {str(e)}")
        return {
            'overall_summary': f"This video titled '{video_title}' contains {len(segment_summaries)} analyzed segments covering various topics and insights.",
            'main_themes': ['Video Content', 'Information'],
            'key_takeaways': ['Video provides informative content']
        }

def format_timestamp(seconds: float) -> str:
    """Format seconds to MM:SS or HH:MM:SS format"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    seconds = int(seconds % 60)
    
    if hours > 0:
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
    else:
        return f"{minutes:02d}:{seconds:02d}"

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "message": "YouTube Summarizer API is running"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
