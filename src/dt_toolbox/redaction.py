"""PII redaction utilities."""
import re
from typing import List

from .types import RedactionConfig


class Redactor:
    """Handles PII redaction in log messages."""
    
    def __init__(self, config: RedactionConfig):
        """Initialize redactor.
        
        Args:
            config: Redaction configuration.
        """
        self.config = config
        self.patterns = [re.compile(pattern, re.IGNORECASE) for pattern in config.patterns]
    
    def redact(self, text: str) -> str:
        """Redact sensitive information from text.
        
        Args:
            text: Text to redact.
            
        Returns:
            Redacted text.
        """
        if not self.config.enabled:
            return text
        
        result = text
        for pattern in self.patterns:
            result = pattern.sub(self.config.replacement, result)
        
        return result
    
    def redact_dict(self, data: dict) -> dict:
        """Redact sensitive information from dictionary values.
        
        Args:
            data: Dictionary to redact.
            
        Returns:
            Dictionary with redacted values.
        """
        if not self.config.enabled:
            return data
        
        result = {}
        for key, value in data.items():
            if isinstance(value, str):
                result[key] = self.redact(value)
            elif isinstance(value, dict):
                result[key] = self.redact_dict(value)
            elif isinstance(value, list):
                result[key] = [
                    self.redact(item) if isinstance(item, str)
                    else self.redact_dict(item) if isinstance(item, dict)
                    else item
                    for item in value
                ]
            else:
                result[key] = value
        
        return result
