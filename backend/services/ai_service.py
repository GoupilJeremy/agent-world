# 🤖 Agent World - AI Service
# Version: 0.1.0 (MVP)
# Description: Service pour l'intégration des modèles IA

"""
AI Service for Agent World.

Ce service contient la logique pour interagir avec les différents modèles IA
(Mistral, OpenAI, etc.). Il fournit une interface unifiée pour tous les modèles.
"""

import os
import time
from typing import Optional, Dict, Any, List, Union
from enum import Enum
from ..models.base import db


class AIModelType(str, Enum):
    """Types of supported AI models."""
    MISTRAL = "mistral"
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    LLAMA = "llama"
    GEMMA = "gemma"


class AIService:
    """
    Service class for interacting with AI models.
    
    This service provides a unified interface for different AI model providers.
    It handles authentication, request formatting, and response parsing.
    """
    
    # Model configuration mapping
    MODEL_CONFIG = {
        'mistral-tiny': {'type': AIModelType.MISTRAL, 'endpoint': 'tiny'},
        'mistral-small': {'type': AIModelType.MISTRAL, 'endpoint': 'small'},
        'mistral-medium': {'type': AIModelType.MISTRAL, 'endpoint': 'medium'},
        'mistral-large': {'type': AIModelType.MISTRAL, 'endpoint': 'large'},
        'gpt-3.5-turbo': {'type': AIModelType.OPENAI, 'endpoint': 'gpt-3.5-turbo'},
        'gpt-4': {'type': AIModelType.OPENAI, 'endpoint': 'gpt-4'},
        'gpt-4-turbo': {'type': AIModelType.OPENAI, 'endpoint': 'gpt-4-turbo'},
    }
    
    def __init__(self):
        """Initialize the AIService."""
        self.connectors = {
            AIModelType.MISTRAL: MistralConnector(),
            AIModelType.OPENAI: OpenAIConnector(),
            AIModelType.ANTHROPIC: AnthropicConnector(),
        }
        self.default_model = os.environ.get('DEFAULT_AI_MODEL', 'mistral-tiny')
    
    def get_connector(self, model_type: AIModelType) -> 'BaseAIConnector':
        """
        Get the connector for a specific model type.
        
        Args:
            model_type: Type of AI model
            
        Returns:
            Connector instance
        """
        return self.connectors.get(model_type, self.connectors[AIModelType.MISTRAL])
    
    def parse_model_string(self, model_string: str) -> Dict[str, Any]:
        """
        Parse a model string to extract type and configuration.
        
        Args:
            model_string: String identifier for the model (e.g., 'mistral-tiny')
            
        Returns:
            Dictionary with model type and configuration
        """
        model_string = model_string.lower()
        
        for model_key, config in self.MODEL_CONFIG.items():
            if model_key in model_string:
                return config
        
        # Default to mistral-tiny
        return self.MODEL_CONFIG['mistral-tiny']
    
    def generate(self, prompt: str, model: str = None, 
                configuration: Optional[Dict[str, Any]] = None,
                max_tokens: int = 1000, temperature: float = 0.7,
                stream: bool = False) -> Dict[str, Any]:
        """
        Generate text using the specified AI model.
        
        Args:
            prompt: The input prompt for the model
            model: Model identifier (default: self.default_model)
            configuration: Optional model configuration
            max_tokens: Maximum number of tokens to generate (default: 1000)
            temperature: Sampling temperature (0-2, default: 0.7)
            stream: Whether to stream the response (default: False)
            
        Returns:
            Dictionary containing the generated text and metadata
            
        Raises:
            ValueError: If model is not supported or configuration is invalid
        """
        model = model or self.default_model
        model_config = self.parse_model_string(model)
        model_type = model_config['type']
        model_endpoint = model_config['endpoint']
        
        connector = self.get_connector(model_type)
        
        # Prepare request parameters
        request_params = {
            'prompt': prompt,
            'model': model_endpoint,
            'max_tokens': max_tokens,
            'temperature': temperature,
            'stream': stream
        }
        
        if configuration:
            request_params.update(configuration)
        
        # Call the appropriate connector
        start_time = time.time()
        result = connector.generate(**request_params)
        duration = time.time() - start_time
        
        # Format the response
        response = {
            'model': model,
            'model_type': model_type.value,
            'prompt': prompt,
            'generated_text': result.get('text', ''),
            'tokens_used': result.get('tokens_used', 0),
            'duration_seconds': duration,
            'finish_reason': result.get('finish_reason', 'stop')
        }
        
        return response
    
    def chat(self, messages: List[Dict[str, Any]], model: str = None,
             configuration: Optional[Dict[str, Any]] = None,
             max_tokens: int = 1000, temperature: float = 0.7) -> Dict[str, Any]:
        """
        Generate a chat completion using the specified AI model.
        
        Args:
            messages: List of message dictionaries (role: 'user' or 'assistant', content: str)
            model: Model identifier (default: self.default_model)
            configuration: Optional model configuration
            max_tokens: Maximum number of tokens to generate (default: 1000)
            temperature: Sampling temperature (0-2, default: 0.7)
            
        Returns:
            Dictionary containing the assistant's response and metadata
        """
        model = model or self.default_model
        model_config = self.parse_model_string(model)
        model_type = model_config['type']
        model_endpoint = model_config['endpoint']
        
        connector = self.get_connector(model_type)
        
        request_params = {
            'messages': messages,
            'model': model_endpoint,
            'max_tokens': max_tokens,
            'temperature': temperature
        }
        
        if configuration:
            request_params.update(configuration)
        
        start_time = time.time()
        result = connector.chat(**request_params)
        duration = time.time() - start_time
        
        return {
            'model': model,
            'model_type': model_type.value,
            'messages': messages,
            'response': result.get('message', {}),
            'tokens_used': result.get('tokens_used', 0),
            'duration_seconds': duration
        }
    
    def get_available_models(self) -> List[str]:
        """
        Get a list of all available models.
        
        Returns:
            List of available model identifiers
        """
        return list(self.MODEL_CONFIG.keys())
    
    def validate_model(self, model: str) -> bool:
        """
        Validate if a model is supported.
        
        Args:
            model: Model identifier to validate
            
        Returns:
            True if model is supported, False otherwise
        """
        return model.lower() in [m.lower() for m in self.get_available_models()]


