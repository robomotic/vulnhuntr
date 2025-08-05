"""
Simple configuration management for vulnhuntr enhanced features.
Uses environment variables for easy configuration.
"""

import os
from typing import Dict, Any


class SimpleConfig:
    """Simple configuration manager using environment variables"""
    
    def __init__(self):
        self._load_config()
    
    def _load_config(self):
        """Load configuration from environment variables"""
        # Rate limiting configuration
        self.rate_limits = {
            'claude': int(os.getenv('CLAUDE_RATE_LIMIT', '50')),
            'openai': int(os.getenv('OPENAI_RATE_LIMIT', '60')),
            'gpt': int(os.getenv('OPENAI_RATE_LIMIT', '60')),  # Alias for openai
            'openrouter': int(os.getenv('OPENROUTER_RATE_LIMIT', '30')),
            'ollama': int(os.getenv('OLLAMA_RATE_LIMIT', '100'))
        }
        
        # Retry configuration
        self.max_retries = int(os.getenv('VULNHUNTR_MAX_RETRIES', '3'))
        self.base_delay = float(os.getenv('VULNHUNTR_BASE_DELAY', '1.0'))
        self.max_delay = float(os.getenv('VULNHUNTR_MAX_DELAY', '60.0'))
        
        # State management configuration
        self.state_file = os.getenv('VULNHUNTR_STATE_FILE', 'vulnhuntr_state.json')
        self.cleanup_days = int(os.getenv('VULNHUNTR_CLEANUP_DAYS', '30'))
        
        # Debug and logging
        self.debug_mode = os.getenv('VULNHUNTR_DEBUG', 'false').lower() == 'true'
        self.verbose_rate_limiting = os.getenv('VULNHUNTR_VERBOSE_RATE_LIMITING', 'false').lower() == 'true'
        
        # Performance settings
        self.enable_caching = os.getenv('VULNHUNTR_ENABLE_CACHING', 'true').lower() == 'true'
        self.cache_ttl_hours = int(os.getenv('VULNHUNTR_CACHE_TTL_HOURS', '24'))
    
    def get_rate_limit(self, provider: str) -> int:
        """Get rate limit for specific provider"""
        return self.rate_limits.get(provider.lower(), 50)
    
    def get_retry_config(self) -> Dict[str, Any]:
        """Get retry configuration"""
        return {
            'max_retries': self.max_retries,
            'base_delay': self.base_delay,
            'max_delay': self.max_delay
        }
    
    def get_state_config(self) -> Dict[str, Any]:
        """Get state management configuration"""
        return {
            'state_file': self.state_file,
            'cleanup_days': self.cleanup_days,
            'enable_caching': self.enable_caching,
            'cache_ttl_hours': self.cache_ttl_hours
        }
    
    def is_debug_mode(self) -> bool:
        """Check if debug mode is enabled"""
        return self.debug_mode
    
    def is_verbose_rate_limiting(self) -> bool:
        """Check if verbose rate limiting is enabled"""
        return self.verbose_rate_limiting
    
    def to_dict(self) -> Dict[str, Any]:
        """Get all configuration as dictionary"""
        return {
            'rate_limits': self.rate_limits,
            'retry_config': self.get_retry_config(),
            'state_config': self.get_state_config(),
            'debug_mode': self.debug_mode,
            'verbose_rate_limiting': self.verbose_rate_limiting
        }
    
    def print_config(self):
        """Print current configuration"""
        print("Vulnhuntr Enhanced Configuration:")
        print(f"  Rate Limits:")
        for provider, limit in self.rate_limits.items():
            print(f"    {provider}: {limit} requests/minute")
        print(f"  Retry Config:")
        print(f"    Max retries: {self.max_retries}")
        print(f"    Base delay: {self.base_delay}s")
        print(f"    Max delay: {self.max_delay}s")
        print(f"  State Management:")
        print(f"    State file: {self.state_file}")
        print(f"    Cleanup after: {self.cleanup_days} days")
        print(f"    Caching enabled: {self.enable_caching}")
        print(f"  Debug mode: {self.debug_mode}")


# Global configuration instance
config = SimpleConfig()


def get_config() -> SimpleConfig:
    """Get global configuration instance"""
    return config


def reload_config():
    """Reload configuration from environment variables"""
    global config
    config = SimpleConfig()


# Environment variable documentation
ENV_VARS_HELP = """
Vulnhuntr Enhanced Environment Variables:

Rate Limiting:
  CLAUDE_RATE_LIMIT=50              # Claude requests per minute
  OPENAI_RATE_LIMIT=60              # OpenAI requests per minute  
  OPENROUTER_RATE_LIMIT=30          # OpenRouter requests per minute
  OLLAMA_RATE_LIMIT=100             # Ollama requests per minute

Retry Configuration:
  VULNHUNTR_MAX_RETRIES=3           # Maximum retry attempts
  VULNHUNTR_BASE_DELAY=1.0          # Base delay between retries (seconds)
  VULNHUNTR_MAX_DELAY=60.0          # Maximum delay between retries (seconds)

State Management:
  VULNHUNTR_STATE_FILE=vulnhuntr_state.json  # State file path
  VULNHUNTR_CLEANUP_DAYS=30         # Days to keep old session data
  VULNHUNTR_ENABLE_CACHING=true     # Enable result caching
  VULNHUNTR_CACHE_TTL_HOURS=24      # Cache time-to-live in hours

Debug and Logging:
  VULNHUNTR_DEBUG=false             # Enable debug mode
  VULNHUNTR_VERBOSE_RATE_LIMITING=false  # Verbose rate limiting logs

Example usage:
  export CLAUDE_RATE_LIMIT=30
  export VULNHUNTR_DEBUG=true
  python -m vulnhuntr.simple_main -r /path/to/repo
"""


def print_env_help():
    """Print environment variables help"""
    print(ENV_VARS_HELP)