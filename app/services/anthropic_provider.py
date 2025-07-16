import os
from typing import List, Dict, Any
import logging
import anthropic
from .base_model_provider import BaseModelProvider

logger = logging.getLogger(__name__)

class AnthropicProvider(BaseModelProvider):
    """Anthropic model provider for Claude models"""
    
    def __init__(self, model_name: str = "claude-3-sonnet-20240229", api_key: str = None):
        super().__init__("Anthropic", model_name)
        self.api_key = api_key or os.getenv('ANTHROPIC_API_KEY')
        if self.api_key:
            self.client = anthropic.AsyncAnthropic(api_key=self.api_key)
        else:
            self.client = None
        
        # Model pricing per 1K tokens (as of 2024)
        self.model_pricing = {
            "claude-3-opus-20240229": {"input": 0.015, "output": 0.075},
            "claude-3-sonnet-20240229": {"input": 0.003, "output": 0.015},
            "claude-3-haiku-20240307": {"input": 0.00025, "output": 0.00125},
            "claude-instant-1.2": {"input": 0.0008, "output": 0.0024}
        }
    
    async def check_availability(self) -> bool:
        """Check if Anthropic is available with valid API key"""
        try:
            if not self.api_key:
                logger.warning("Anthropic API key not provided")
                self.is_available = False
                return False
            
            if not self.client:
                self.client = anthropic.AsyncAnthropic(api_key=self.api_key)
            
            # Test API connection with a simple request
            try:
                response = await self.client.messages.create(
                    model=self.model_name,
                    max_tokens=10,
                    messages=[{"role": "user", "content": "Hello"}]
                )
                if response.content:
                    self.is_available = True
                    logger.info("Anthropic API is available")
                    return True
                else:
                    self.is_available = False
                    return False
            except Exception as e:
                logger.error(f"Error testing Anthropic API: {str(e)}")
                self.is_available = False
                return False
                
        except Exception as e:
            logger.error(f"Error checking Anthropic availability: {str(e)}")
            self.is_available = False
            return False
    
    async def list_models(self) -> List[Dict[str, Any]]:
        """List available Anthropic models"""
        try:
            if not await self.check_availability():
                return []
            
            # Anthropic doesn't have a models endpoint, so we provide known models
            available_models = [
                {
                    "name": "claude-3-opus-20240229",
                    "id": "claude-3-opus-20240229",
                    "size": "API-based",
                    "modified": "",
                    "display_name": "Claude 3 Opus ($0.015/1K tokens)",
                    "description": "Anthropic Claude 3 Opus - Most capable model",
                    "context_length": 200000,
                    "cost_per_token": 0.000015
                },
                {
                    "name": "claude-3-sonnet-20240229",
                    "id": "claude-3-sonnet-20240229",
                    "size": "API-based",
                    "modified": "",
                    "display_name": "Claude 3 Sonnet ($0.003/1K tokens)",
                    "description": "Anthropic Claude 3 Sonnet - Balanced performance",
                    "context_length": 200000,
                    "cost_per_token": 0.000003
                },
                {
                    "name": "claude-3-haiku-20240307",
                    "id": "claude-3-haiku-20240307",
                    "size": "API-based",
                    "modified": "",
                    "display_name": "Claude 3 Haiku ($0.00025/1K tokens)",
                    "description": "Anthropic Claude 3 Haiku - Fast and cost-effective",
                    "context_length": 200000,
                    "cost_per_token": 0.00000025
                },
                {
                    "name": "claude-instant-1.2",
                    "id": "claude-instant-1.2",
                    "size": "API-based",
                    "modified": "",
                    "display_name": "Claude Instant 1.2 ($0.0008/1K tokens)",
                    "description": "Anthropic Claude Instant - Legacy fast model",
                    "context_length": 100000,
                    "cost_per_token": 0.0000008
                }
            ]
            
            models = []
            for model_info in available_models:
                models.append(self.format_model_info(model_info))
            
            return models
            
        except Exception as e:
            logger.error(f"Error listing Anthropic models: {str(e)}")
            return []
    
    async def generate_summary(self, prompt: str, max_tokens: int = 300) -> str:
        """Generate a summary using Anthropic"""
        try:
            if not await self.check_availability():
                raise Exception("Anthropic is not available")
            
            # Anthropic uses a different message format
            system_message = "You are an expert at creating concise, informative summaries of video content. Focus on extracting the most important information and key insights."
            
            response = await self.client.messages.create(
                model=self.model_name,
                max_tokens=max_tokens,
                temperature=0.3,
                system=system_message,
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            )
            
            return response.content[0].text
            
        except Exception as e:
            logger.error(f"Error generating summary with Anthropic: {str(e)}")
            raise
    
    async def generate_chat_response(self, messages: List[Dict[str, str]], max_tokens: int = 500) -> str:
        """Generate a chat response using Anthropic"""
        try:
            if not await self.check_availability():
                raise Exception("Anthropic is not available")
            
            # Convert messages format and extract system message if present
            system_message = None
            anthropic_messages = []
            
            for message in messages:
                if message.get("role") == "system":
                    system_message = message.get("content")
                else:
                    anthropic_messages.append({
                        "role": message.get("role"),
                        "content": message.get("content")
                    })
            
            # Create the request
            request_params = {
                "model": self.model_name,
                "max_tokens": max_tokens,
                "temperature": 0.3,
                "messages": anthropic_messages
            }
            
            if system_message:
                request_params["system"] = system_message
            
            response = await self.client.messages.create(**request_params)
            
            return response.content[0].text
            
        except Exception as e:
            logger.error(f"Error generating chat response with Anthropic: {str(e)}")
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
