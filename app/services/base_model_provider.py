from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

class BaseModelProvider(ABC):
    """Abstract base class for all model providers (Ollama, OpenAI, Anthropic)"""
    
    def __init__(self, provider_name: str, model_name: str = None):
        self.provider_name = provider_name
        self.model_name = model_name
        self.is_available = False
    
    @abstractmethod
    async def check_availability(self) -> bool:
        """Check if the provider is available and accessible"""
        pass
    
    @abstractmethod
    async def list_models(self) -> List[Dict[str, Any]]:
        """List available models from this provider"""
        pass
    
    @abstractmethod
    async def generate_summary(self, prompt: str, max_tokens: int = 300) -> str:
        """Generate a summary using the provider's model"""
        pass
    
    @abstractmethod
    async def generate_chat_response(self, messages: List[Dict[str, str]], max_tokens: int = 500) -> str:
        """Generate a chat response using the provider's model"""
        pass
    
    def format_model_info(self, model_data: Dict[str, Any]) -> Dict[str, Any]:
        """Format model information for consistent display"""
        return {
            "provider": self.provider_name,
            "name": model_data.get("name", "Unknown"),
            "display_name": model_data.get("display_name", model_data.get("name", "Unknown")),
            "size": model_data.get("size", "Unknown"),
            "id": model_data.get("id", ""),
            "description": model_data.get("description", ""),
            "context_length": model_data.get("context_length", 0),
            "cost_per_token": model_data.get("cost_per_token", 0.0)
        }
    
    async def test_connection(self) -> Dict[str, Any]:
        """Test connection to the provider and return status"""
        try:
            available = await self.check_availability()
            if available:
                models = await self.list_models()
                return {
                    "status": "available",
                    "provider": self.provider_name,
                    "model_count": len(models),
                    "message": f"{self.provider_name} is available with {len(models)} models"
                }
            else:
                return {
                    "status": "unavailable",
                    "provider": self.provider_name,
                    "model_count": 0,
                    "message": f"{self.provider_name} is not available"
                }
        except Exception as e:
            logger.error(f"Error testing {self.provider_name} connection: {str(e)}")
            return {
                "status": "error",
                "provider": self.provider_name,
                "model_count": 0,
                "message": f"Error connecting to {self.provider_name}: {str(e)}"
            }
