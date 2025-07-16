import os
import json
import subprocess
import asyncio
from typing import List, Dict, Any
import logging
import ollama
from .base_model_provider import BaseModelProvider

logger = logging.getLogger(__name__)

class OllamaProvider(BaseModelProvider):
    """Ollama model provider with enhanced connectivity and error handling"""
    
    def __init__(self, model_name: str = "llama3.1:8b", host: str = None):
        super().__init__("Ollama", model_name)
        self.host = host or os.getenv('OLLAMA_HOST', 'localhost:11434')
        self.base_url = f'http://{self.host}'
        self.client = ollama.AsyncClient(host=self.base_url)
        
    async def check_availability(self) -> bool:
        """Check if Ollama is available using multiple methods"""
        try:
            logger.info(f"Checking Ollama availability at {self.base_url}")
            
            # Method 1: Try using the ollama client directly
            try:
                models = await self.client.list()
                self.is_available = True
                logger.info(f"Ollama available via client at {self.base_url}")
                return True
            except Exception as e:
                logger.warning(f"Ollama client failed: {str(e)}")
            
            # Method 2: Try using curl command (fallback)
            try:
                result = subprocess.run(
                    ['curl', '-s', f'{self.base_url}/api/tags'], 
                    capture_output=True, 
                    text=True, 
                    timeout=10
                )
                
                if result.returncode == 0:
                    response = json.loads(result.stdout)
                    if 'models' in response:
                        self.is_available = True
                        logger.info(f"Ollama available via curl at {self.base_url}")
                        return True
            except Exception as e:
                logger.warning(f"Ollama curl check failed: {str(e)}")
            
            # Method 3: Try alternative hosts if the main one fails
            if self.host == 'host.docker.internal:11434':
                alternative_hosts = ['localhost:11434', 'ollama:11434']
                for alt_host in alternative_hosts:
                    try:
                        alt_url = f'http://{alt_host}'
                        result = subprocess.run(
                            ['curl', '-s', f'{alt_url}/api/tags'], 
                            capture_output=True, 
                            text=True, 
                            timeout=5
                        )
                        
                        if result.returncode == 0:
                            response = json.loads(result.stdout)
                            if 'models' in response:
                                self.host = alt_host
                                self.base_url = alt_url
                                self.client = ollama.AsyncClient(host=alt_url)
                                self.is_available = True
                                logger.info(f"Ollama available via alternative host: {alt_host}")
                                return True
                    except Exception as e:
                        logger.debug(f"Alternative host {alt_host} failed: {str(e)}")
                        continue
            
            logger.warning(f"Ollama not available at {self.base_url}")
            self.is_available = False
            return False
            
        except Exception as e:
            logger.error(f"Error checking Ollama availability: {str(e)}")
            self.is_available = False
            return False
    
    async def test_connection(self) -> Dict[str, Any]:
        """Test connection to Ollama and return detailed status"""
        try:
            # Check if we can connect
            is_available = await self.check_availability()
            
            if is_available:
                # Try to get models to verify full functionality
                models = await self.list_models()
                model_count = len(models)
                
                return {
                    "status": "available",
                    "provider": self.provider_name,
                    "message": f"Ollama is available with {model_count} models",
                    "host": self.host,
                    "base_url": self.base_url,
                    "model_count": model_count,
                    "models": [m.get('name', 'Unknown') for m in models[:5]]  # First 5 models
                }
            else:
                return {
                    "status": "unavailable",
                    "provider": self.provider_name,
                    "message": f"Ollama is not available at {self.base_url}",
                    "host": self.host,
                    "base_url": self.base_url,
                    "model_count": 0
                }
                
        except Exception as e:
            logger.error(f"Error testing Ollama connection: {str(e)}")
            return {
                "status": "error",
                "provider": self.provider_name,
                "message": f"Error connecting to Ollama: {str(e)}",
                "host": self.host,
                "base_url": self.base_url,
                "model_count": 0
            }
    
    async def list_models(self) -> List[Dict[str, Any]]:
        """List available Ollama models"""
        try:
            # First ensure we're connected
            if not await self.check_availability():
                return []
            
            # Try using the client first
            try:
                models_response = await self.client.list()
                models = []
                
                for model in models_response.get('models', []):
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
                    
                    model_info = {
                        "name": model_name,
                        "id": model.get('digest', ''),
                        "size": size_str,
                        "modified": model.get('modified_at', ''),
                        "display_name": f"{model_name} ({size_str})",
                        "description": f"Local Ollama model - {model_name}",
                        "context_length": 4096,  # Default context length
                        "cost_per_token": 0.0  # Free
                    }
                    
                    models.append(self.format_model_info(model_info))
                
                return models
                
            except Exception as e:
                logger.warning(f"Client list failed, trying curl: {str(e)}")
                
                # Fallback to curl
                result = subprocess.run(
                    ['curl', '-s', f'{self.base_url}/api/tags'], 
                    capture_output=True, 
                    text=True, 
                    timeout=10
                )
                
                if result.returncode == 0:
                    response = json.loads(result.stdout)
                    models = []
                    
                    for model in response.get('models', []):
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
                        
                        model_info = {
                            "name": model_name,
                            "id": model.get('digest', ''),
                            "size": size_str,
                            "modified": model.get('modified_at', ''),
                            "display_name": f"{model_name} ({size_str})",
                            "description": f"Local Ollama model - {model_name}",
                            "context_length": 4096,
                            "cost_per_token": 0.0
                        }
                        
                        models.append(self.format_model_info(model_info))
                    
                    return models
                else:
                    logger.error(f"Failed to get models via curl: {result.stderr}")
                    return []
            
        except Exception as e:
            logger.error(f"Error listing Ollama models: {str(e)}")
            return []
    
    async def generate_summary(self, prompt: str, max_tokens: int = 300) -> str:
        """Generate a summary using Ollama"""
        try:
            if not await self.check_availability():
                raise Exception("Ollama is not available")
            
            # Ensure we have a valid model
            if not self.model_name:
                models = await self.list_models()
                if not models:
                    raise Exception("No models available")
                self.model_name = models[0]['name']
            
            response = await self.client.chat(
                model=self.model_name,
                messages=[
                    {
                        'role': 'system',
                        'content': 'You are an expert at creating concise, informative summaries of video content.'
                    },
                    {
                        'role': 'user',
                        'content': prompt
                    }
                ],
                options={
                    'temperature': 0.3,
                    'top_p': 0.9,
                    'max_tokens': max_tokens
                }
            )
            
            return response['message']['content']
            
        except Exception as e:
            logger.error(f"Error generating summary with Ollama: {str(e)}")
            raise
    
    async def generate_chat_response(self, messages: List[Dict[str, str]], max_tokens: int = 500) -> str:
        """Generate a chat response using Ollama"""
        try:
            if not await self.check_availability():
                raise Exception("Ollama is not available")
            
            # Ensure we have a valid model
            if not self.model_name:
                models = await self.list_models()
                if not models:
                    raise Exception("No models available")
                self.model_name = models[0]['name']
            
            response = await self.client.chat(
                model=self.model_name,
                messages=messages,
                options={
                    'temperature': 0.3,
                    'top_p': 0.9,
                    'max_tokens': max_tokens
                }
            )
            
            return response['message']['content']
            
        except Exception as e:
            logger.error(f"Error generating chat response with Ollama: {str(e)}")
            raise
    
    def get_connection_info(self) -> Dict[str, Any]:
        """Get connection information for debugging"""
        return {
            "provider": self.provider_name,
            "host": self.host,
            "base_url": self.base_url,
            "model_name": self.model_name,
            "is_available": self.is_available
        }
