"""Configuration management for CUSD Email Summarizer."""
import json
import os
from pathlib import Path
from typing import Dict, Any


class Config:
    """Configuration manager for the application."""
    
    def __init__(self, config_path: str = None):
        """Initialize configuration.
        
        Args:
            config_path: Path to config.json file. If None, uses default location.
        """
        if config_path is None:
            # Default to config/config.json relative to project root
            project_root = Path(__file__).parent.parent
            config_path = project_root / "config" / "config.json"
        
        self.config_path = Path(config_path)
        self.config = self._load_config()
        self._validate_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from JSON file."""
        if not self.config_path.exists():
            raise FileNotFoundError(f"Config file not found: {self.config_path}")
        
        with open(self.config_path, 'r') as f:
            return json.load(f)
    
    def _validate_config(self):
        """Validate required configuration keys."""
        required_sections = ['gmail', 'ai', 'output', 'tracking', 'logging']
        for section in required_sections:
            if section not in self.config:
                raise ValueError(f"Missing required config section: {section}")
    
    def get(self, *keys) -> Any:
        """Get configuration value by nested keys.
        
        Args:
            *keys: Nested keys to access configuration values.
            
        Example:
            config.get('gmail', 'label')  # Returns 'CUSD'
        """
        value = self.config
        for key in keys:
            if isinstance(value, dict):
                value = value.get(key)
            else:
                return None
        return value
    
    def get_ai_api_key(self) -> str:
        """Get AI API key from environment variable.
        
        Returns:
            API key string.
            
        Raises:
            ValueError: If API key environment variable is not set.
        """
        env_var = self.get('ai', 'env_var_name')
        api_key = os.getenv(env_var)
        
        if not api_key:
            raise ValueError(
                f"Environment variable '{env_var}' not set. "
                f"Please set your API key using: "
                f"export {env_var}='your-key-here' (Linux/Mac) or "
                f"$env:{env_var}='your-key-here' (PowerShell)"
            )
        
        return api_key
    
    def get_project_root(self) -> Path:
        """Get project root directory."""
        return Path(__file__).parent.parent
    
    def resolve_path(self, relative_path: str) -> Path:
        """Resolve relative path from project root.
        
        Args:
            relative_path: Path relative to project root.
            
        Returns:
            Absolute Path object.
        """
        if relative_path.startswith('./'):
            relative_path = relative_path[2:]
        
        return self.get_project_root() / relative_path


# Global config instance
_config = None


def get_config(config_path: str = None) -> Config:
    """Get or create global configuration instance.
    
    Args:
        config_path: Optional path to config file.
        
    Returns:
        Config instance.
    """
    global _config
    if _config is None:
        _config = Config(config_path)
    return _config
