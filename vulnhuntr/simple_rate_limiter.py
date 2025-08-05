"""
Simple rate limiter implementation for vulnhuntr LLM providers.
Uses token bucket algorithm with configurable rates per provider.
"""

import time
import threading
import os
from typing import Dict, Optional


class SimpleRateLimiter:
    """Simple token bucket rate limiter for LLM providers"""
    
    def __init__(self, requests_per_minute: int = 50):
        self.requests_per_minute = requests_per_minute
        self.tokens = float(requests_per_minute)
        self.last_refill = time.time()
        self.lock = threading.Lock()
    
    def can_proceed(self) -> bool:
        """Check if request can proceed, refill tokens if needed"""
        with self.lock:
            now = time.time()
            elapsed = now - self.last_refill
            
            # Refill tokens based on elapsed time
            tokens_to_add = elapsed * (self.requests_per_minute / 60.0)
            self.tokens = min(self.requests_per_minute, self.tokens + tokens_to_add)
            self.last_refill = now
            
            if self.tokens >= 1:
                self.tokens -= 1
                return True
            return False
    
    def wait_time(self) -> float:
        """Get seconds to wait before next request"""
        with self.lock:
            if self.tokens >= 1:
                return 0
            return (1 - self.tokens) / (self.requests_per_minute / 60.0)
    
    def get_status(self) -> Dict[str, float]:
        """Get current rate limiter status"""
        with self.lock:
            return {
                'tokens': self.tokens,
                'requests_per_minute': self.requests_per_minute,
                'last_refill': self.last_refill
            }


# Provider-specific rate limiters with configurable limits
def create_rate_limiters() -> Dict[str, SimpleRateLimiter]:
    """Create rate limiters for each provider with configurable limits"""
    return {
        'claude': SimpleRateLimiter(int(os.getenv('CLAUDE_RATE_LIMIT', '50'))),
        'openai': SimpleRateLimiter(int(os.getenv('OPENAI_RATE_LIMIT', '60'))),
        'gpt': SimpleRateLimiter(int(os.getenv('OPENAI_RATE_LIMIT', '60'))),  # Alias for openai
        'openrouter': SimpleRateLimiter(int(os.getenv('OPENROUTER_RATE_LIMIT', '30'))),
        'ollama': SimpleRateLimiter(int(os.getenv('OLLAMA_RATE_LIMIT', '100')))
    }


# Global rate limiters instance
RATE_LIMITERS = create_rate_limiters()


def get_rate_limiter(provider_name: str) -> Optional[SimpleRateLimiter]:
    """Get rate limiter for specific provider"""
    return RATE_LIMITERS.get(provider_name.lower())


def reset_rate_limiters():
    """Reset all rate limiters (useful for testing)"""
    global RATE_LIMITERS
    RATE_LIMITERS = create_rate_limiters()