class BaseAIConnector:
    """Base class for AI model connectors."""
    
    def __init__(self):
        """Initialize the connector."""
        self.api_key = None
        self.base_url = None
    
    def generate(self, prompt: str, model: str, **kwargs) -> Dict[str, Any]:
        """
        Generate text from a prompt.
        
        Args:
            prompt: Input prompt
            model: Model identifier
            **kwargs: Additional parameters
            
        Returns:
            Dictionary with generation results
            
        Raises:
            NotImplementedError: Must be implemented by subclasses
        """
        raise NotImplementedError("Subclasses must implement generate method")
    
    def chat(self, messages: List[Dict[str, Any]], model: str, **kwargs) -> Dict[str, Any]:
        """
        Generate a chat completion.
        
        Args:
            messages: List of message dictionaries
            model: Model identifier
            **kwargs: Additional parameters
            
        Returns:
            Dictionary with chat results
            
        Raises:
            NotImplementedError: Must be implemented by subclasses
        """
        raise NotImplementedError("Subclasses must implement chat method")
    
    def _handle_error(self, error: Exception) -> Dict[str, Any]:
        """
        Handle API errors and return a standardized response.
        
        Args:
            error: The exception that occurred
            
        Returns:
            Dictionary with error information
        """
        return {
            'error': str(error),
            'text': f"Error generating response: {str(error)}",
            'tokens_used': 0
        }


