import yt_dlp
import os
import re
import asyncio
from typing import Dict, List, Any
import logging
from pydub import AudioSegment
import tempfile

logger = logging.getLogger(__name__)

class YouTubeService:
    """Service for handling YouTube video downloads and audio processing"""
    
    def __init__(self):
        self.temp_dir = tempfile.mkdtemp()
        
    def is_valid_youtube_url(self, url: str) -> bool:
        """Validate if the URL is a valid YouTube URL"""
        youtube_regex = re.compile(
            r'(https?://)?(www\.)?(youtube|youtu|youtube-nocookie)\.(com|be)/'
            r'(watch\?v=|embed/|v/|.+\?v=)?([^&=%\?]{11})'
        )
        return bool(youtube_regex.match(url))
    
    async def download_video(self, url: str) -> Dict[str, Any]:
        """Download YouTube video and extract audio"""
        try:
            # Configure yt-dlp options with anti-bot measures
            ydl_opts = {
                'format': 'bestaudio/best',
                'outtmpl': os.path.join(self.temp_dir, '%(title)s.%(ext)s'),
                'extractaudio': True,
                'audioformat': 'wav',
                'audioquality': '192K',
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'wav',
                    'preferredquality': '192',
                }],
                'quiet': True,
                'no_warnings': True,
                # Anti-bot measures
                'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'headers': {
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                    'Accept-Language': 'en-us,en;q=0.5',
                    'Accept-Encoding': 'gzip,deflate',
                    'Accept-Charset': 'ISO-8859-1,utf-8;q=0.7,*;q=0.7',
                    'Connection': 'keep-alive',
                    'Upgrade-Insecure-Requests': '1',
                },
                'extractor_retries': 3,
                'fragment_retries': 3,
                'retry_sleep_functions': {
                    'http': lambda n: min(4 ** n, 60),
                    'fragment': lambda n: min(4 ** n, 60),
                    'extractor': lambda n: min(4 ** n, 60),
                },
                'sleep_interval': 1,
                'max_sleep_interval': 5,
                'cookiesfrombrowser': None,  # Use system cookies if available
            }
            
            # Download video info and audio
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                # Get video info first
                info = await asyncio.get_event_loop().run_in_executor(
                    None, ydl.extract_info, url, False
                )
                
                # Download the audio
                await asyncio.get_event_loop().run_in_executor(
                    None, ydl.download, [url]
                )
                
                # Find the downloaded audio file
                audio_path = None
                for file in os.listdir(self.temp_dir):
                    if file.endswith('.wav'):
                        audio_path = os.path.join(self.temp_dir, file)
                        break
                
                if not audio_path:
                    raise Exception("Failed to download audio file")
                
                return {
                    'title': info.get('title', 'Unknown'),
                    'duration': info.get('duration', 0),
                    'audio_path': audio_path,
                    'video_id': info.get('id', ''),
                    'uploader': info.get('uploader', 'Unknown')
                }
                
        except Exception as e:
            logger.error(f"Error downloading video: {str(e)}")
            raise Exception(f"Failed to download video: {str(e)}")
    
    async def extract_audio_segments(self, audio_path: str, segment_length: int = 60) -> List[Dict[str, Any]]:
        """Extract audio segments from the downloaded audio file"""
        try:
            # Load audio file
            audio = AudioSegment.from_wav(audio_path)
            duration_ms = len(audio)
            segment_length_ms = segment_length * 1000
            
            segments = []
            
            # Create segments
            for start_ms in range(0, duration_ms, segment_length_ms):
                end_ms = min(start_ms + segment_length_ms, duration_ms)
                
                # Extract segment
                segment = audio[start_ms:end_ms]
                
                # Save segment to temporary file
                segment_path = os.path.join(
                    self.temp_dir, 
                    f"segment_{start_ms//1000}_{end_ms//1000}.wav"
                )
                segment.export(segment_path, format="wav")
                
                segments.append({
                    'start_time': start_ms / 1000,
                    'end_time': end_ms / 1000,
                    'duration': (end_ms - start_ms) / 1000,
                    'path': segment_path
                })
            
            logger.info(f"Created {len(segments)} audio segments")
            return segments
            
        except Exception as e:
            logger.error(f"Error extracting audio segments: {str(e)}")
            raise Exception(f"Failed to extract audio segments: {str(e)}")
    
    async def cleanup_files(self, *file_paths: str):
        """Clean up temporary files"""
        try:
            for file_path in file_paths:
                if os.path.exists(file_path):
                    os.remove(file_path)
            
            # Clean up segment files
            for file in os.listdir(self.temp_dir):
                if file.startswith('segment_') and file.endswith('.wav'):
                    os.remove(os.path.join(self.temp_dir, file))
                    
        except Exception as e:
            logger.warning(f"Error cleaning up files: {str(e)}")
    
    def format_timestamp(self, seconds: float) -> str:
        """Format seconds to MM:SS or HH:MM:SS format"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        seconds = int(seconds % 60)
        
        if hours > 0:
            return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        else:
            return f"{minutes:02d}:{seconds:02d}"
