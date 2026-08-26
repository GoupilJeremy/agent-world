# 🔐 Agent World - Log Masking Service
# Version: 1.0.0 (EPIC 10 - US-067)
# Description: Service pour masquer les données sensibles dans les logs

"""
Log Masking Service for Agent World.

Ce service fournit un filtre de logging qui masque automatiquement les données sensibles
avant qu'elles ne soient écrites dans les logs.

Fonctionnalités :
- Masquage automatique des champs sensibles (clés API, tokens, mots de passe, etc.)
- Configuration des champs à masquer
- Intégration avec le système de logging Python
"""

import logging
import re
from typing import Any, Callable, Dict, List, Optional, Pattern, Set, Union


# Default fields to mask
DEFAULT_SENSITIVE_FIELDS = {
    # API keys and secrets
    "api_key",
    "apikey",
    "secret",
    "secret_key",
    "private_key",
    "access_key",
    "secret_token",
    
    # Authentication
    "password",
    "passwd",
    "pwd",
    "token",
    "access_token",
    "refresh_token",
    "auth_token",
    "bearer",
    "authorization",
    
    # Two-factor authentication
    "recovery_code",
    "recovery_codes",
    "totp",
    "2fa",
    "two_factor",
    
    # Personal information
    "email",
    "credit_card",
    "creditcard",
    "ssn",
    "social_security",
    
    # Database
    "connection_string",
    "db_url",
    "database_url",
}

# Patterns to detect sensitive data in strings
DEFAULT_SENSITIVE_PATTERNS: List[Pattern[str]] = [
    # API keys (common formats)
    re.compile(r"sk-[a-zA-Z0-9]{20,}", re.IGNORECASE),  # Stripe, OpenAI, etc.
    re.compile(r"pk-[a-zA-Z0-9]{20,}", re.IGNORECASE),  # Public keys
    re.compile(r"[a-zA-Z0-9]{32,64}", re.IGNORECASE),   # Generic long alphanumeric strings
    
    # Bearer tokens
    re.compile(r"Bearer [a-zA-Z0-9\-\_\.]+\.[a-zA-Z0-9\-\_\.]+\.[a-zA-Z0-9\-\_\.]+", re.IGNORECASE),
    
    # Basic auth
    re.compile(r"Basic [a-zA-Z0-9\+/=]+", re.IGNORECASE),
    
    # Passwords in URLs
    re.compile(r"://[^:]+:[^@]+@", re.IGNORECASE),
    
    # Email addresses
    re.compile(r"[a-zA-Z0-9\._%+-]+@[a-zA-Z0-9\.-]+\.[a-zA-Z]{2,}", re.IGNORECASE),
    
    # Credit card numbers (basic pattern)
    re.compile(r"\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b"),
    
    # SSN (US)
    re.compile(r"\b\d{3}-\d{2}-\d{4}\b"),
]


