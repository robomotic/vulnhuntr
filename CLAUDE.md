# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Vulnhuntr is an AI-powered vulnerability detection tool that leverages Large Language Models (LLMs) to identify remotely exploitable vulnerabilities in Python codebases through static code analysis. The tool is designed for security researchers and has discovered multiple 0-day vulnerabilities in popular open-source projects.

**Key vulnerability types detected:**
- Local File Inclusion (LFI)
- Remote Code Execution (RCE) 
- Server-Side Request Forgery (SSRF)
- Arbitrary File Overwrite (AFO)
- SQL Injection (SQLI)
- Cross-Site Scripting (XSS)
- Insecure Direct Object References (IDOR)

## Development Commands

### Installation and Setup
```bash
# Install with poetry (recommended for development)
poetry install

# Install with pipx (for usage)
pipx install git+https://github.com/protectai/vulnhuntr.git --python python3.10

# Docker build
docker build -t vulnhuntr https://github.com/protectai/vulnhuntr.git#main
```

### Running the Tool
```bash
# Basic usage with Claude (requires ANTHROPIC_API_KEY)
vulnhuntr -r /path/to/repo

# Analyze specific file with GPT-4 (requires OPENAI_API_KEY)
vulnhuntr -r /path/to/repo -a server.py -l gpt

# With verbosity for debugging
vulnhuntr -r /path/to/repo -v
vulnhuntr -r /path/to/repo -vv  # Debug level
```

### Environment Variables
- `ANTHROPIC_API_KEY` - Required for Claude LLM
- `OPENAI_API_KEY` - Required for GPT LLM
- `ANTHROPIC_MODEL` - Default: "claude-3-5-sonnet-latest"
- `OPENAI_MODEL` - Default: "chatgpt-4o-latest"
- `ANTHROPIC_BASE_URL` - Default: "https://api.anthropic.com"
- `OPENAI_BASE_URL` - Default: "https://api.openai.com/v1"
- `OLLAMA_BASE_URL` - For Ollama usage (experimental)
- `OLLAMA_MODEL` - Default: "llama3"

## Code Architecture

### Core Components

1. **vulnhuntr/__main__.py** - Main entry point and orchestration logic
   - `RepoOps` class: Repository analysis and file filtering
   - `run()` function: CLI interface and main analysis workflow
   - Network-related file detection using regex patterns

2. **vulnhuntr/LLMs.py** - LLM client implementations
   - `Claude` class: Anthropic Claude integration with structured prompting
   - `ChatGPT` class: OpenAI GPT integration
   - `Ollama` class: Local model support (experimental)
   - Base `LLM` class with common functionality

3. **vulnhuntr/symbol_finder.py** - Code analysis and context extraction
   - `SymbolExtractor` class: Uses Jedi for Python code parsing
   - Extracts function/class definitions for LLM context
   - Handles complex symbol resolution (imports, instances, etc.)

4. **vulnhuntr/prompts.py** - LLM prompt templates
   - Vulnerability-specific analysis prompts for each vuln type
   - System prompts and analysis guidelines
   - Bypass technique examples for each vulnerability class

### Analysis Workflow

1. **Repository Scanning**: Identifies Python files with network-related patterns
2. **README Summarization**: Extracts project context for better analysis
3. **Initial Analysis**: Broad vulnerability scanning of target files
4. **Secondary Analysis**: Vulnerability-specific deep dives with context gathering
5. **Iterative Context Gathering**: Requests additional code context up to 7 iterations
6. **Report Generation**: Structured JSON output with confidence scores and PoCs

### Key Design Patterns

- **Structured Prompting**: Uses XML tags and Pydantic models for reliable LLM responses
- **Context-Aware Analysis**: Iteratively gathers code context based on LLM requests
- **Multi-Model Support**: Abstracted LLM interface supports multiple providers
- **Network Pattern Detection**: Regex-based identification of web frameworks and entry points

## Important Notes

- **Python Version Requirement**: Strictly requires Python 3.10 due to Jedi parser dependencies
- **Cost Monitoring**: Tool can generate high LLM costs - monitor usage and set spending limits
- **Security Focus**: Only analyzes remotely exploitable vulnerabilities, not local issues
- **Logging**: Comprehensive logging to `vulnhuntr.log` for debugging and analysis tracking

## File Exclusions

The tool automatically excludes:
- Test files (`/test`, `_test/`, files with `test_` prefix)
- Documentation (`/docs`, `/example`)
- Build artifacts (`/dist`, `.venv`, `virtualenv`)
- Configuration files (`/setup.py`)