"""
Configuration management for the YouTube Analyzer application.
This module provides centralized configuration handling for all services.
"""

import os
from typing import Dict, Any, Optional
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)

@dataclass
class DatabaseConfig:
    """Database configuration settings (for future use)"""
    url: Optional[str] = None
    enabled: bool = False

@dataclass
class OllamaConfig:
    """Ollama configuration settings"""
    host: str = "localhost:11434"
    base_url: str = "http://localhost:11434"
    default_model: str = "llama3.1:8b"
    timeout: int = 30
    max_retries: int = 3

@dataclass
class OpenAIConfig:
    """OpenAI configuration settings"""
    api_key: Optional[str] = None
    default_model: str = "gpt-3.5-turbo"
    max_tokens: int = 4000
    temperature: float = 0.3
    timeout: int = 30

@dataclass
class AnthropicConfig:
    """Anthropic configuration settings"""
    api_key: Optional[str] = None
    default_model: str = "claude-3-sonnet-20240229"
    max_tokens: int = 4000
    temperature: float = 0.3
    timeout: int = 30

@dataclass
class TranscriptionConfig:
    """Transcription service configuration"""
    model_name: str = "base"
    device: str = "auto"  # auto, cpu, cuda
    language: Optional[str] = None
    task: str = "transcribe"
    beam_size: int = 1
    temperature: float = 0.0
    chunk_length: int = 30  # seconds

@dataclass
class ProcessingConfig:
    """Video processing configuration"""
    max_segments: int = 5
    segment_length: int = 60  # seconds
    max_video_length: int = 7200  # 2 hours in seconds
    temp_dir: Optional[str] = None
    cleanup_temp_files: bool = True

@dataclass
class ServerConfig:
    """Server configuration"""
    host: str = "0.0.0.0"
    port: int = 8000
    debug: bool = False
    log_level: str = "INFO"
    cors_enabled: bool = True
    cors_origins: list = None

@dataclass
class SecurityConfig:
    """Security configuration"""
    max_file_size: int = 500 * 1024 * 1024  # 500MB
    allowed_domains: list = None
    rate_limit_enabled: bool = False
    rate_limit_per_minute: int = 60

@dataclass
class ComputerUseConfig:
    """Computer use configuration for YouTube bot detection evasion"""
    enabled: bool = False
    llama4_api_url: str = "http://localhost:11434/v1"
    llama4_api_key: Optional[str] = None
    llama4_model: str = "llama3.1:8b"
    uitars_api_url: str = "http://localhost:11434/v1"
    uitars_api_key: Optional[str] = None
    uitars_model: str = "llama3.1:8b"
    max_iterations: int = 20
    screenshot_delay: float = 2.0
    action_delay: float = 1.0
    browser_timeout: int = 60
    display_size: str = "1920x1080"
    user_agent: str = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36"

