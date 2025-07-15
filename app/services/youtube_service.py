import yt_dlp
import os
import re
import asyncio
from typing import Dict, List, Any
import logging
from pydub import AudioSegment
import tempfile
import time
import random
import requests
from urllib.parse import urlparse, parse_qs

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
    
    def _get_random_user_agent(self) -> str:
        """Get a random realistic user agent"""
        user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:132.0) Gecko/20100101 Firefox/132.0',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:132.0) Gecko/20100101 Firefox/132.0',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36',
            'Mozilla/5.0 (X11; Linux x86_64; rv:131.0) Gecko/20100101 Firefox/131.0',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15'
        ]
        return random.choice(user_agents)
    
    def _get_enhanced_headers(self) -> Dict[str, str]:
        """Get enhanced realistic headers"""
        return {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9,es;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'Cache-Control': 'max-age=0',
        }
    
    async def _check_video_accessibility(self, url: str) -> Dict[str, Any]:
        """Check if video is accessible before attempting download"""
        try:
            # Extract video ID from URL
            parsed_url = urlparse(url)
            if 'youtu.be' in parsed_url.netloc:
                video_id = parsed_url.path[1:]
            elif 'youtube.com' in parsed_url.netloc:
                video_id = parse_qs(parsed_url.query).get('v', [None])[0]
            else:
                raise Exception("Invalid YouTube URL format")
            
            if not video_id:
                raise Exception("Could not extract video ID from URL")
            
            # Check video accessibility using YouTube's oEmbed API
            oembed_url = f"https://www.youtube.com/oembed?url={url}&format=json"
            
            def check_oembed():
                try:
                    response = requests.get(oembed_url, timeout=10)
                    if response.status_code == 200:
                        data = response.json()
                        return {
                            'accessible': True,
                            'title': data.get('title', 'Unknown'),
                            'author': data.get('author_name', 'Unknown'),
                            'duration': None  # oEmbed doesn't provide duration
                        }
                    else:
                        return {'accessible': False, 'reason': f"HTTP {response.status_code}"}
                except Exception as e:
                    return {'accessible': False, 'reason': str(e)}
            
            result = await asyncio.get_event_loop().run_in_executor(None, check_oembed)
            return result
            
        except Exception as e:
            logger.warning(f"Video accessibility check failed: {str(e)}")
            return {'accessible': True, 'reason': 'Check failed, proceeding anyway'}
    
    async def download_video(self, url: str) -> Dict[str, Any]:
        """Download YouTube video and extract audio with enhanced anti-bot measures"""
        max_attempts = 3
        last_exception = None
        
        # Check video accessibility first
        accessibility = await self._check_video_accessibility(url)
        if not accessibility.get('accessible', True):
            raise Exception(f"Video not accessible: {accessibility.get('reason', 'Unknown reason')}")
        
        for attempt in range(max_attempts):
            try:
                # Add progressive delay between attempts
                if attempt > 0:
                    delay = (2 ** attempt) + random.uniform(1, 3)
                    logger.info(f"Retrying download (attempt {attempt + 1}/{max_attempts}) after {delay:.1f}s delay")
                    await asyncio.sleep(delay)
                
                # Get random user agent and headers for this attempt
                user_agent = self._get_random_user_agent()
                headers = self._get_enhanced_headers()
                
                # Configure yt-dlp options with enhanced anti-bot measures
                ydl_opts = {
                    'format': 'bestaudio[ext=webm]/bestaudio[ext=m4a]/bestaudio/best',
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
                    
                    # Enhanced anti-bot measures
                    'user_agent': user_agent,
                    'headers': headers,
                    
                    # Retry configuration
                    'extractor_retries': 5,
                    'fragment_retries': 5,
                    'retry_sleep_functions': {
                        'http': lambda n: min(2 ** n, 30) + random.uniform(0, 2),
                        'fragment': lambda n: min(2 ** n, 30) + random.uniform(0, 2),
                        'extractor': lambda n: min(2 ** n, 30) + random.uniform(0, 2),
                    },
                    
                    # Network configuration
                    'socket_timeout': 30,
                    'sleep_interval': random.uniform(0.5, 2.0),
                    'max_sleep_interval': 10,
                    
                    # Additional anti-detection measures
                    'no_check_certificate': False,
                    'prefer_insecure': False,
                    'cachedir': False,
                    'extract_flat': False,
                    
                    # Try to use cookies from browser if available (disable in Docker)
                    'cookiesfrombrowser': None,
                    
                    # Additional YouTube-specific options
                    'youtube_include_dash_manifest': False,
                    'writesubtitles': False,
                    'writeautomaticsub': False,
                }
                
                # Attempt download
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    # Get video info first
                    logger.info(f"Extracting video info for attempt {attempt + 1}")
                    info = await asyncio.get_event_loop().run_in_executor(
                        None, ydl.extract_info, url, False
                    )
                    
                    # Check if video is available
                    if info.get('availability') == 'private':
                        raise Exception("Video is private")
                    elif info.get('availability') == 'premium_only':
                        raise Exception("Video requires YouTube Premium")
                    elif info.get('live_status') == 'is_live':
                        raise Exception("Cannot download live streams")
                    
                    # Download the audio
                    logger.info(f"Downloading audio for attempt {attempt + 1}")
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
                        raise Exception("Failed to find downloaded audio file")
                    
                    # Verify audio file exists and is not empty
                    if not os.path.exists(audio_path) or os.path.getsize(audio_path) == 0:
                        raise Exception("Downloaded audio file is empty or corrupted")
                    
                    logger.info(f"Successfully downloaded video on attempt {attempt + 1}")
                    return {
                        'title': info.get('title', 'Unknown'),
                        'duration': info.get('duration', 0),
                        'audio_path': audio_path,
                        'video_id': info.get('id', ''),
                        'uploader': info.get('uploader', 'Unknown'),
                        'upload_date': info.get('upload_date', ''),
                        'view_count': info.get('view_count', 0),
                        'like_count': info.get('like_count', 0),
                        'description': info.get('description', '')[:500] + '...' if info.get('description') else ''
                    }
                    
            except Exception as e:
                last_exception = e
                error_msg = str(e).lower()
                
                # Check for specific error types
                if 'sign in to confirm your age' in error_msg:
                    raise Exception("Video requires age verification - cannot download")
                elif 'video unavailable' in error_msg:
                    raise Exception("Video is unavailable or has been removed")
                elif 'private video' in error_msg:
                    raise Exception("Video is private")
                elif 'this video is not available' in error_msg:
                    raise Exception("Video is not available in your region")
                elif 'http error 429' in error_msg:
                    if attempt < max_attempts - 1:
                        logger.warning(f"Rate limited on attempt {attempt + 1}, will retry with longer delay")
                        await asyncio.sleep(random.uniform(10, 20))
                        continue
                    else:
                        raise Exception("Rate limited by YouTube - please try again later")
                elif 'http error 403' in error_msg:
                    if attempt < max_attempts - 1:
                        logger.warning(f"403 Forbidden on attempt {attempt + 1}, trying different strategy")
                        continue
                    else:
                        raise Exception("Access forbidden - YouTube may have blocked the request")
                
                logger.warning(f"Download attempt {attempt + 1} failed: {str(e)}")
                
                if attempt == max_attempts - 1:
                    # Last attempt failed
                    break
        
        # All attempts failed
        raise Exception(f"Failed to download video after {max_attempts} attempts. Last error: {str(last_exception)}")
    
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