class SensitiveDataFilter(logging.Filter):
    """
    Logging filter that masks sensitive data in log messages.
    
    This filter can be added to any logger to automatically mask sensitive
    information before it's written to the log.
    """
    
    def __init__(
        self,
        sensitive_fields: Optional[Set[str]] = None,
        sensitive_patterns: Optional[List[Pattern[str]]] = None,
        mask_char: str = "*",
        show_last: int = 4,
    ):
        """
        Initialize the SensitiveDataFilter.
        
        Args:
            sensitive_fields: Set of field names to mask in dictionaries
            sensitive_patterns: List of regex patterns to detect sensitive data
            mask_char: Character to use for masking
            show_last: Number of characters to show at the end of masked values
        """
        super().__init__()
        
        self.sensitive_fields = sensitive_fields or DEFAULT_SENSITIVE_FIELDS
        self.sensitive_patterns = sensitive_patterns or DEFAULT_SENSITIVE_PATTERNS
        self.mask_char = mask_char
        self.show_last = show_last
    
    def mask_value(self, value: Any) -> Any:
        """
        Mask a single value if it contains sensitive data.
        
        Args:
            value: The value to mask
            
        Returns:
            Masked value
        """
        if value is None:
            return value
        
        if isinstance(value, str):
            # Check if the value matches any sensitive pattern
            for pattern in self.sensitive_patterns:
                if pattern.search(value):
                    return self._mask_string(value)
            return value
        
        if isinstance(value, dict):
            return self.mask_dict(value)
        
        if isinstance(value, (list, tuple)):
            return type(value)(self.mask_value(v) for v in value)
        
        return value
    
    def _mask_string(self, value: str) -> str:
        """Mask a string value."""
        if len(value) <= self.show_last:
            return self.mask_char * len(value)
        return self.mask_char * (len(value) - self.show_last) + value[-self.show_last:]
    
    def mask_dict(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Mask sensitive fields in a dictionary.
        
        Args:
            data: The dictionary to mask
            
        Returns:
            A new dictionary with sensitive fields masked
        """
        if not isinstance(data, dict):
            return data
        
        result = {}
        for key, value in data.items():
            key_lower = key.lower()
            
            # Check if the key is a sensitive field
            is_sensitive = any(
                sensitive_field in key_lower 
                for sensitive_field in self.sensitive_fields
            )
            
            if is_sensitive:
                result[key] = self._mask_string(value) if isinstance(value, str) else "[MASKED]"
            else:
                result[key] = self.mask_value(value)
        
        return result
    
    def filter(self, record: logging.LogRecord) -> bool:
        """
        Filter a log record, masking sensitive data.
        
        Args:
            record: The log record to filter
            
        Returns:
            True (always returns True to allow the log to be written)
        """
        # Process the message
        if isinstance(record.msg, dict):
            record.msg = self.mask_dict(record.msg)
        elif isinstance(record.msg, str):
            record.msg = self.mask_string_values(record.msg)
        
        # Process arguments
        if record.args:
            if isinstance(record.args, dict):
                record.args = self.mask_dict(record.args)
            elif isinstance(record.args, tuple):
                record.args = tuple(self.mask_value(arg) for arg in record.args)
            elif isinstance(record.args, list):
                record.args = [self.mask_value(arg) for arg in record.args]
        
        return True
    
    def mask_string_values(self, value: str) -> str:
        """
        Mask sensitive patterns in a string.
        
        Args:
            value: The string to process
            
        Returns:
            The string with sensitive patterns masked
        """
        if not isinstance(value, str):
            return value
        
        result = value
        for pattern in self.sensitive_patterns:
            # Find all matches
            matches = pattern.finditer(result)
            for match in matches:
                matched_text = match.group()
                masked_text = self._mask_string(matched_text)
                result = result.replace(matched_text, masked_text)
        
        return result


class LogMaskingService:
    """
    Service for managing log masking configuration.
    
    This service provides:
    - Configuration of sensitive fields and patterns
    - Easy setup of logging filters
    - Custom masking functions
    """
    
    def __init__(
        self,
        sensitive_fields: Optional[Set[str]] = None,
        sensitive_patterns: Optional[List[Pattern[str]]] = None,
        mask_char: str = "*",
        show_last: int = 4,
    ):
        """
        Initialize the LogMaskingService.
        
        Args:
            sensitive_fields: Additional field names to mask
            sensitive_patterns: Additional regex patterns to detect sensitive data
            mask_char: Character to use for masking
            show_last: Number of characters to show at the end
        """
        self.sensitive_fields = DEFAULT_SENSITIVE_FIELDS.union(sensitive_fields or set())
        self.sensitive_patterns = DEFAULT_SENSITIVE_PATTERNS + (sensitive_patterns or [])
        self.mask_char = mask_char
        self.show_last = show_last
    
    def create_filter(self) -> SensitiveDataFilter:
        """
        Create a SensitiveDataFilter with the current configuration.
        
        Returns:
            A configured SensitiveDataFilter
        """
        return SensitiveDataFilter(
            sensitive_fields=self.sensitive_fields,
            sensitive_patterns=self.sensitive_patterns,
            mask_char=self.mask_char,
            show_last=self.show_last,
        )
    
    def setup_logging(self, logger_name: str = None, level: int = None) -> None:
        """
        Set up logging with sensitive data masking.
        
        Args:
            logger_name: Name of the logger to configure (None for root logger)
            level: Logging level (optional)
        """
        logger_obj = logging.getLogger(logger_name)
        
        if level is not None:
            logger_obj.setLevel(level)
        
        # Add filter to all handlers
        filter_obj = self.create_filter()
        for handler in logger_obj.handlers:
            handler.addFilter(filter_obj)
        
        # Also add to the logger itself
        logger_obj.addFilter(filter_obj)
        
        logger.info(f"Configured log masking for logger: {logger_name or 'root'}")
    
    def add_sensitive_field(self, field: str) -> None:
        """Add a field to the sensitive fields list."""
        self.sensitive_fields.add(field.lower())
    
    def add_sensitive_fields(self, fields: List[str]) -> None:
        """Add multiple fields to the sensitive fields list."""
        for field in fields:
            self.sensitive_fields.add(field.lower())
    
    def add_sensitive_pattern(self, pattern: Union[str, Pattern[str]]) -> None:
        """Add a regex pattern to the sensitive patterns list."""
        if isinstance(pattern, str):
            self.sensitive_patterns.append(re.compile(pattern, re.IGNORECASE))
        else:
            self.sensitive_patterns.append(pattern)
    
    def mask_data(self, data: Any) -> Any:
        """
        Mask sensitive data in any data structure.
        
        Args:
            data: The data to mask
            
        Returns:
            The data with sensitive information masked
        """
        filter_obj = self.create_filter()
        return filter_obj.mask_value(data)
    
    def mask_string(self, value: str) -> str:
        """Mask sensitive patterns in a string."""
        filter_obj = self.create_filter()
        return filter_obj.mask_string_values(value)


# Convenience function to create a filter with custom settings
def create_sensitive_data_filter(
    sensitive_fields: Optional[Set[str]] = None,
    sensitive_patterns: Optional[List[Pattern[str]]] = None,
    mask_char: str = "*",
    show_last: int = 4,
) -> SensitiveDataFilter:
    """
    Create a SensitiveDataFilter with custom settings.
    
    Args:
        sensitive_fields: Set of field names to mask
        sensitive_patterns: List of regex patterns to detect sensitive data
        mask_char: Character to use for masking
        show_last: Number of characters to show at the end
        
    Returns:
        A configured SensitiveDataFilter
    """
    return SensitiveDataFilter(
        sensitive_fields=sensitive_fields,
        sensitive_patterns=sensitive_patterns,
        mask_char=mask_char,
        show_last=show_last,
    )


# Convenience function to set up log masking for a logger
def setup_log_masking(
    logger_name: str = None,
    sensitive_fields: Optional[Set[str]] = None,
    sensitive_patterns: Optional[List[Pattern[str]]] = None,
    mask_char: str = "*",
    show_last: int = 4,
    level: int = None,
) -> SensitiveDataFilter:
    """
    Set up log masking for a logger.
    
    Args:
        logger_name: Name of the logger to configure (None for root logger)
        sensitive_fields: Additional field names to mask
        sensitive_patterns: Additional regex patterns
        mask_char: Character to use for masking
        show_last: Number of characters to show at the end
        level: Logging level
        
    Returns:
        The created filter
    """
    service = LogMaskingService(
        sensitive_fields=sensitive_fields,
        sensitive_patterns=sensitive_patterns,
        mask_char=mask_char,
        show_last=show_last,
    )
    service.setup_logging(logger_name, level)
    return service.create_filter()
