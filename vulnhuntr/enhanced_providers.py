"""
Enhanced provider classes that integrate rate limiting and retry logic
with the existing vulnhuntr LLM providers.
"""

import os
import time
from vulnhuntr.LLMs import Claude as OriginalClaude, ChatGPT as OriginalChatGPT
from vulnhuntr.LLMs import OpenRouter as OriginalOpenRouter, Ollama as OriginalOllama
from vulnhuntr.enhanced_llm import EnhancedLLM


class Claude(EnhancedLLM, OriginalClaude):
    """Enhanced Claude provider with rate limiting and retry logic"""
    
    def __init__(self, model: str, base_url: str, system_prompt: str = ""):
        # Initialize both parent classes
        OriginalClaude.__init__(self, model, base_url, system_prompt)
        EnhancedLLM.__init__(self, system_prompt, "claude")
    
    def chat(self, user_prompt: str, response_model=None, max_tokens: int = 4096):
        """Override chat to use enhanced version with rate limiting"""
        return self.chat_with_rate_limiting(user_prompt, response_model, max_tokens)
    
    def chat_original(self, user_prompt: str, response_model=None, max_tokens: int = 4096):
        """Access to original chat method without enhancements"""
        return OriginalClaude.chat(self, user_prompt, response_model, max_tokens)


class ChatGPT(EnhancedLLM, OriginalChatGPT):
    """Enhanced ChatGPT provider with rate limiting and retry logic"""
    
    def __init__(self, model: str, base_url: str, system_prompt: str = ""):
        OriginalChatGPT.__init__(self, model, base_url, system_prompt)
        EnhancedLLM.__init__(self, system_prompt, "openai")
    
    def chat(self, user_prompt: str, response_model=None, max_tokens: int = 4096):
        """Override chat to use enhanced version with rate limiting"""
        return self.chat_with_rate_limiting(user_prompt, response_model, max_tokens)
    
    def chat_original(self, user_prompt: str, response_model=None, max_tokens: int = 4096):
        """Access to original chat method without enhancements"""
        return OriginalChatGPT.chat(self, user_prompt, response_model, max_tokens)


class OpenRouter(EnhancedLLM, OriginalOpenRouter):
    """Enhanced OpenRouter provider with rate limiting and retry logic"""
    
    def __init__(self, model: str, base_url: str, system_prompt: str = ""):
        OriginalOpenRouter.__init__(self, model, base_url, system_prompt)
        EnhancedLLM.__init__(self, system_prompt, "openrouter")
    
    def chat(self, user_prompt: str, response_model=None, max_tokens: int = 4096):
        """Override chat to use enhanced version with rate limiting"""
        return self.chat_with_rate_limiting(user_prompt, response_model, max_tokens)
    
    def chat_original(self, user_prompt: str, response_model=None, max_tokens: int = 4096):
        """Access to original chat method without enhancements"""
        return OriginalOpenRouter.chat(self, user_prompt, response_model, max_tokens)


class Ollama(EnhancedLLM, OriginalOllama):
    """Enhanced Ollama provider with rate limiting and retry logic"""
    
    def __init__(self, model: str, base_url: str, system_prompt: str = ""):
        OriginalOllama.__init__(self, model, base_url, system_prompt)
        EnhancedLLM.__init__(self, system_prompt, "ollama")
    
    def chat(self, user_prompt: str, response_model=None, max_tokens: int = 4096):
        """Override chat to use enhanced version with rate limiting"""
        return self.chat_with_rate_limiting(user_prompt, response_model, max_tokens)
    
    def chat_original(self, user_prompt: str, response_model=None, max_tokens: int = 4096):
        """Access to original chat method without enhancements"""
        return OriginalOllama.chat(self, user_prompt, response_model, max_tokens)


def initialize_llm_enhanced(llm_arg: str, system_prompt: str = ""):
    """
    Enhanced LLM initialization that uses enhanced providers.
    Drop-in replacement for the original initialize_llm function.
    """
    llm_arg = llm_arg.lower()
    
    if llm_arg == 'claude':
        anth_model = os.getenv("ANTHROPIC_MODEL", "claude-3-5-sonnet-latest")
        anth_base_url = os.getenv("ANTHROPIC_BASE_URL", "https://api.anthropic.com")
        return Claude(anth_model, anth_base_url, system_prompt)
    
    elif llm_arg == 'gpt':
        openai_model = os.getenv("OPENAI_MODEL", "chatgpt-4o-latest")
        openai_base_url = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
        return ChatGPT(openai_model, openai_base_url, system_prompt)
    
    elif llm_arg == 'openrouter':
        openrouter_model = os.getenv("OPENROUTER_MODEL", "anthropic/claude-3.5-sonnet")
        openrouter_base_url = os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")
        return OpenRouter(openrouter_model, openrouter_base_url, system_prompt)
    
    elif llm_arg == 'ollama':
        ollama_model = os.getenv("OLLAMA_MODEL", "llama3")
        ollama_base_url = os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434/api/generate")
        return Ollama(ollama_model, ollama_base_url, system_prompt)
    
    else:
        raise ValueError(f"Invalid LLM argument: {llm_arg}\nValid options are: claude, gpt, openrouter, ollama")


def get_provider_status(llm):
    """Get status information for an enhanced provider"""
    if hasattr(llm, 'get_rate_limiter_status'):
        rate_status = llm.get_rate_limiter_status()
        return {
            'provider': llm.provider_name,
            'rate_limiter': rate_status,
            'enhanced': True
        }
    else:
        return {
            'provider': getattr(llm, 'provider_name', 'unknown'),
            'enhanced': False
        }


def print_provider_status(llm):
    """Print status information for a provider"""
    status = get_provider_status(llm)
    print(f"Provider: {status['provider']}")
    print(f"Enhanced: {status['enhanced']}")
    
    if status['enhanced'] and status['rate_limiter']:
        rl = status['rate_limiter']
        print(f"Rate Limiter:")
        print(f"  Tokens available: {rl['tokens']:.2f}")
        print(f"  Rate limit: {rl['requests_per_minute']}/min")
        print(f"  Last refill: {time.ctime(rl['last_refill'])}")