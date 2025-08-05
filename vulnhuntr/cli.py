"""
Simple CLI wrapper for vulnhuntr enhanced features.
Provides easy access to rate limiting and state recovery.
"""

import sys
import os
from pathlib import Path

# Add vulnhuntr to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from enhanced_main import run_enhanced
from simple_config import get_config, print_env_help


def main():
    """Main CLI entry point"""
    
    # Check if user wants help
    if len(sys.argv) > 1 and sys.argv[1] in ['--help', '-h', 'help']:
        print_help()
        return
    
    # Check if user wants config help
    if len(sys.argv) > 1 and sys.argv[1] in ['--config-help', 'config-help']:
        print_env_help()
        return
    
    # Check if user wants to see current config
    if len(sys.argv) > 1 and sys.argv[1] in ['--show-config', 'show-config']:
        config = get_config()
        config.print_config()
        return
    
    # Run enhanced vulnhuntr
    try:
        run_enhanced()
    except KeyboardInterrupt:
        print("\nInterrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


def print_help():
    """Print help information"""
    help_text = """
Vulnhuntr Enhanced - Vulnerability Scanner with Rate Limiting and State Recovery

USAGE:
    python -m vulnhuntr.cli [OPTIONS]

BASIC OPTIONS:
    -r, --root PATH          Path to repository root (required)
    -a, --analyze PATH       Specific path or file to analyze
    -l, --llm PROVIDER       LLM provider: claude, gpt, openrouter, ollama (default: claude)
    -v, --verbosity          Increase verbosity (-v for INFO, -vv for DEBUG)

ENHANCED OPTIONS:
    --resume SESSION_ID      Resume analysis from session ID
    --list-sessions          List resumable analysis sessions
    --stats                  Show analysis statistics
    --no-enhanced            Disable enhanced features

UTILITY OPTIONS:
    --config-help            Show environment variable configuration help
    --show-config            Show current configuration
    -h, --help               Show this help message

EXAMPLES:
    # Basic analysis
    python -m vulnhuntr.cli -r /path/to/repo -l claude

    # Resume interrupted analysis
    python -m vulnhuntr.cli --resume abc12345

    # List available sessions
    python -m vulnhuntr.cli --list-sessions

    # Show statistics
    python -m vulnhuntr.cli --stats

    # Analyze specific file with verbose output
    python -m vulnhuntr.cli -r /path/to/repo -a src/app.py -v

CONFIGURATION:
    Enhanced features can be configured via environment variables.
    Use --config-help to see all available options.

    Common settings:
        export CLAUDE_RATE_LIMIT=30          # Reduce Claude rate limit
        export VULNHUNTR_DEBUG=true          # Enable debug mode
        export VULNHUNTR_STATE_FILE=my_state.json  # Custom state file

RATE LIMITING:
    The enhanced version automatically rate limits requests to prevent
    hitting API limits. Default rates:
        - Claude: 50 requests/minute
        - OpenAI: 60 requests/minute
        - OpenRouter: 30 requests/minute
        - Ollama: 100 requests/minute

STATE RECOVERY:
    Analysis sessions are automatically saved and can be resumed if
    interrupted. Use --list-sessions to see available sessions and
    --resume SESSION_ID to continue from where you left off.

For more information, visit: https://github.com/protectai/vulnhuntr
"""
    print(help_text)


if __name__ == '__main__':
    main()