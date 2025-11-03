"""Configuration management for CUSD Email Summarizer."""
import json
import os
from pathlib import Path
from typing import Dict, Any, Optional


class Config:
    """Configuration manager for the application with profile support."""

    def __init__(self, config_path: str = None, profile: str = None):
        """Initialize configuration.

        Args:
            config_path: Path to config.json file. If None, uses default location.
            profile: Profile name (e.g., 'cusd', 'hoa'). If None, uses default from config.
        """
        if config_path is None:
            # Default to config/config.json relative to project root
            project_root = Path(__file__).parent.parent
            config_path = project_root / "config" / "config.json"

        self.config_path = Path(config_path)
        self.base_config = self._load_config()

        # Determine active profile
        self.profile_name = profile or self.base_config.get('default_profile', 'cusd')

        # Load profile-specific configuration
        self.profile_config = self._load_profile_config(self.profile_name)

        # Merge configurations (profile overrides base)
        self.config = self._merge_configs(self.base_config, self.profile_config)

        self._validate_config()

    def _load_config(self) -> Dict[str, Any]:
        """Load base configuration from JSON file."""
        if not self.config_path.exists():
            raise FileNotFoundError(f"Config file not found: {self.config_path}")

        with open(self.config_path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def _load_profile_config(self, profile_name: str) -> Dict[str, Any]:
        """Load profile-specific configuration.

        Args:
            profile_name: Name of the profile (e.g., 'cusd', 'hoa').

        Returns:
            Profile configuration dictionary.
        """
        project_root = Path(__file__).parent.parent
        profile_path = project_root / "profiles" / f"{profile_name}.json"

        if not profile_path.exists():
            raise FileNotFoundError(
                f"Profile configuration not found: {profile_path}\n"
                f"Available profiles should be in the 'profiles/' directory."
            )

        with open(profile_path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def _merge_configs(self, base: Dict[str, Any], profile: Dict[str, Any]) -> Dict[str, Any]:
        """Merge base and profile configurations.

        Profile settings override base settings. Nested dictionaries are merged recursively.

        Args:
            base: Base configuration dictionary.
            profile: Profile-specific configuration dictionary.

        Returns:
            Merged configuration dictionary.
        """
        merged = base.copy()

        for key, value in profile.items():
            if key in merged and isinstance(merged[key], dict) and isinstance(value, dict):
                # Recursively merge nested dictionaries
                merged[key] = self._merge_configs(merged[key], value)
            else:
                # Override with profile value
                merged[key] = value

        return merged

    def _validate_config(self):
        """Validate required configuration keys."""
        # Base config validation
        required_sections = ['ai']
        for section in required_sections:
            if section not in self.config:
                raise ValueError(f"Missing required config section: {section}")

        # Profile-specific validation
        if 'prompts' not in self.config:
            raise ValueError(f"Profile '{self.profile_name}' missing 'prompts' section")
    
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


def get_config(config_path: str = None, profile: str = None) -> Config:
    """Get or create global configuration instance.

    Args:
        config_path: Optional path to config file.
        profile: Optional profile name to use.

    Returns:
        Config instance.
    """
    global _config
    if _config is None:
        _config = Config(config_path, profile)
    return _config


def reset_config():
    """Reset the global config instance (useful for switching profiles)."""
    global _config
    _config = None
