import requests
from bs4 import BeautifulSoup
import re
import asyncio
import os
import tempfile
import logging
from typing import Dict, List, Any, Optional
from urllib.parse import urljoin, urlparse, parse_qs
import json
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import TimeoutException, WebDriverException
import yt_dlp
from pydub import AudioSegment
import time
import random

logger = logging.getLogger(__name__)

class ConferenceVideoService:
    """Service for handling conference video downloads and processing"""
    
    def __init__(self):
        self.temp_dir = tempfile.mkdtemp()
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36'
        })
        
    def _setup_selenium_driver(self) -> webdriver.Chrome:
        """Setup Selenium Chrome driver with optimal configuration"""
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--window-size=1920,1080')
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_argument('--disable-web-security')
        chrome_options.add_argument('--disable-features=VizDisplayCompositor')
        chrome_options.add_argument('--disable-extensions')
        chrome_options.add_argument('--disable-plugins')
        chrome_options.add_argument('--disable-images')
        chrome_options.add_argument('--disable-default-apps')
        chrome_options.add_argument('--disable-sync')
        chrome_options.add_argument('--disable-translate')
        chrome_options.add_argument('--hide-scrollbars')
        chrome_options.add_argument('--metrics-recording-only')
        chrome_options.add_argument('--mute-audio')
        chrome_options.add_argument('--no-first-run')
        chrome_options.add_argument('--safebrowsing-disable-auto-update')
        chrome_options.add_argument('--single-process')
        chrome_options.add_argument('--disable-background-timer-throttling')
        chrome_options.add_argument('--disable-renderer-backgrounding')
        chrome_options.add_argument('--disable-backgrounding-occluded-windows')
        chrome_options.add_argument('--remote-debugging-port=9222')
        chrome_options.add_argument('--disable-logging')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-ipc-flooding-protection')
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        # Check if we're running in Docker environment
        is_docker = os.path.exists('/.dockerenv')
        
        # Try different chromedriver locations
        chromedriver_paths = [
            '/usr/local/bin/chromedriver',  # Docker installation location
            '/usr/bin/chromedriver',        # Alternative system location
            'chromedriver'                  # PATH lookup
        ]
        
        driver = None
        last_error = None
        
        # Try system chromedriver first
        for chromedriver_path in chromedriver_paths:
            try:
                logger.info(f"Trying chromedriver at: {chromedriver_path}")
                
                # Check if file exists and is executable
                if chromedriver_path != 'chromedriver':
                    if not os.path.exists(chromedriver_path):
                        logger.warning(f"Chromedriver not found at: {chromedriver_path}")
                        continue
                    if not os.access(chromedriver_path, os.X_OK):
                        logger.warning(f"Chromedriver not executable at: {chromedriver_path}")
                        continue
                
                service = Service(executable_path=chromedriver_path)
                driver = webdriver.Chrome(service=service, options=chrome_options)
                
                # Execute script to remove webdriver property
                driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
                
                logger.info(f"Successfully created Chrome driver using: {chromedriver_path}")
                return driver
                
            except Exception as e:
                last_error = e
                logger.warning(f"Failed to create Chrome driver with {chromedriver_path}: {str(e)}")
                if driver:
                    try:
                        driver.quit()
                    except:
                        pass
                    driver = None
                continue
        
        # If system chromedriver failed, try one more approach with explicit binary path
        if not driver:
            try:
                logger.info("Trying Chrome binary with auto-detected chromedriver...")
                
                # Try to find Chrome binary location
                chrome_binaries = [
                    '/usr/bin/google-chrome',
                    '/usr/bin/google-chrome-stable',
                    '/usr/bin/chromium-browser',
                    '/usr/bin/chromium'
                ]
                
                chrome_binary = None
                for binary_path in chrome_binaries:
                    if os.path.exists(binary_path) and os.access(binary_path, os.X_OK):
                        chrome_binary = binary_path
                        break
                
                if chrome_binary:
                    chrome_options.binary_location = chrome_binary
                    logger.info(f"Using Chrome binary: {chrome_binary}")
                
                # Try with default service (no explicit path)
                service = Service()
                driver = webdriver.Chrome(service=service, options=chrome_options)
                driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
                logger.info("Successfully created Chrome driver with auto-detection")
                return driver
                
            except Exception as e:
                logger.error(f"Auto-detection fallback failed: {str(e)}")
                last_error = e
                if driver:
                    try:
                        driver.quit()
                    except:
                        pass
        
        # If all else fails, raise the last error
        raise Exception(f"Unable to create Chrome driver with any method. Last error: {str(last_error)}")
    
    async def authenticate_and_get_page(self, url: str, username: str = None, password: str = None) -> str:
        """Authenticate with the conference site and get the page content"""
        driver = None
        try:
            driver = self._setup_selenium_driver()
            
            # Navigate to the page
            driver.get(url)
            await asyncio.sleep(2)
            
            # Check if login is required
            login_indicators = [
                'login', 'sign in', 'sign-in', 'signin', 'authenticate', 
                'username', 'email', 'password', 'log in'
            ]
            
            page_source = driver.page_source.lower()
            needs_login = any(indicator in page_source for indicator in login_indicators)
            
            if needs_login and username and password:
                logger.info("Login required, attempting authentication...")
                
                # Try to find login form elements
                login_success = await self._attempt_login(driver, username, password)
                
                if login_success:
                    logger.info("Authentication successful")
                    # Navigate back to the original page after login
                    driver.get(url)
                    await asyncio.sleep(3)
                else:
                    logger.warning("Authentication failed or not required")
            
            # Get the final page content
            page_content = driver.page_source
            
            return page_content
            
        except Exception as e:
            logger.error(f"Error during authentication: {str(e)}")
            raise Exception(f"Failed to authenticate and get page: {str(e)}")
            
        finally:
            if driver:
                driver.quit()
    
    async def _attempt_login(self, driver: webdriver.Chrome, username: str, password: str) -> bool:
        """Attempt to login using common login form patterns"""
        try:
            # Common username field selectors
            username_selectors = [
                'input[type="email"]',
                'input[type="text"][name*="user"]',
                'input[type="text"][name*="email"]',
                'input[id*="user"]',
                'input[id*="email"]',
                'input[name="username"]',
                'input[name="email"]',
                '#username',
                '#email',
                '.username',
                '.email'
            ]
            
            # Common password field selectors
            password_selectors = [
                'input[type="password"]',
                'input[name="password"]',
                '#password',
                '.password'
            ]
            
            # Try to find and fill username field
            username_field = None
            for selector in username_selectors:
                try:
                    username_field = driver.find_element(By.CSS_SELECTOR, selector)
                    break
                except:
                    continue
            
            if not username_field:
                logger.warning("Could not find username field")
                return False
            
            # Try to find password field
            password_field = None
            for selector in password_selectors:
                try:
                    password_field = driver.find_element(By.CSS_SELECTOR, selector)
                    break
                except:
                    continue
            
            if not password_field:
                logger.warning("Could not find password field")
                return False
            
            # Fill in credentials
            username_field.clear()
            username_field.send_keys(username)
            await asyncio.sleep(1)
            
            password_field.clear()
            password_field.send_keys(password)
            await asyncio.sleep(1)
            
            # Try to find and click submit button
            submit_selectors = [
                'input[type="submit"]',
                'button[type="submit"]',
                'button[class*="login"]',
                'button[class*="signin"]',
                'button[class*="sign-in"]',
                '.login-button',
                '.signin-button',
                '.submit-button'
            ]
            
            submit_button = None
            for selector in submit_selectors:
                try:
                    submit_button = driver.find_element(By.CSS_SELECTOR, selector)
                    break
                except:
                    continue
            
            if submit_button:
                submit_button.click()
                await asyncio.sleep(3)
                
                # Check if login was successful by looking for success indicators
                success_indicators = ['dashboard', 'profile', 'logout', 'sign out']
                page_source = driver.page_source.lower()
                
                return any(indicator in page_source for indicator in success_indicators)
            
            return False
            
        except Exception as e:
            logger.error(f"Login attempt failed: {str(e)}")
            return False
    
    async def extract_video_urls(self, page_content: str, base_url: str) -> List[Dict[str, Any]]:
        """Extract video URLs from the page content"""
        soup = BeautifulSoup(page_content, 'html.parser')
        video_urls = []
        
        # 1. Look for direct video tags
        video_tags = soup.find_all('video')
        for video in video_tags:
            src = video.get('src')
            if src:
                video_urls.append({
                    'url': urljoin(base_url, src),
                    'type': 'direct_video',
                    'format': 'mp4'
                })
            
            # Check for source tags within video
            sources = video.find_all('source')
            for source in sources:
                src = source.get('src')
                if src:
                    video_urls.append({
                        'url': urljoin(base_url, src),
                        'type': 'direct_video',
                        'format': source.get('type', 'mp4')
                    })
        
        # 2. Look for iframe embeds
        iframes = soup.find_all('iframe')
        for iframe in iframes:
            src = iframe.get('src')
            if src and any(domain in src for domain in ['youtube.com', 'vimeo.com', 'twitch.tv', 'wistia.com']):
                video_urls.append({
                    'url': src,
                    'type': 'iframe_embed',
                    'format': 'embed'
                })
        
        # 3. Look for JavaScript-embedded videos
        scripts = soup.find_all('script')
        for script in scripts:
            if script.string:
                # Look for common video streaming patterns
                video_patterns = [
                    r'["\']https?://[^"\']*\.m3u8["\']',  # HLS streams
                    r'["\']https?://[^"\']*\.mpd["\']',   # DASH streams
                    r'["\']https?://[^"\']*\.mp4["\']',   # MP4 files
                    r'["\']https?://[^"\']*\.webm["\']',  # WebM files
                ]
                
                for pattern in video_patterns:
                    matches = re.findall(pattern, script.string)
                    for match in matches:
                        clean_url = match.strip('\'"')
                        video_urls.append({
                            'url': clean_url,
                            'type': 'javascript_embed',
                            'format': clean_url.split('.')[-1]
                        })
        
        # 4. Look for data attributes that might contain video URLs
        elements_with_data = soup.find_all(attrs={'data-src': True})
        for element in elements_with_data:
            data_src = element.get('data-src')
            if data_src and any(ext in data_src for ext in ['.mp4', '.webm', '.m3u8', '.mpd']):
                video_urls.append({
                    'url': urljoin(base_url, data_src),
                    'type': 'data_attribute',
                    'format': data_src.split('.')[-1]
                })
        
        # Remove duplicates
        unique_urls = []
        seen_urls = set()
        for video in video_urls:
            if video['url'] not in seen_urls:
                unique_urls.append(video)
                seen_urls.add(video['url'])
        
        logger.info(f"Found {len(unique_urls)} potential video URLs")
        return unique_urls
    
    async def download_conference_video(self, url: str, username: str = None, password: str = None) -> Dict[str, Any]:
        """Download conference video with authentication support"""
        try:
            # Get the page content with authentication
            page_content = await self.authenticate_and_get_page(url, username, password)
            
            # Extract video URLs from the page
            video_urls = await self.extract_video_urls(page_content, url)
            
            if not video_urls:
                raise Exception("No video URLs found on the page")
            
            # Try to download each video URL until one succeeds
            last_error = None
            
            for video_info in video_urls:
                try:
                    video_url = video_info['url']
                    logger.info(f"Attempting to download video: {video_url}")
                    
                    # Use yt-dlp to download the video
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
                    }
                    
                    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                        # Extract info
                        info = await asyncio.get_event_loop().run_in_executor(
                            None, ydl.extract_info, video_url, False
                        )
                        
                        # Download the video
                        await asyncio.get_event_loop().run_in_executor(
                            None, ydl.download, [video_url]
                        )
                        
                        # Find the downloaded audio file
                        audio_path = None
                        for file in os.listdir(self.temp_dir):
                            if file.endswith('.wav'):
                                audio_path = os.path.join(self.temp_dir, file)
                                break
                        
                        if audio_path and os.path.exists(audio_path):
                            return {
                                'title': info.get('title', 'Conference Video'),
                                'duration': info.get('duration', 0),
                                'audio_path': audio_path,
                                'video_url': video_url,
                                'source_page': url,
                                'video_type': video_info['type'],
                                'format': video_info['format'],
                                'description': info.get('description', '')[:500] + '...' if info.get('description') else ''
                            }
                
                except Exception as e:
                    last_error = e
                    logger.warning(f"Failed to download {video_info['url']}: {str(e)}")
                    continue
            
            # If we get here, all downloads failed
            raise Exception(f"Failed to download any video from the page. Last error: {str(last_error)}")
            
        except Exception as e:
            logger.error(f"Conference video download failed: {str(e)}")
            raise Exception(f"Failed to download conference video: {str(e)}")
    
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
    
    def is_valid_conference_url(self, url: str) -> bool:
        """Validate if the URL is a valid conference URL"""
        try:
            parsed = urlparse(url)
            return parsed.scheme in ['http', 'https'] and parsed.netloc
        except:
            return False
    
    def format_timestamp(self, seconds: float) -> str:
        """Format seconds to MM:SS or HH:MM:SS format"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        seconds = int(seconds % 60)
        
        if hours > 0:
            return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        else:
            return f"{minutes:02d}:{seconds:02d}"