class ConfigManager:
    """Centralized configuration manager"""
    
    def __init__(self):
        self.ollama = OllamaConfig()
        self.openai = OpenAIConfig()
        self.anthropic = AnthropicConfig()
        self.transcription = TranscriptionConfig()
        self.processing = ProcessingConfig()
        self.server = ServerConfig()
        self.security = SecurityConfig()
        self.database = DatabaseConfig()
        self.computer_use = ComputerUseConfig()
        
        # Load configuration from environment
        self._load_from_environment()
        
        # Validate configuration
        self._validate_configuration()
    
    def _load_from_environment(self):
        """Load configuration from environment variables"""
        
        # Ollama configuration
        self.ollama.host = os.getenv('OLLAMA_HOST', self.ollama.host)
        self.ollama.base_url = f"http://{self.ollama.host}"
        self.ollama.default_model = os.getenv('OLLAMA_DEFAULT_MODEL', self.ollama.default_model)
        self.ollama.timeout = int(os.getenv('OLLAMA_TIMEOUT', str(self.ollama.timeout)))
        
        # OpenAI configuration
        self.openai.api_key = os.getenv('OPENAI_API_KEY')
        self.openai.default_model = os.getenv('OPENAI_DEFAULT_MODEL', self.openai.default_model)
        self.openai.max_tokens = int(os.getenv('OPENAI_MAX_TOKENS', str(self.openai.max_tokens)))
        self.openai.temperature = float(os.getenv('OPENAI_TEMPERATURE', str(self.openai.temperature)))
        
        # Anthropic configuration
        self.anthropic.api_key = os.getenv('ANTHROPIC_API_KEY')
        self.anthropic.default_model = os.getenv('ANTHROPIC_DEFAULT_MODEL', self.anthropic.default_model)
        self.anthropic.max_tokens = int(os.getenv('ANTHROPIC_MAX_TOKENS', str(self.anthropic.max_tokens)))
        self.anthropic.temperature = float(os.getenv('ANTHROPIC_TEMPERATURE', str(self.anthropic.temperature)))
        
        # Transcription configuration
        self.transcription.model_name = os.getenv('WHISPER_MODEL', self.transcription.model_name)
        self.transcription.device = os.getenv('WHISPER_DEVICE', self.transcription.device)
        self.transcription.language = os.getenv('WHISPER_LANGUAGE', self.transcription.language)
        
        # Processing configuration
        self.processing.max_segments = int(os.getenv('MAX_SEGMENTS', str(self.processing.max_segments)))
        self.processing.segment_length = int(os.getenv('SEGMENT_LENGTH', str(self.processing.segment_length)))
        self.processing.max_video_length = int(os.getenv('MAX_VIDEO_LENGTH', str(self.processing.max_video_length)))
        self.processing.temp_dir = os.getenv('TEMP_DIR', self.processing.temp_dir)
        self.processing.cleanup_temp_files = os.getenv('CLEANUP_TEMP_FILES', 'true').lower() == 'true'
        
        # Server configuration
        self.server.host = os.getenv('HOST', self.server.host)
        self.server.port = int(os.getenv('PORT', str(self.server.port)))
        self.server.debug = os.getenv('DEBUG', 'false').lower() == 'true'
        self.server.log_level = os.getenv('LOG_LEVEL', self.server.log_level)
        self.server.cors_enabled = os.getenv('CORS_ENABLED', 'true').lower() == 'true'
        
        # Security configuration
        self.security.max_file_size = int(os.getenv('MAX_FILE_SIZE', str(self.security.max_file_size)))
        self.security.rate_limit_enabled = os.getenv('RATE_LIMIT_ENABLED', 'false').lower() == 'true'
        self.security.rate_limit_per_minute = int(os.getenv('RATE_LIMIT_PER_MINUTE', str(self.security.rate_limit_per_minute)))
        
        # Database configuration
        self.database.url = os.getenv('DATABASE_URL')
        self.database.enabled = os.getenv('DATABASE_ENABLED', 'false').lower() == 'true'
        
        # Computer use configuration
        self.computer_use.enabled = os.getenv('COMPUTER_USE_ENABLED', 'false').lower() == 'true'
        self.computer_use.llama4_api_url = os.getenv('LLAMA4_API_URL', self.computer_use.llama4_api_url)
        self.computer_use.llama4_api_key = os.getenv('LLAMA4_API_KEY')
        self.computer_use.llama4_model = os.getenv('LLAMA4_MODEL', self.computer_use.llama4_model)
        self.computer_use.uitars_api_url = os.getenv('UITARS_API_URL', self.computer_use.uitars_api_url)
        self.computer_use.uitars_api_key = os.getenv('UITARS_API_KEY')
        self.computer_use.uitars_model = os.getenv('UITARS_MODEL', self.computer_use.uitars_model)
        self.computer_use.max_iterations = int(os.getenv('COMPUTER_USE_MAX_ITERATIONS', str(self.computer_use.max_iterations)))
        self.computer_use.screenshot_delay = float(os.getenv('COMPUTER_USE_SCREENSHOT_DELAY', str(self.computer_use.screenshot_delay)))
        self.computer_use.action_delay = float(os.getenv('COMPUTER_USE_ACTION_DELAY', str(self.computer_use.action_delay)))
        self.computer_use.browser_timeout = int(os.getenv('COMPUTER_USE_BROWSER_TIMEOUT', str(self.computer_use.browser_timeout)))
        self.computer_use.display_size = os.getenv('COMPUTER_USE_DISPLAY_SIZE', self.computer_use.display_size)
        self.computer_use.user_agent = os.getenv('COMPUTER_USE_USER_AGENT', self.computer_use.user_agent)
        
        # Parse list configurations
        if os.getenv('CORS_ORIGINS'):
            self.server.cors_origins = [origin.strip() for origin in os.getenv('CORS_ORIGINS').split(',')]
        
        if os.getenv('ALLOWED_DOMAINS'):
            self.security.allowed_domains = [domain.strip() for domain in os.getenv('ALLOWED_DOMAINS').split(',')]
    
    def _validate_configuration(self):
        """Validate configuration settings"""
        errors = []
        
        # Validate processing settings
        if self.processing.max_segments < 1 or self.processing.max_segments > 20:
            errors.append("max_segments must be between 1 and 20")
        
        if self.processing.segment_length < 10 or self.processing.segment_length > 300:
            errors.append("segment_length must be between 10 and 300 seconds")
        
        if self.processing.max_video_length < 60 or self.processing.max_video_length > 14400:  # 4 hours
            errors.append("max_video_length must be between 60 and 14400 seconds")
        
        # Validate server settings
        if self.server.port < 1 or self.server.port > 65535:
            errors.append("port must be between 1 and 65535")
        
        if self.server.log_level not in ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']:
            errors.append("log_level must be one of: DEBUG, INFO, WARNING, ERROR, CRITICAL")
        
        # Validate transcription settings
        if self.transcription.device not in ['auto', 'cpu', 'cuda']:
            errors.append("transcription device must be one of: auto, cpu, cuda")
        
        if self.transcription.model_name not in ['tiny', 'base', 'small', 'medium', 'large', 'large-v2', 'large-v3']:
            logger.warning(f"Unusual transcription model: {self.transcription.model_name}")
        
        # Validate model settings
        if self.openai.temperature < 0 or self.openai.temperature > 2:
            errors.append("openai temperature must be between 0 and 2")
        
        if self.anthropic.temperature < 0 or self.anthropic.temperature > 2:
            errors.append("anthropic temperature must be between 0 and 2")
        
        if errors:
            error_msg = "Configuration validation errors:\n" + "\n".join(f"- {error}" for error in errors)
            logger.error(error_msg)
            raise ValueError(error_msg)
        
        logger.info("Configuration validation passed")
    
    def get_provider_config(self, provider: str) -> Dict[str, Any]:
        """Get configuration for a specific provider"""
        provider_configs = {
            'ollama': self.ollama,
            'openai': self.openai,
            'anthropic': self.anthropic
        }
        
        config = provider_configs.get(provider.lower())
        if not config:
            raise ValueError(f"Unknown provider: {provider}")
        
        return config.__dict__
    
    def is_provider_configured(self, provider: str) -> bool:
        """Check if a provider is properly configured"""
        provider = provider.lower()
        
        if provider == 'ollama':
            return True  # Ollama doesn't require API key
        elif provider == 'openai':
            return self.openai.api_key is not None
        elif provider == 'anthropic':
            return self.anthropic.api_key is not None
        
        return False
    
    def get_available_providers(self) -> list:
        """Get list of configured providers"""
        providers = []
        
        # Ollama is always available if configured
        providers.append('ollama')
        
        if self.openai.api_key:
            providers.append('openai')
        
        if self.anthropic.api_key:
            providers.append('anthropic')
        
        return providers
    
    def update_api_key(self, provider: str, api_key: str):
        """Update API key for a provider"""
        provider = provider.lower()
        
        if provider == 'openai':
            self.openai.api_key = api_key
        elif provider == 'anthropic':
            self.anthropic.api_key = api_key
        else:
            raise ValueError(f"Cannot update API key for provider: {provider}")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary"""
        return {
            'ollama': self.ollama.__dict__,
            'openai': {**self.openai.__dict__, 'api_key': '***' if self.openai.api_key else None},
            'anthropic': {**self.anthropic.__dict__, 'api_key': '***' if self.anthropic.api_key else None},
            'transcription': self.transcription.__dict__,
            'processing': self.processing.__dict__,
            'server': self.server.__dict__,
            'security': self.security.__dict__,
            'database': self.database.__dict__,
            'computer_use': {
                **self.computer_use.__dict__, 
                'llama4_api_key': '***' if self.computer_use.llama4_api_key else None,
                'uitars_api_key': '***' if self.computer_use.uitars_api_key else None
            }
        }
    
    def log_configuration(self):
        """Log current configuration (without sensitive data)"""
        logger.info("Current configuration:")
        config_dict = self.to_dict()
        
        for section, settings in config_dict.items():
            logger.info(f"  {section.upper()}:")
            for key, value in settings.items():
                logger.info(f"    {key}: {value}")

# Global configuration instance
config = ConfigManager()
