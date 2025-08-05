"""
Enhanced LLM base class with rate limiting and retry logic.
Extends the existing LLM class with resilience features.
"""

import time
import os
from typing import Optional, Any
from vulnhuntr.LLMs import LLM, RateLimitError, APIConnectionError, APIStatusError
from vulnhuntr.simple_rate_limiter import get_rate_limiter


class EnhancedLLM(LLM):
    """Enhanced LLM with simple rate limiting and retry logic"""
    
    def __init__(self, system_prompt: str = "", provider_name: str = ""):
        super().__init__(system_prompt)
        self.provider_name = provider_name.lower()
        self.rate_limiter = get_rate_limiter(self.provider_name)
        self.max_retries = int(os.getenv('VULNHUNTR_MAX_RETRIES', '3'))
        self.base_delay = float(os.getenv('VULNHUNTR_BASE_DELAY', '1.0'))
        self.max_delay = float(os.getenv('VULNHUNTR_MAX_DELAY', '60.0'))
    
    def chat_with_rate_limiting(self, user_prompt: str, response_model=None, max_tokens: int = 4096):
        """Chat with rate limiting and simple retry logic"""
        
        for attempt in range(self.max_retries):
            try:
                # Check rate limiter first
                if self.rate_limiter and not self.rate_limiter.can_proceed():
                    wait_time = self.rate_limiter.wait_time()
                    if wait_time > 0:
                        print(f"Rate limited ({self.provider_name}), waiting {wait_time:.1f} seconds...")
                        time.sleep(wait_time)
                        # Try rate limiter again after waiting
                        if not self.rate_limiter.can_proceed():
                            # If still rate limited, treat as rate limit error
                            raise RateLimitError("Rate limit still active after waiting")
                
                # Use original chat method
                return self.chat(user_prompt, response_model, max_tokens)
                
            except RateLimitError as e:
                if attempt < self.max_retries - 1:
                    # Exponential backoff for rate limits: 2s, 4s, 8s
                    delay = min(self.base_delay * (2 ** (attempt + 1)), self.max_delay)
                    print(f"Rate limit hit ({self.provider_name}), retrying in {delay} seconds... (attempt {attempt + 1}/{self.max_retries})")
                    time.sleep(delay)
                else:
                    print(f"Rate limit exceeded after {self.max_retries} attempts")
                    raise
                    
            except (APIConnectionError, APIStatusError) as e:
                if attempt < self.max_retries - 1:
                    # Linear backoff for connection/API errors: 1.5s, 3s, 4.5s
                    delay = min(self.base_delay * (1.5 ** (attempt + 1)), self.max_delay)
                    print(f"API error ({self.provider_name}): {str(e)}, retrying in {delay:.1f} seconds... (attempt {attempt + 1}/{self.max_retries})")
                    time.sleep(delay)
                else:
                    print(f"API error persisted after {self.max_retries} attempts")
                    raise
                    
            except Exception as e:
                # For other errors, only retry once with short delay
                if attempt == 0:
                    delay = self.base_delay
                    print(f"Unexpected error ({self.provider_name}): {str(e)}, retrying in {delay} seconds...")
                    time.sleep(delay)
                else:
                    print(f"Unexpected error persisted: {str(e)}")
                    raise
    
    def get_rate_limiter_status(self) -> Optional[dict]:
        """Get current rate limiter status"""
        if self.rate_limiter:
            return self.rate_limiter.get_status()
        return None
    
    def reset_rate_limiter(self):
        """Reset rate limiter (useful for testing)"""
        if self.rate_limiter:
            self.rate_limiter.tokens = float(self.rate_limiter.requests_per_minute)
            self.rate_limiter.last_refill = time.time()


class EnhancedClaude(EnhancedLLM):
    """Enhanced Claude with rate limiting - placeholder for integration"""
    
    def __init__(self, model: str, base_url: str, system_prompt: str = ""):
        super().__init__(system_prompt, "claude")
        self.model = model
        self.base_url = base_url
        # Note: Actual Claude client initialization will be done in integration phase


class EnhancedChatGPT(EnhancedLLM):
    """Enhanced ChatGPT with rate limiting - placeholder for integration"""
    
    def __init__(self, model: str, base_url: str, system_prompt: str = ""):
        super().__init__(system_prompt, "openai")
        self.model = model
        self.base_url = base_url
        # Note: Actual OpenAI client initialization will be done in integration phase


class EnhancedOpenRouter(EnhancedLLM):
    """Enhanced OpenRouter with rate limiting - placeholder for integration"""
    
    def __init__(self, model: str, base_url: str, system_prompt: str = ""):
        super().__init__(system_prompt, "openrouter")
        self.model = model
        self.base_url = base_url
        # Note: Actual OpenRouter client initialization will be done in integration phase


class EnhancedOllama(EnhancedLLM):
    """Enhanced Ollama with rate limiting - placeholder for integration"""
    
    def __init__(self, model: str, base_url: str, system_prompt: str = ""):
        super().__init__(system_prompt, "ollama")
        self.model = model
        self.base_url = base_url
        # Note: Actual Ollama client initialization will be done in integration phase


def create_enhanced_llm(provider: str, model: str, base_url: str, system_prompt: str = "") -> EnhancedLLM:
    """Factory function to create enhanced LLM instances"""
    provider = provider.lower()
    
    if provider == 'claude':
        return EnhancedClaude(model, base_url, system_prompt)
    elif provider in ['openai', 'gpt']:
        return EnhancedChatGPT(model, base_url, system_prompt)
    elif provider == 'openrouter':
        return EnhancedOpenRouter(model, base_url, system_prompt)
    elif provider == 'ollama':
        return EnhancedOllama(model, base_url, system_prompt)
    else:
        raise ValueError(f"Unsupported provider: {provider}")