import os
import asyncio
from typing import List, Dict, Any, Optional
import logging
from .base_model_provider import BaseModelProvider
from .ollama_provider import OllamaProvider
from .openai_provider import OpenAIProvider
from .anthropic_provider import AnthropicProvider

logger = logging.getLogger(__name__)

class ModelManager:
    """Manages multiple model providers and provides unified access to all models"""
    
    def __init__(self):
        self.providers: Dict[str, BaseModelProvider] = {}
        self.available_providers: List[str] = []
        self.all_models: List[Dict[str, Any]] = []
        self.initialized = False
        
    async def initialize(self, openai_api_key: str = None, anthropic_api_key: str = None, ollama_host: str = None):
        """Initialize all providers and check their availability"""
        try:
            logger.info("Initializing model manager...")
            
            # Clear existing providers
            self.providers.clear()
            self.available_providers.clear()
            self.all_models.clear()
            
            # Initialize providers with error handling for each
            initialization_errors = []
            
            # Initialize Ollama provider
            try:
                ollama_provider = OllamaProvider(host=ollama_host)
                self.providers["Ollama"] = ollama_provider
                logger.info("Ollama provider initialized")
            except Exception as e:
                initialization_errors.append(f"Ollama: {str(e)}")
                logger.warning(f"Failed to initialize Ollama provider: {str(e)}")
            
            # Initialize OpenAI provider
            try:
                openai_provider = OpenAIProvider(api_key=openai_api_key)
                self.providers["OpenAI"] = openai_provider
                logger.info("OpenAI provider initialized")
            except Exception as e:
                initialization_errors.append(f"OpenAI: {str(e)}")
                logger.warning(f"Failed to initialize OpenAI provider: {str(e)}")
            
            # Initialize Anthropic provider
            try:
                anthropic_provider = AnthropicProvider(api_key=anthropic_api_key)
                self.providers["Anthropic"] = anthropic_provider
                logger.info("Anthropic provider initialized")
            except Exception as e:
                initialization_errors.append(f"Anthropic: {str(e)}")
                logger.warning(f"Failed to initialize Anthropic provider: {str(e)}")
            
            # Check availability of all providers
            await self.check_all_providers()
            
            # Load all models
            await self.load_all_models()
            
            self.initialized = True
            logger.info(f"Model manager initialized with {len(self.available_providers)} available providers")
            
            # Log initialization summary
            if initialization_errors:
                logger.warning(f"Provider initialization errors: {'; '.join(initialization_errors)}")
            
            if not self.available_providers:
                logger.warning("No providers are available! Please check your configuration.")
            
        except Exception as e:
            logger.error(f"Critical error initializing model manager: {str(e)}")
            # Don't raise the error - allow partial initialization
            self.initialized = True  # Mark as initialized even with errors
    
    async def check_all_providers(self):
        """Check availability of all providers"""
        self.available_providers = []
        
        # Check each provider concurrently
        tasks = []
        for provider_name, provider in self.providers.items():
            tasks.append(self._check_provider_availability(provider_name, provider))
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for result in results:
            if isinstance(result, Exception):
                logger.error(f"Error checking provider: {result}")
            elif result:
                self.available_providers.append(result)
        
        logger.info(f"Available providers: {self.available_providers}")
    
    async def _check_provider_availability(self, provider_name: str, provider: BaseModelProvider) -> Optional[str]:
        """Check if a specific provider is available"""
        try:
            if await provider.check_availability():
                return provider_name
            return None
        except Exception as e:
            logger.error(f"Error checking {provider_name}: {str(e)}")
            return None
    
    async def load_all_models(self):
        """Load models from all available providers"""
        self.all_models = []
        
        # Load models from each available provider
        tasks = []
        for provider_name in self.available_providers:
            provider = self.providers[provider_name]
            tasks.append(self._load_provider_models(provider_name, provider))
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for result in results:
            if isinstance(result, Exception):
                logger.error(f"Error loading models: {result}")
            elif result:
                self.all_models.extend(result)
        
        logger.info(f"Loaded {len(self.all_models)} models from {len(self.available_providers)} providers")
    
    async def _load_provider_models(self, provider_name: str, provider: BaseModelProvider) -> List[Dict[str, Any]]:
        """Load models from a specific provider"""
        try:
            return await provider.list_models()
        except Exception as e:
            logger.error(f"Error loading models from {provider_name}: {str(e)}")
            return []
    
    async def get_all_models(self) -> List[Dict[str, Any]]:
        """Get all available models from all providers"""
        if not self.initialized:
            await self.initialize()
        
        return self.all_models
    
    async def get_provider_models(self, provider_name: str) -> List[Dict[str, Any]]:
        """Get models from a specific provider"""
        if provider_name not in self.providers:
            return []
        
        provider = self.providers[provider_name]
        return await provider.list_models()
    
    def get_provider_by_model(self, model_name: str) -> Optional[BaseModelProvider]:
        """Get the provider for a specific model"""
        for model in self.all_models:
            if model.get("name") == model_name:
                provider_name = model.get("provider")
                return self.providers.get(provider_name)
        return None
    
    async def generate_summary(self, model_name: str, prompt: str, max_tokens: int = 300) -> str:
        """Generate a summary using the specified model"""
        provider = self.get_provider_by_model(model_name)
        if not provider:
            raise Exception(f"Model {model_name} not found")
        
        # Update the provider's model name
        provider.model_name = model_name
        
        return await provider.generate_summary(prompt, max_tokens)
    
    async def generate_chat_response(self, model_name: str, messages: List[Dict[str, str]], max_tokens: int = 500) -> str:
        """Generate a chat response using the specified model"""
        provider = self.get_provider_by_model(model_name)
        if not provider:
            raise Exception(f"Model {model_name} not found")
        
        # Update the provider's model name
        provider.model_name = model_name
        
        return await provider.generate_chat_response(messages, max_tokens)
    
    def get_provider_status(self) -> Dict[str, Any]:
        """Get status of all providers"""
        status = {
            "initialized": self.initialized,
            "available_providers": self.available_providers,
            "total_models": len(self.all_models),
            "providers": {}
        }
        
        for provider_name, provider in self.providers.items():
            is_available = provider_name in self.available_providers
            model_count = len([m for m in self.all_models if m.get("provider") == provider_name])
            
            status["providers"][provider_name] = {
                "available": is_available,
                "is_available": provider.is_available,
                "model_count": model_count,
                "status": "available" if is_available else "unavailable",
                "message": f"{provider_name} is {'available' if is_available else 'unavailable'}"
            }
        
        return status
    
    async def get_detailed_provider_status(self) -> Dict[str, Any]:
        """Get detailed status of all providers with real-time checks"""
        status = {
            "initialized": self.initialized,
            "available_providers": self.available_providers,
            "total_models": len(self.all_models),
            "providers": {}
        }
        
        # Get real-time status for each provider
        for provider_name, provider in self.providers.items():
            try:
                # Check availability in real-time
                is_available = await provider.check_availability()
                model_count = len([m for m in self.all_models if m.get("provider") == provider_name])
                
                status["providers"][provider_name] = {
                    "available": is_available,
                    "is_available": is_available,
                    "model_count": model_count,
                    "status": "available" if is_available else "unavailable",
                    "message": f"{provider_name} is {'available' if is_available else 'unavailable'} ({model_count} models)"
                }
            except Exception as e:
                logger.error(f"Error getting status for {provider_name}: {str(e)}")
                status["providers"][provider_name] = {
                    "available": False,
                    "is_available": False,
                    "model_count": 0,
                    "status": "error",
                    "message": f"{provider_name} error: {str(e)}"
                }
        
        return status
    
    def get_recommended_model(self, provider_preference: str = None) -> Optional[Dict[str, Any]]:
        """Get a recommended model based on availability and preference"""
        if not self.all_models:
            return None
        
        # If a provider preference is specified, try to find a model from that provider
        if provider_preference:
            for model in self.all_models:
                if model.get("provider") == provider_preference:
                    return model
        
        # Fallback to the first available model, preferring free models
        free_models = [m for m in self.all_models if m.get("cost_per_token", 0) == 0]
        if free_models:
            return free_models[0]
        
        return self.all_models[0] if self.all_models else None
    
    async def test_all_connections(self) -> Dict[str, Any]:
        """Test connections to all providers"""
        test_results = {}
        
        tasks = []
        for provider_name, provider in self.providers.items():
            tasks.append(self._test_provider_connection(provider_name, provider))
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for i, result in enumerate(results):
            provider_name = list(self.providers.keys())[i]
            if isinstance(result, Exception):
                test_results[provider_name] = {
                    "status": "error",
                    "message": str(result)
                }
            else:
                test_results[provider_name] = result
        
        return test_results
    
    async def _test_provider_connection(self, provider_name: str, provider: BaseModelProvider) -> Dict[str, Any]:
        """Test connection to a specific provider"""
        try:
            return await provider.test_connection()
        except Exception as e:
            return {
                "status": "error",
                "provider": provider_name,
                "message": str(e)
            }
    
    def get_model_info(self, model_name: str) -> Optional[Dict[str, Any]]:
        """Get detailed information about a specific model"""
        for model in self.all_models:
            if model.get("name") == model_name:
                return model
        return None
    
    def get_models_by_provider(self, provider_name: str) -> List[Dict[str, Any]]:
        """Get all models from a specific provider"""
        return [model for model in self.all_models if model.get("provider") == provider_name]
