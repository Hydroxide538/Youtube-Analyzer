import os
from typing import List, Dict, Any
import logging
import openai
from .base_model_provider import BaseModelProvider

logger = logging.getLogger(__name__)

class OpenAIProvider(BaseModelProvider):
    """OpenAI model provider for GPT models"""
    
    def __init__(self, model_name: str = "gpt-3.5-turbo", api_key: str = None):
        super().__init__("OpenAI", model_name)
        self.api_key = api_key or os.getenv('OPENAI_API_KEY')
        if self.api_key:
            self.client = openai.AsyncOpenAI(api_key=self.api_key)
        else:
            self.client = None
        
        # Model pricing per 1K tokens (as of 2024)
        self.model_pricing = {
            "gpt-4": {"input": 0.03, "output": 0.06},
            "gpt-4-turbo": {"input": 0.01, "output": 0.03},
            "gpt-3.5-turbo": {"input": 0.0015, "output": 0.002},
            "gpt-3.5-turbo-16k": {"input": 0.003, "output": 0.004}
        }
    
    async def check_availability(self) -> bool:
        """Check if OpenAI is available with valid API key"""
        try:
            if not self.api_key:
                logger.warning("OpenAI API key not provided")
                self.is_available = False
                return False
            
            if not self.client:
                self.client = openai.AsyncOpenAI(api_key=self.api_key)
            
            # Test API connection with a simple request
            models = await self.client.models.list()
            if models.data:
                self.is_available = True
                logger.info("OpenAI API is available")
                return True
            else:
                self.is_available = False
                return False
                
        except Exception as e:
            logger.error(f"Error checking OpenAI availability: {str(e)}")
            self.is_available = False
            return False
    
    async def list_models(self) -> List[Dict[str, Any]]:
        """List available OpenAI models"""
        try:
            if not await self.check_availability():
                return []
            
            # Get available models from OpenAI API
            models_response = await self.client.models.list()
            models = []
            
            # Filter for chat models and add relevant information
            chat_models = [
                "gpt-4",
                "gpt-4-turbo",
                "gpt-3.5-turbo",
                "gpt-3.5-turbo-16k"
            ]
            
            for model in models_response.data:
                if any(chat_model in model.id for chat_model in chat_models):
                    # Get pricing info
                    pricing = self.model_pricing.get(model.id, {"input": 0.0, "output": 0.0})
                    
                    # Determine context length
                    context_length = 4096
                    if "16k" in model.id:
                        context_length = 16384
                    elif "gpt-4" in model.id:
                        context_length = 8192
                    
                    model_info = {
                        "name": model.id,
                        "id": model.id,
                        "size": "API-based",
                        "modified": "",
                        "display_name": f"{model.id} (${pricing['input']:.4f}/1K tokens)",
                        "description": f"OpenAI {model.id} - Cloud-based API",
                        "context_length": context_length,
                        "cost_per_token": pricing['input'] / 1000
                    }
                    
                    models.append(self.format_model_info(model_info))
            
            # If no models found via API, provide defaults
            if not models:
                default_models = [
                    {
                        "name": "gpt-3.5-turbo",
                        "id": "gpt-3.5-turbo",
                        "size": "API-based",
                        "modified": "",
                        "display_name": "gpt-3.5-turbo ($0.0015/1K tokens)",
                        "description": "OpenAI GPT-3.5 Turbo - Fast and cost-effective",
                        "context_length": 4096,
                        "cost_per_token": 0.0000015
                    },
                    {
                        "name": "gpt-4",
                        "id": "gpt-4",
                        "size": "API-based",
                        "modified": "",
                        "display_name": "gpt-4 ($0.03/1K tokens)",
                        "description": "OpenAI GPT-4 - Most capable model",
                        "context_length": 8192,
                        "cost_per_token": 0.00003
                    }
                ]
                
                for model_info in default_models:
                    models.append(self.format_model_info(model_info))
            
            return models
            
        except Exception as e:
            logger.error(f"Error listing OpenAI models: {str(e)}")
            return []
    
    async def generate_summary(self, prompt: str, max_tokens: int = 300) -> str:
        """Generate a summary using OpenAI"""
        try:
            if not await self.check_availability():
                raise Exception("OpenAI is not available")
            
            response = await self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert at creating concise, informative summaries of video content. Focus on extracting the most important information and key insights."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                max_tokens=max_tokens,
                temperature=0.3,
                top_p=0.9
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"Error generating summary with OpenAI: {str(e)}")
            raise
    
    async def generate_chat_response(self, messages: List[Dict[str, str]], max_tokens: int = 500) -> str:
        """Generate a chat response using OpenAI"""
        try:
            if not await self.check_availability():
                raise Exception("OpenAI is not available")
            
            response = await self.client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                max_tokens=max_tokens,
                temperature=0.3,
                top_p=0.9
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"Error generating chat response with OpenAI: {str(e)}")
            raise
    
    def get_connection_info(self) -> Dict[str, Any]:
        """Get connection information for debugging"""
        return {
            "provider": self.provider_name,
            "model_name": self.model_name,
            "api_key_provided": bool(self.api_key),
            "is_available": self.is_available
        }
    
    def estimate_cost(self, input_tokens: int, output_tokens: int) -> float:
        """Estimate cost for a request"""
        pricing = self.model_pricing.get(self.model_name, {"input": 0.0, "output": 0.0})
        input_cost = (input_tokens / 1000) * pricing["input"]
        output_cost = (output_tokens / 1000) * pricing["output"]
        return input_cost + output_cost
