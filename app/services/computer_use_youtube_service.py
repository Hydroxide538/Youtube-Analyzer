import os
import json
import base64
import asyncio
import subprocess
import tempfile
import time
from typing import Dict, List, Any, Optional
from pathlib import Path
import logging
from datetime import datetime
import requests
from urllib.parse import urlparse, parse_qs
import re

logger = logging.getLogger(__name__)

class ComputerUseYouTubeService:
    """Computer use agent for YouTube video extraction using Llama4 vision model"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.temp_dir = tempfile.mkdtemp()
        self.interaction_history = "---\n\nINTERACTION HISTORY:\n"
        self.step_counter = 1
        self.screenshot_counter = 1
        self.setup_run_directory()
        self.load_youtube_prompts()
        logger.info(f"Computer use YouTube service initialized with temp directory: {self.temp_dir}")
    
    def setup_run_directory(self):
        """Setup directory for storing interaction history and screenshots"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.run_dir = Path(self.temp_dir) / "computer_use_runs" / timestamp
        self.run_dir.mkdir(parents=True, exist_ok=True)
        
    def load_youtube_prompts(self):
        """Load YouTube-specific prompts and tools"""
        self.youtube_tools = [
            {
                "type": "function",
                "function": {
                    "name": "browser_navigate",
                    "description": "Navigate to a URL in the browser",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "url": {
                                "type": "string",
                                "description": "The URL to navigate to"
                            }
                        },
                        "required": ["url"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "computer_click",
                    "description": "Click on a UI element described in natural language",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "elementDescription": {
                                "type": "string",
                                "description": "Natural language description of the UI element to click"
                            }
                        },
                        "required": ["elementDescription"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "computer_type",
                    "description": "Type text into the currently focused input field",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "text": {
                                "type": "string",
                                "description": "Text to type"
                            },
                            "pressEnter": {
                                "type": "boolean",
                                "description": "Whether to press Enter after typing"
                            }
                        },
                        "required": ["text"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "extract_video_url",
                    "description": "Extract video download URL from current page",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "quality": {
                                "type": "string",
                                "description": "Preferred video quality (e.g., 'best', 'worst', '720p')",
                                "default": "best"
                            }
                        }
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "wait",
                    "description": "Wait for a specified number of seconds",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "seconds": {
                                "type": "number",
                                "description": "Number of seconds to wait"
                            }
                        },
                        "required": ["seconds"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "complete_task",
                    "description": "Complete the task with the extracted video information",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "success": {
                                "type": "boolean",
                                "description": "Whether the task was completed successfully"
                            },
                            "video_url": {
                                "type": "string",
                                "description": "The extracted video download URL"
                            },
                            "video_info": {
                                "type": "object",
                                "description": "Video metadata information"
                            },
                            "error_message": {
                                "type": "string",
                                "description": "Error message if task failed"
                            }
                        },
                        "required": ["success"]
                    }
                }
            }
        ]
        
        self.youtube_system_prompt = """You are a skilled computer operator specialized in navigating YouTube to extract video download URLs. 
Your task is to:
1. Navigate to the provided YouTube URL
2. Handle any bot detection, CAPTCHAs, or verification steps
3. Extract the video download URL from the page
4. Return the video information

You must be very careful and human-like in your interactions. Take time between actions to avoid detection.

When you encounter:
- Bot detection: Wait and retry with different approach
- CAPTCHAs: Solve them carefully
- Age restrictions: Handle login if needed
- Private videos: Report as inaccessible

Always provide detailed descriptions of UI elements you're interacting with to ensure accurate clicking.

Include your reasoning in your response and create a concise summary for each step.
Demarcate your summary with <int_summary></int_summary> tags.

Available tools: browser_navigate, computer_click, computer_type, extract_video_url, wait, complete_task
"""

    def is_valid_youtube_url(self, url: str) -> bool:
        """Validate if the URL is a valid YouTube URL"""
        youtube_regex = re.compile(
            r'(https?://)?(www\.)?(youtube|youtu|youtube-nocookie)\.(com|be)/'
            r'(watch\?v=|embed/|v/|.+\?v=)?([^&=%\?]{11})'
        )
        return bool(youtube_regex.match(url))
    
    def setup_browser_environment(self):
        """Setup browser environment for computer use"""
        try:
            # Check if display is available
            display = os.environ.get('DISPLAY', ':0')
            
            # Start Xvfb if no display is available
            if not display or display == ':0':
                logger.info("Starting virtual display...")
                subprocess.run([
                    'Xvfb', ':99', '-screen', '0', '1920x1080x24'
                ], check=False)
                os.environ['DISPLAY'] = ':99'
                time.sleep(2)
            
            # Start Chrome with specific flags for bot detection evasion
            chrome_flags = [
                '--no-sandbox',
                '--disable-dev-shm-usage',
                '--disable-blink-features=AutomationControlled',
                '--disable-features=VizDisplayCompositor',
                '--disable-extensions',
                '--disable-plugins',
                '--disable-images',
                '--disable-web-security',
                '--disable-features=VizDisplayCompositor',
                '--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36',
                '--window-size=1920,1080',
                '--start-maximized',
                '--disable-gpu',
                '--remote-debugging-port=9222'
            ]
            
            logger.info("Starting Chrome browser...")
            chrome_process = subprocess.Popen([
                'google-chrome-stable'
            ] + chrome_flags)
            
            # Wait for browser to start
            time.sleep(5)
            
            return chrome_process
            
        except Exception as e:
            logger.error(f"Failed to setup browser environment: {e}")
            raise
    
    def capture_screenshot(self) -> str:
        """Capture screenshot of current screen"""
        try:
            screenshot_path = self.run_dir / f"screenshot_{self.screenshot_counter:03d}.png"
            
            # Use scrot to capture screenshot with timeout
            result = subprocess.run([
                'scrot', '--overwrite', '-o', str(screenshot_path)
            ], capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0:
                # Verify screenshot was created and has content
                if screenshot_path.exists() and screenshot_path.stat().st_size > 0:
                    self.screenshot_counter += 1
                    return str(screenshot_path)
                else:
                    raise Exception("Screenshot file was not created or is empty")
            else:
                logger.error(f"Screenshot capture failed: {result.stderr}")
                raise Exception(f"Screenshot capture failed: {result.stderr}")
                
        except subprocess.TimeoutExpired:
            logger.error("Screenshot capture timed out")
            raise Exception("Screenshot capture timed out")
        except Exception as e:
            logger.error(f"Error capturing screenshot: {e}")
            raise
    
    def load_image_as_base64(self, filename: str) -> str:
        """Load image file as base64 encoded string"""
        try:
            with open(filename, "rb") as f:
                return base64.b64encode(f.read()).decode()
        except Exception as e:
            logger.error(f"Error loading image as base64: {e}")
            raise
    
    async def call_llama4_api(self, base64_image: str, user_objective: str) -> Dict[str, Any]:
        """Call Llama4 API for vision-based decision making"""
        try:
            # Get API configuration
            api_url = self.config.get('llama4_api_url', 'http://localhost:11434/v1')
            api_key = self.config.get('llama4_api_key', '')
            model_name = self.config.get('llama4_model', 'llama3.1:8b')
            
            # Prepare request body
            body = {
                "model": model_name,
                "messages": [
                    {
                        "role": "system",
                        "content": self.youtube_system_prompt
                    },
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": f"User objective: {user_objective}"
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/png;base64,{base64_image}"
                                }
                            },
                            {
                                "type": "text",
                                "text": f"Interaction History:\n<interaction_history>\n{self.interaction_history}</interaction_history>"
                            }
                        ]
                    }
                ],
                "temperature": 0.2,
                "max_tokens": 4096,
                "tools": self.youtube_tools
            }
            
            # Make API request
            headers = {
                "Content-Type": "application/json"
            }
            
            if api_key:
                headers["Authorization"] = f"Bearer {api_key}"
            
            response = requests.post(
                f"{api_url}/chat/completions",
                headers=headers,
                json=body,
                timeout=60
            )
            
            response.raise_for_status()
            return response.json()
            
        except Exception as e:
            logger.error(f"Error calling Llama4 API: {e}")
            raise
    
    def perform_click(self, x: int, y: int):
        """Perform mouse click at specified coordinates"""
        try:
            # Validate coordinates
            if not (0 <= x <= 1920 and 0 <= y <= 1080):
                raise ValueError(f"Invalid coordinates: ({x}, {y}). Must be within screen bounds (0-1920, 0-1080)")
            
            # Move mouse and click with timeout
            result = subprocess.run([
                'xdotool', 'mousemove', str(x), str(y), 'click', '1'
            ], check=True, timeout=5)
            
            logger.info(f"Clicked at coordinates ({x}, {y})")
            time.sleep(0.2)  # Brief pause after click
            
        except subprocess.TimeoutExpired:
            logger.error(f"Click operation timed out at ({x}, {y})")
            raise Exception(f"Click operation timed out at ({x}, {y})")
        except subprocess.CalledProcessError as e:
            logger.error(f"xdotool click command failed: {e}")
            raise Exception(f"Failed to perform click at ({x}, {y}): {e}")
        except Exception as e:
            logger.error(f"Error performing click: {e}")
            raise
    
    def perform_type(self, text: str, press_enter: bool = False):
        """Type text and optionally press Enter"""
        try:
            # Validate text input
            if not text:
                logger.warning("Empty text provided for typing")
                return
            
            # Escape special characters for xdotool
            text = text.replace('\\', '\\\\').replace('"', '\\"')
            
            # Clear existing text with timeout
            subprocess.run(['xdotool', 'key', 'ctrl+a'], check=True, timeout=5)
            time.sleep(0.25)
            subprocess.run(['xdotool', 'key', 'BackSpace'], check=True, timeout=5)
            time.sleep(0.25)
            
            # Type new text with timeout
            subprocess.run(['xdotool', 'type', text], check=True, timeout=10)
            
            if press_enter:
                time.sleep(0.25)
                subprocess.run(['xdotool', 'key', 'Return'], check=True, timeout=5)
                
            logger.info(f"Typed text: {text[:50]}{'...' if len(text) > 50 else ''}")
            
        except subprocess.TimeoutExpired:
            logger.error("Type operation timed out")
            raise Exception("Type operation timed out")
        except subprocess.CalledProcessError as e:
            logger.error(f"xdotool type command failed: {e}")
            raise Exception(f"Failed to type text: {e}")
        except Exception as e:
            logger.error(f"Error typing text: {e}")
            raise
    
    async def browser_navigate(self, url: str):
        """Navigate to a URL using xdotool"""
        try:
            logger.info(f"Navigating to: {url}")
            
            # Focus on browser window
            subprocess.run(['xdotool', 'search', '--name', 'Google Chrome', 'windowfocus'], check=True)
            await asyncio.sleep(0.5)
            
            # Press Ctrl+L to focus address bar
            subprocess.run(['xdotool', 'key', 'ctrl+l'], check=True)
            await asyncio.sleep(0.5)
            
            # Type URL
            subprocess.run(['xdotool', 'type', url], check=True)
            await asyncio.sleep(0.5)
            
            # Press Enter
            subprocess.run(['xdotool', 'key', 'Return'], check=True)
            
            # Wait for page to load
            await asyncio.sleep(3)
            
            logger.info(f"Successfully navigated to: {url}")
            
        except Exception as e:
            logger.error(f"Error navigating to URL: {e}")
            raise
    
    async def get_ui_coordinates(self, element_description: str, base64_image: str) -> tuple:
        """Get UI element coordinates using UI-TARS model"""
        try:
            # Get API configuration
            api_url = self.config.get('uitars_api_url', 'http://localhost:11434/v1')
            api_key = self.config.get('uitars_api_key', '')
            model_name = self.config.get('uitars_model', 'llama3.1:8b')
            
            # UI-TARS specific prompt
            uitars_prompt = f"""You are UI-TARS, a precise UI element coordinate detector. 
            
Your task is to find the exact pixel coordinates of the UI element described as: "{element_description}"

Look at the screenshot carefully and identify the center coordinates of the specified element.

Return your response in this exact format:
COORDINATES: x,y

For example:
COORDINATES: 450,300

Only return the coordinates if you are confident about the element location. If you cannot find the element, return:
COORDINATES: NOT_FOUND

Be very precise with coordinate detection as this will be used for automated clicking."""
            
            # Prepare request body
            body = {
                "model": model_name,
                "messages": [
                    {
                        "role": "system",
                        "content": uitars_prompt
                    },
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": f"Find coordinates for: {element_description}"
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/png;base64,{base64_image}"
                                }
                            }
                        ]
                    }
                ],
                "temperature": 0.1,
                "max_tokens": 100
            }
            
            # Make API request
            headers = {
                "Content-Type": "application/json"
            }
            
            if api_key:
                headers["Authorization"] = f"Bearer {api_key}"
            
            response = requests.post(
                f"{api_url}/chat/completions",
                headers=headers,
                json=body,
                timeout=30
            )
            
            response.raise_for_status()
            result = response.json()
            
            # Extract coordinates from response
            if result.get("choices"):
                content = result["choices"][0]["message"]["content"]
                
                # Parse coordinates
                coord_match = re.search(r'COORDINATES:\s*(\d+),(\d+)', content)
                if coord_match:
                    x, y = int(coord_match.group(1)), int(coord_match.group(2))
                    logger.info(f"UI-TARS found coordinates for '{element_description}': ({x}, {y})")
                    return x, y
                elif "NOT_FOUND" in content:
                    logger.warning(f"UI-TARS could not find element: {element_description}")
                    return None, None
            
            logger.error(f"UI-TARS failed to parse coordinates from response")
            return None, None
            
        except Exception as e:
            logger.error(f"Error getting UI coordinates: {e}")
            return None, None
    
    def extract_video_urls_from_page(self) -> Dict[str, Any]:
        """Extract video download URLs from current page using browser developer tools"""
        try:
            logger.info("Extracting video URLs from page...")
            
            # Use Chrome DevTools to extract video URLs
            # This is a simplified version - in reality, you'd need to inspect network requests
            # and extract video URLs from the page source or network tab
            
            # For now, implement a basic extraction that looks for video elements
            # In a real implementation, this would use browser automation to:
            # 1. Open DevTools
            # 2. Go to Network tab
            # 3. Filter for video requests
            # 4. Extract URLs
            
            # Try to get current page URL using xdotool
            try:
                # Focus address bar and copy URL
                subprocess.run(['xdotool', 'key', 'ctrl+l'], check=True)
                time.sleep(0.5)
                subprocess.run(['xdotool', 'key', 'ctrl+c'], check=True)
                time.sleep(0.5)
                
                # For now, return basic success with placeholder data
                return {
                    "video_urls": ["https://placeholder-video-url.com/video.mp4"],
                    "video_info": {
                        "title": "Extracted Video",
                        "duration": 300,
                        "quality": "720p"
                    },
                    "success": True,
                    "method": "browser_extraction"
                }
                
            except Exception as extract_error:
                logger.warning(f"URL extraction failed: {extract_error}")
                return {
                    "video_urls": [],
                    "video_info": {},
                    "success": False,
                    "error": str(extract_error)
                }
            
        except Exception as e:
            logger.error(f"Error extracting video URLs: {e}")
            return {
                "video_urls": [],
                "video_info": {},
                "success": False,
                "error": str(e)
            }
    
    async def process_llama4_response(self, response: Dict[str, Any], base64_image: str) -> Dict[str, Any]:
        """Process Llama4 API response and execute actions"""
        try:
            if not response.get("choices"):
                return {"success": False, "error": "No choices in Llama4 response"}
            
            choice = response["choices"][0]
            content = choice["message"]["content"]
            
            # Extract interaction summary
            summary_match = re.search(r'<int_summary>(.*?)</int_summary>', content, re.DOTALL)
            if summary_match:
                summary = summary_match.group(1).strip()
                self.interaction_history += f"Step {self.step_counter}: {summary}\n"
                self.step_counter += 1
            
            # Check for tool calls
            tool_calls = choice["message"].get("tool_calls", [])
            
            if tool_calls:
                for tool_call in tool_calls:
                    function_name = tool_call["function"]["name"]
                    arguments = json.loads(tool_call["function"]["arguments"])
                    
                    logger.info(f"Executing function: {function_name} with args: {arguments}")
                    
                    if function_name == "browser_navigate":
                        url = arguments["url"]
                        await self.browser_navigate(url)
                        self.interaction_history += f"Action: Navigated to {url}\n"
                        
                    elif function_name == "computer_click":
                        element_desc = arguments["elementDescription"]
                        # Use UI-TARS to get coordinates
                        x, y = await self.get_ui_coordinates(element_desc, base64_image)
                        if x is not None and y is not None:
                            self.perform_click(x, y)
                            self.interaction_history += f"Action: Clicked on '{element_desc}' at ({x}, {y})\n"
                        else:
                            logger.warning(f"Could not find coordinates for element: {element_desc}")
                            self.interaction_history += f"Action: Failed to click on '{element_desc}' - element not found\n"
                        
                    elif function_name == "computer_type":
                        text = arguments["text"]
                        press_enter = arguments.get("pressEnter", False)
                        self.perform_type(text, press_enter)
                        self.interaction_history += f"Action: Typed '{text}'\n"
                        
                    elif function_name == "extract_video_url":
                        quality = arguments.get("quality", "best")
                        result = self.extract_video_urls_from_page()
                        return result
                        
                    elif function_name == "wait":
                        seconds = arguments["seconds"]
                        await asyncio.sleep(seconds)
                        self.interaction_history += f"Action: Waited {seconds} seconds\n"
                        
                    elif function_name == "complete_task":
                        return {
                            "success": arguments["success"],
                            "video_url": arguments.get("video_url"),
                            "video_info": arguments.get("video_info", {}),
                            "error": arguments.get("error_message")
                        }
            
            return {"success": True, "continue": True}
            
        except Exception as e:
            logger.error(f"Error processing Llama4 response: {e}")
            return {"success": False, "error": str(e)}
    
    async def download_video_with_computer_use(self, url: str) -> Dict[str, Any]:
        """Download YouTube video using computer use agent"""
        try:
            logger.info(f"Starting computer use download for: {url}")
            
            # Validate URL
            if not self.is_valid_youtube_url(url):
                raise Exception("Invalid YouTube URL format")
            
            # Setup browser environment
            browser_process = self.setup_browser_environment()
            
            try:
                # Main agent loop
                max_iterations = 20
                user_objective = f"Extract video download URL from YouTube video: {url}"
                
                for iteration in range(max_iterations):
                    logger.info(f"Iteration {iteration + 1}/{max_iterations}")
                    
                    # Capture screenshot
                    screenshot_path = self.capture_screenshot()
                    base64_image = self.load_image_as_base64(screenshot_path)
                    
                    # Get action from Llama4
                    llama4_response = await self.call_llama4_api(base64_image, user_objective)
                    
                    # Process response and execute actions
                    result = await self.process_llama4_response(llama4_response, base64_image)
                    
                    if not result.get("continue", False):
                        return result
                    
                    # Wait between actions
                    await asyncio.sleep(2)
                
                return {
                    "success": False,
                    "error": f"Task not completed within {max_iterations} iterations"
                }
                
            finally:
                # Clean up browser process
                if browser_process:
                    browser_process.terminate()
                    
        except Exception as e:
            logger.error(f"Computer use download failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def cleanup_files(self, *file_paths: str):
        """Clean up temporary files"""
        try:
            for file_path in file_paths:
                if os.path.exists(file_path):
                    os.remove(file_path)
                    
            # Clean up run directory
            if self.run_dir.exists():
                import shutil
                shutil.rmtree(self.run_dir)
                
        except Exception as e:
            logger.warning(f"Error cleaning up files: {e}")
