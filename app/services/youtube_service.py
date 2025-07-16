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
import yt_dlp
import subprocess

logger = logging.getLogger(__name__)

try:
    from .computer_use_youtube_service import ComputerUseYouTubeService
    COMPUTER_USE_AVAILABLE = True
except ImportError:
    COMPUTER_USE_AVAILABLE = False
    logger.warning("Computer use service not available")

class YouTubeService:
    """Service for handling YouTube video downloads and audio processing"""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.temp_dir = tempfile.mkdtemp()
        self.config = config or {}
        
        # Initialize computer use service if available and configured
        self.computer_use_service = None
        if COMPUTER_USE_AVAILABLE and self.config.get('computer_use_enabled', False):
            try:
                self.computer_use_service = ComputerUseYouTubeService(self.config)
                logger.info("Computer use service initialized successfully")
            except Exception as e:
                logger.warning(f"Failed to initialize computer use service: {e}")
        
        logger.info(f"YouTube service initialized with temp directory: {self.temp_dir}")
        
    def is_valid_youtube_url(self, url: str) -> bool:
        """Validate if the URL is a valid YouTube URL"""
        youtube_regex = re.compile(
            r'(https?://)?(www\.)?(youtube|youtu|youtube-nocookie)\.(com|be)/'
            r'(watch\?v=|embed/|v/|.+\?v=)?([^&=%\?]{11})'
        )
        return bool(youtube_regex.match(url))
    
    def _get_random_user_agent(self) -> str:
        """Get a random realistic user agent with more recent versions"""
        user_agents = [
            # Chrome - Latest versions
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
            
            # Firefox - Latest versions
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:133.0) Gecko/20100101 Firefox/133.0',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:133.0) Gecko/20100101 Firefox/133.0',
            'Mozilla/5.0 (X11; Linux x86_64; rv:133.0) Gecko/20100101 Firefox/133.0',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:132.0) Gecko/20100101 Firefox/132.0',
            
            # Safari - Latest versions
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.1 Safari/605.1.15',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.6 Safari/605.1.15',
            
            # Edge - Latest versions
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36 Edg/132.0.0.0',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36 Edg/132.0.0.0',
            
            # Mobile user agents for diversity
            'Mozilla/5.0 (iPhone; CPU iPhone OS 18_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.1 Mobile/15E148 Safari/604.1',
            'Mozilla/5.0 (Linux; Android 14; SM-G998B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Mobile Safari/537.36',
        ]
        return random.choice(user_agents)
    
    def _get_enhanced_headers(self) -> Dict[str, str]:
        """Get enhanced realistic headers with randomization"""
        # Randomize Accept-Language
        languages = [
            'en-US,en;q=0.9',
            'en-US,en;q=0.9,es;q=0.8',
            'en-US,en;q=0.9,fr;q=0.8',
            'en-US,en;q=0.9,de;q=0.8',
            'en-US,en;q=0.9,it;q=0.8',
            'en-US,en;q=0.9,pt;q=0.8',
            'en-US,en;q=0.9,ja;q=0.8',
            'en-US,en;q=0.9,ko;q=0.8',
        ]
        
        # Randomize viewport and screen info
        viewports = [
            '1920x1080',
            '1366x768',
            '1440x900',
            '1536x864',
            '1280x720',
            '1600x900',
            '2560x1440',
            '3840x2160'
        ]
        
        headers = {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'Accept-Language': random.choice(languages),
            'Accept-Encoding': 'gzip, deflate, br, zstd',
            'DNT': random.choice(['1', '0']),
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': random.choice(['none', 'same-origin', 'cross-site']),
            'Sec-Fetch-User': '?1',
            'Cache-Control': random.choice(['max-age=0', 'no-cache', 'no-store']),
            'Pragma': 'no-cache',
            'sec-ch-ua': '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': f'"{random.choice(["Windows", "macOS", "Linux"])}"',
            'sec-ch-ua-platform-version': f'"{random.choice(["15.0.0", "14.0.0", "13.0.0"])}"',
            'sec-ch-ua-arch': f'"{random.choice(["x86", "arm"])}"',
            'sec-ch-ua-bitness': f'"{random.choice(["64", "32"])}"',
            'sec-ch-ua-full-version-list': '"Not_A Brand";v="8.0.0.0", "Chromium";v="120.0.0.0", "Google Chrome";v="120.0.0.0"',
            'sec-ch-viewport-width': str(random.randint(1200, 1920)),
            'sec-ch-viewport-height': str(random.randint(800, 1080)),
            'sec-ch-dpr': str(random.choice([1, 1.25, 1.5, 2])),
            'X-Forwarded-For': f"{random.randint(1, 255)}.{random.randint(1, 255)}.{random.randint(1, 255)}.{random.randint(1, 255)}",
            'X-Real-IP': f"{random.randint(1, 255)}.{random.randint(1, 255)}.{random.randint(1, 255)}.{random.randint(1, 255)}",
        }
        
        # Randomly add optional headers
        optional_headers = {
            'X-Requested-With': 'XMLHttpRequest',
            'Origin': 'https://www.youtube.com',
            'Referer': 'https://www.youtube.com/',
            'sec-ch-ua-wow64': '?0',
            'sec-ch-prefers-color-scheme': random.choice(['light', 'dark']),
            'sec-ch-prefers-reduced-motion': random.choice(['no-preference', 'reduce']),
        }
        
        # Add some optional headers randomly
        for header, value in optional_headers.items():
            if random.random() > 0.5:
                headers[header] = value
                
        return headers
    
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
        """Download YouTube video using yt-dlp with multiple retry strategies"""
        try:
            logger.info(f"Starting YouTube video download for: {url}")
            
            # Validate URL first
            if not self.is_valid_youtube_url(url):
                raise Exception("Invalid YouTube URL format")
            
            # Check video accessibility
            accessibility = await self._check_video_accessibility(url)
            if not accessibility.get('accessible', True):
                logger.warning(f"Video accessibility check failed: {accessibility.get('reason', 'Unknown')}")
                # Continue anyway as the check might be inaccurate
            
            # Use yt-dlp to download video and extract audio
            result = await self._download_with_yt_dlp(url)
            
            if result.get('success'):
                logger.info(f"YouTube download successful: {result.get('message', 'Success')}")
                
                info = result.get('info', {})
                
                return {
                    'title': info.get('title', 'Downloaded Video'),
                    'duration': info.get('duration', 0),
                    'audio_path': result.get('audio_path'),
                    'video_id': self._extract_video_id(url),
                    'uploader': info.get('uploader', 'Unknown'),
                    'upload_date': info.get('upload_date', ''),
                    'view_count': info.get('view_count', 0),
                    'like_count': info.get('like_count', 0),
                    'description': info.get('description', '')[:500] + '...' if info.get('description') else 'No description available',
                    'source_url': url
                }
            else:
                # If traditional methods failed, try computer use as final fallback
                if self.computer_use_service:
                    logger.info("Traditional methods failed, trying computer use fallback...")
                    try:
                        computer_use_result = await self.computer_use_service.download_video_with_computer_use(url)
                        
                        if computer_use_result.get('success'):
                            logger.info("Computer use download successful!")
                            video_info = computer_use_result.get('video_info', {})
                            
                            return {
                                'title': video_info.get('title', 'Downloaded Video'),
                                'duration': video_info.get('duration', 0),
                                'audio_path': computer_use_result.get('audio_path'),
                                'video_id': self._extract_video_id(url),
                                'uploader': video_info.get('uploader', 'Unknown'),
                                'upload_date': video_info.get('upload_date', ''),
                                'view_count': video_info.get('view_count', 0),
                                'like_count': video_info.get('like_count', 0),
                                'description': video_info.get('description', 'No description available'),
                                'source_url': url,
                                'download_method': 'computer_use'
                            }
                        else:
                            logger.error(f"Computer use download failed: {computer_use_result.get('error', 'Unknown error')}")
                            
                    except Exception as computer_use_error:
                        logger.error(f"Computer use fallback failed: {computer_use_error}")
                
                raise Exception(f"YouTube download failed: {result.get('error', 'Unknown error')}")
                
        except Exception as e:
            logger.error(f"YouTube download failed: {str(e)}")
            raise Exception(f"Failed to download YouTube video: {str(e)}")
    
    async def _download_with_yt_dlp(self, url: str) -> Dict[str, Any]:
        """Download YouTube video using yt-dlp with multiple retry strategies"""
        try:
            logger.info(f"Using yt-dlp to download: {url}")
            
            # Define multiple extraction strategies with enhanced options
            extraction_strategies = [
                {
                    'name': 'enhanced_android',
                    'player_client': ['android', 'android_creator'],
                    'skip': ['hls', 'dash'],
                    'player_skip': ['configs'],
                    'innertube_host': 'www.youtube.com',
                    'innertube_key': 'AIzaSyA8eiZmM1FaDVjRy-df2KTyQ_vz_yYM39w',
                },
                {
                    'name': 'ios_music',
                    'player_client': ['ios_music', 'ios'],
                    'skip': ['hls'],
                    'player_skip': ['configs'],
                    'innertube_host': 'music.youtube.com',
                },
                {
                    'name': 'android_vr',
                    'player_client': ['android_vr', 'android'],
                    'skip': ['dash'],
                    'player_skip': [],
                    'innertube_host': 'www.youtube.com',
                },
                {
                    'name': 'web_creator',
                    'player_client': ['web_creator', 'web'],
                    'skip': ['hls'],
                    'player_skip': ['configs'],
                    'innertube_host': 'studio.youtube.com',
                },
                {
                    'name': 'tv_embedded',
                    'player_client': ['tv_embedded', 'web'],
                    'skip': [],
                    'player_skip': [],
                    'innertube_host': 'www.youtube.com',
                },
                {
                    'name': 'standard',
                    'player_client': ['android', 'web'],
                    'skip': ['hls', 'dash'],
                    'player_skip': ['configs'],
                },
                {
                    'name': 'web_only',
                    'player_client': ['web'],
                    'skip': ['dash'],
                    'player_skip': [],
                },
                {
                    'name': 'fallback',
                    'player_client': ['android', 'web', 'ios', 'android_creator'],
                    'skip': [],
                    'player_skip': [],
                },
            ]
            
            # Try each strategy with exponential backoff
            for attempt, strategy in enumerate(extraction_strategies, 1):
                try:
                    logger.info(f"Attempt {attempt}: Using {strategy['name']} strategy")
                    
                    # Wait between attempts (exponential backoff)
                    if attempt > 1:
                        wait_time = min(2 ** (attempt - 1), 30)  # Max 30 seconds
                        logger.info(f"Waiting {wait_time} seconds before retry...")
                        await asyncio.sleep(wait_time)
                    
                    # Generate random user agent for each attempt
                    current_ua = self._get_random_user_agent()
                    headers = self._get_enhanced_headers()
                    
                    # Configure yt-dlp options for this strategy
                    ydl_opts = {
                        'format': 'bestaudio/best',
                        'outtmpl': os.path.join(self.temp_dir, '%(title)s.%(ext)s'),
                        'noplaylist': True,
                        'quiet': True,
                        'no_warnings': True,
                        'extract_flat': False,
                        
                        # Anti-detection measures
                        'user_agent': current_ua,
                        'referer': 'https://www.youtube.com/',
                        'sleep_interval': random.uniform(1, 3),
                        'max_sleep_interval': random.uniform(3, 6),
                        'sleep_interval_requests': random.uniform(0.5, 2),
                        'sleep_interval_subtitles': random.uniform(0.5, 2),
                        
                        # Request headers to avoid detection
                        'http_headers': headers,
                        
                        # Retry configuration
                        'retries': 5,
                        'fragment_retries': 5,
                        'retry_sleep_functions': {'http': lambda n: min(2 ** n, 30)},
                        
                        # Strategy-specific extractor options
                        'extractor_args': {
                            'youtube': strategy
                        },
                        
                        # Additional options to avoid rate limiting
                        'concurrent_fragment_downloads': 1,
                        'ratelimit': random.randint(30000, 70000),  # Randomize rate limit
                    }
                    
                    # Try to get video info first
                    info = None
                    try:
                        with yt_dlp.YoutubeDL({**ydl_opts, 'quiet': True}) as ydl:
                            info = await asyncio.get_event_loop().run_in_executor(
                                None, ydl.extract_info, url, False
                            )
                            logger.info(f"Successfully extracted video info: {info.get('title', 'Unknown')}")
                    except Exception as info_error:
                        logger.warning(f"Failed to extract video info: {info_error}")
                        # Continue with download attempt even if info extraction fails
                    
                    # Attempt download
                    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                        await asyncio.get_event_loop().run_in_executor(
                            None, ydl.download, [url]
                        )
                    
                    # Find the downloaded file
                    audio_extensions = ['.webm', '.mp4', '.m4a', '.wav', '.mp3', '.ogg', '.opus', '.aac']
                    downloaded_files = [f for f in os.listdir(self.temp_dir) 
                                      if any(f.lower().endswith(ext) for ext in audio_extensions)]
                    
                    if not downloaded_files:
                        raise Exception("No audio file was downloaded")
                    
                    original_path = os.path.join(self.temp_dir, downloaded_files[0])
                    
                    # Convert to WAV format if needed
                    audio_path = await self._convert_to_wav(original_path)
                    
                    logger.info(f"Successfully downloaded using {strategy['name']} strategy")
                    return {
                        "success": True,
                        "message": f"Successfully downloaded using yt-dlp ({strategy['name']} strategy)",
                        "audio_path": audio_path,
                        "info": info or {},
                        "strategy_used": strategy['name'],
                        "attempt": attempt
                    }
                    
                except Exception as strategy_error:
                    logger.warning(f"Strategy {strategy['name']} failed: {str(strategy_error)}")
                    
                    # Check for specific errors
                    if "Sign in to confirm your age" in str(strategy_error):
                        logger.error("Video is age-restricted and requires sign-in")
                        return {"success": False, "error": "Video is age-restricted and requires authentication"}
                    
                    if "Private video" in str(strategy_error):
                        logger.error("Video is private")
                        return {"success": False, "error": "Video is private and cannot be downloaded"}
                    
                    if "Video unavailable" in str(strategy_error):
                        logger.error("Video is unavailable")
                        return {"success": False, "error": "Video is unavailable"}
                    
                    # If this is the last strategy, raise the error
                    if attempt == len(extraction_strategies):
                        raise strategy_error
            
            # If we get here, all strategies failed
            logger.warning("All yt-dlp strategies failed, trying youtube-dl as fallback")
            return await self._download_with_youtube_dl(url)
            
        except Exception as e:
            logger.error(f"yt-dlp download completely failed: {str(e)}")
            # Try youtube-dl as final fallback
            logger.warning("Trying youtube-dl as final fallback")
            return await self._download_with_youtube_dl(url)
    
    async def _download_with_youtube_dl(self, url: str) -> Dict[str, Any]:
        """Download YouTube video using youtube-dl as fallback"""
        try:
            logger.info(f"Using youtube-dl as fallback for: {url}")
            
            # Generate random user agent
            current_ua = self._get_random_user_agent()
            headers = self._get_enhanced_headers()
            
            # Configure youtube-dl options
            ydl_opts = {
                'format': 'bestaudio/best',
                'outtmpl': os.path.join(self.temp_dir, '%(title)s.%(ext)s'),
                'noplaylist': True,
                'quiet': True,
                'no_warnings': True,
                'extract_flat': False,
                
                # Anti-detection measures
                'user_agent': current_ua,
                'referer': 'https://www.youtube.com/',
                'sleep_interval': random.uniform(1, 3),
                'max_sleep_interval': random.uniform(3, 6),
                
                # Request headers
                'http_headers': headers,
                
                # Retry configuration
                'retries': 3,
                'fragment_retries': 3,
                
                # Rate limiting
                'ratelimit': random.randint(30000, 70000),
            }
            
            # Try to import youtube-dl
            try:
                import youtube_dl
            except ImportError:
                logger.error("youtube-dl not available as fallback")
                return {"success": False, "error": "youtube-dl not available"}
            
            # Attempt download with youtube-dl
            with youtube_dl.YoutubeDL(ydl_opts) as ydl:
                # Get video info first
                info = await asyncio.get_event_loop().run_in_executor(
                    None, ydl.extract_info, url, False
                )
                
                # Download the video
                await asyncio.get_event_loop().run_in_executor(
                    None, ydl.download, [url]
                )
            
            # Find the downloaded file
            audio_extensions = ['.webm', '.mp4', '.m4a', '.wav', '.mp3', '.ogg', '.opus', '.aac']
            downloaded_files = [f for f in os.listdir(self.temp_dir) 
                              if any(f.lower().endswith(ext) for ext in audio_extensions)]
            
            if not downloaded_files:
                raise Exception("No audio file was downloaded")
            
            original_path = os.path.join(self.temp_dir, downloaded_files[0])
            
            # Convert to WAV format if needed
            audio_path = await self._convert_to_wav(original_path)
            
            logger.info("Successfully downloaded using youtube-dl fallback")
            return {
                "success": True,
                "message": "Successfully downloaded using youtube-dl fallback",
                "audio_path": audio_path,
                "info": info or {},
                "strategy_used": "youtube-dl_fallback",
                "attempt": "fallback"
            }
            
        except Exception as e:
            logger.error(f"youtube-dl fallback also failed: {str(e)}")
            return {"success": False, "error": f"Both yt-dlp and youtube-dl failed: {str(e)}"}
    
    async def _convert_to_wav(self, input_path: str) -> str:
        """Convert audio file to WAV format using ffmpeg"""
        try:
            if input_path.lower().endswith('.wav'):
                return input_path
            
            logger.info(f"Converting {input_path} to WAV format")
            wav_path = os.path.join(self.temp_dir, 'converted_audio.wav')
            
            # Use ffmpeg to convert to WAV
            result = await asyncio.get_event_loop().run_in_executor(
                None, 
                lambda: subprocess.run([
                    'ffmpeg', '-i', input_path, 
                    '-acodec', 'pcm_s16le', 
                    '-ar', '16000', 
                    '-ac', '1', 
                    '-y',  # Overwrite output file
                    wav_path
                ], capture_output=True, text=True, timeout=60)
            )
            
            if result.returncode == 0:
                logger.info("Successfully converted to WAV")
                # Clean up original file
                if os.path.exists(input_path):
                    os.remove(input_path)
                return wav_path
            else:
                logger.warning(f"FFmpeg conversion failed: {result.stderr}")
                # Return original file as fallback
                return input_path
                
        except subprocess.TimeoutExpired:
            logger.error("Audio conversion timed out")
            return input_path
        except Exception as conv_error:
            logger.warning(f"Audio conversion failed: {conv_error}")
            return input_path
    
    def _extract_video_id(self, url: str) -> str:
        """Extract video ID from YouTube URL"""
        try:
            parsed_url = urlparse(url)
            if 'youtu.be' in parsed_url.netloc:
                return parsed_url.path[1:]
            elif 'youtube.com' in parsed_url.netloc:
                return parse_qs(parsed_url.query).get('v', [''])[0]
            return ''
        except:
            return ''
    
    
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
