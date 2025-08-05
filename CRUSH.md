# Vulnhuntr Development Guide

## Build/Test Commands
```bash
poetry install              # Install dependencies
poetry run vulnhuntr -h    # Run CLI help
poetry run python -m vulnhuntr -r /path/to/repo  # Run vulnerability scan
poetry shell               # Activate virtual environment
poetry build               # Build distribution packages
```

## Code Style Guidelines
- **Python version**: Strictly Python 3.10 (due to Jedi parser requirements)
- **Package manager**: Poetry for dependency management
- **Imports**: Standard library → third-party → local, separated by blank lines
- **Type hints**: Required for all function signatures using `typing` module
- **Naming**: PascalCase for classes, snake_case for functions/variables, UPPER_SNAKE_CASE for constants
- **Line length**: ~120 characters max
- **Docstrings**: Triple quotes for classes and complex functions

## Error Handling
- Custom exception hierarchy with base `LLMError` class
- Always re-raise with context using `raise NewError() from e`
- Log warnings/errors before raising exceptions
- Handle API-specific errors (rate limits, connection errors)

## Project Structure
- `vulnhuntr/` - Main package directory
- `LLMs.py` - LLM client implementations (Claude, GPT, Ollama)
- `symbol_finder.py` - Code analysis and symbol extraction
- `prompts.py` - Vulnerability detection prompt templates
- Use Pydantic for data validation and structured responses