class MistralConnector(BaseAIConnector):
    """Connector for Mistral AI models."""
    
    def __init__(self):
        """Initialize the Mistral connector."""
        super().__init__()
        self.api_key = os.environ.get('MISTRAL_API_KEY')
        self.base_url = 'https://api.mistral.ai/v1'
    
    def generate(self, prompt: str, model: str, **kwargs) -> Dict[str, Any]:
        """
        Generate text using Mistral API.
        
        Note: This is a mock implementation for MVP.
        Actual API calls will be implemented in a future version.
        """
        if not self.api_key:
            return {
                'error': 'MISTRAL_API_KEY not configured',
                'text': 'Mistral API is not configured. Please set MISTRAL_API_KEY environment variable.',
                'tokens_used': 0
            }
        
        # Mock response for MVP
        # TODO: Implement actual API call
        return {
            'text': f"[Mock Mistral {model} response]\n\n{prompt}",
            'tokens_used': 10,
            'finish_reason': 'stop'
        }
    
    def chat(self, messages: List[Dict[str, Any]], model: str, **kwargs) -> Dict[str, Any]:
        """
        Generate chat completion using Mistral API.
        
        Note: This is a mock implementation for MVP.
        """
        if not self.api_key:
            return {
                'error': 'MISTRAL_API_KEY not configured',
                'message': {'role': 'assistant', 'content': 'Mistral API is not configured.'},
                'tokens_used': 0
            }
        
        # Mock response
        return {
            'message': {
                'role': 'assistant',
                'content': f"[Mock Mistral {model} chat response]\n\nI'm a helpful AI assistant."
            },
            'tokens_used': 20,
            'finish_reason': 'stop'
        }


class OpenAIConnector(BaseAIConnector):
    """Connector for OpenAI models."""
    
    def __init__(self):
        """Initialize the OpenAI connector."""
        super().__init__()
        self.api_key = os.environ.get('OPENAI_API_KEY')
        self.base_url = 'https://api.openai.com/v1'
    
    def generate(self, prompt: str, model: str, **kwargs) -> Dict[str, Any]:
        """
        Generate text using OpenAI API.
        
        Note: This is a mock implementation for MVP.
        """
        if not self.api_key:
            return {
                'error': 'OPENAI_API_KEY not configured',
                'text': 'OpenAI API is not configured. Please set OPENAI_API_KEY environment variable.',
                'tokens_used': 0
            }
        
        # Mock response
        return {
            'text': f"[Mock OpenAI {model} response]\n\n{prompt}",
            'tokens_used': 15,
            'finish_reason': 'stop'
        }
    
    def chat(self, messages: List[Dict[str, Any]], model: str, **kwargs) -> Dict[str, Any]:
        """
        Generate chat completion using OpenAI API.
        
        Note: This is a mock implementation for MVP.
        """
        if not self.api_key:
            return {
                'error': 'OPENAI_API_KEY not configured',
                'message': {'role': 'assistant', 'content': 'OpenAI API is not configured.'},
                'tokens_used': 0
            }
        
        # Mock response
        return {
            'message': {
                'role': 'assistant',
                'content': f"[Mock OpenAI {model} chat response]\n\nI'm a helpful AI assistant."
            },
            'tokens_used': 25,
            'finish_reason': 'stop'
        }


class AnthropicConnector(BaseAIConnector):
    """Connector for Anthropic models."""
    
    def __init__(self):
        """Initialize the Anthropic connector."""
        super().__init__()
        self.api_key = os.environ.get('ANTHROPIC_API_KEY')
        self.base_url = 'https://api.anthropic.com/v1'
    
    def generate(self, prompt: str, model: str, **kwargs) -> Dict[str, Any]:
        """
        Generate text using Anthropic API.
        
        Note: This is a mock implementation for MVP.
        """
        if not self.api_key:
            return {
                'error': 'ANTHROPIC_API_KEY not configured',
                'text': 'Anthropic API is not configured.',
                'tokens_used': 0
            }
        
        # Mock response
        return {
            'text': f"[Mock Anthropic {model} response]\n\n{prompt}",
            'tokens_used': 12,
            'finish_reason': 'end_turn'
        }
    
    def chat(self, messages: List[Dict[str, Any]], model: str, **kwargs) -> Dict[str, Any]:
        """
        Generate chat completion using Anthropic API.
        
        Note: This is a mock implementation for MVP.
        """
        if not self.api_key:
            return {
                'error': 'ANTHROPIC_API_KEY not configured',
                'message': {'role': 'assistant', 'content': 'Anthropic API is not configured.'},
                'tokens_used': 0
            }
        
        # Mock response
        return {
            'message': {
                'role': 'assistant',
                'content': f"[Mock Anthropic {model} chat response]\n\nI am a helpful AI assistant."
            },
            'tokens_used': 18,
            'finish_reason': 'end_turn'
        }
