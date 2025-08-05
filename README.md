<div align="center">

  <img width="250" src="https://github.com/user-attachments/assets/d1153ab4-df29-4955-ad49-1be7fad18bb3" alt="Vulnhuntr Logo">

A tool to identify remotely exploitable vulnerabilities using LLMs and static code analysis.

**World's first autonomous AI-discovered 0day vulnerabilities**

</div>

## Description
Vulnhuntr leverages the power of LLMs to automatically create and analyze entire code call chains starting from remote user input and ending at server output for detection of complex, multi-step, security-bypassing vulnerabilities that go far beyond what traditional static code analysis tools are capable of performing. See all the details including the Vulnhuntr output for all the 0-days here: [Protect AI Vulnhuntr Blog](https://protectai.com/threat-research/vulnhuntr-first-0-day-vulnerabilities)

## Vulnerabilities Found

> [!TIP]
> Found a vulnerability using Vulnhuntr? Submit a report to [huntr.com](https://huntr.com) to get $$ and submit a PR to add it to the list below!

> [!NOTE]
> This table is just a sample of the vulnerabilities found so far. We will unredact as responsible disclosure periods end.

| Repository | Stars | Vulnerabilities |
| - | - | - |
| [gpt_academic](https://github.com/binary-husky/gpt_academic) | 67k | [LFI](https://nvd.nist.gov/vuln/detail/CVE-2024-10100), [XSS](https://nvd.nist.gov/vuln/detail/CVE-2024-10101) |
| [ComfyUI](https://github.com/comfyanonymous/ComfyUI) | 66k | [XSS](https://nvd.nist.gov/vuln/detail/CVE-2024-10099) |
| [Langflow](https://github.com/langflow-ai/langflow) | 46k | RCE, IDOR |
| [FastChat](https://github.com/lm-sys/FastChat) | 37k | [SSRF](https://nvd.nist.gov/vuln/detail/CVE-2024-10044) | 
| [Ragflow](https://github.com/infiniflow/ragflow) | 31k | [RCE](https://nvd.nist.gov/vuln/detail/CVE-2024-10131) |
| [LLaVA](https://github.com/haotian-liu/LLaVA) | 21k | [SSRF](https://www.cve.org/CVERecord?id=CVE-2024-9309) |
| [gpt-researcher](https://github.com/assafelovic/gpt-researcher) | 17k | [AFO](https://github.com/assafelovic/gpt-researcher/pull/935) |
| [Letta](https://github.com/letta-ai/letta) | 14k | [AFO](https://github.com/letta-ai/letta/pull/2067) | 

## Limitations

- Only Python codebases are supported.
- Can only identify the following vulnerability classes:
  - Local file include (LFI)
  - Arbitrary file overwrite (AFO)
  - Remote code execution (RCE)
  - Cross site scripting (XSS)
  - SQL Injection (SQLI)
  - Server side request forgery (SSRF)
  - Insecure Direct Object Reference (IDOR)

## Installation

> [!IMPORTANT]
> Vulnhuntr strictly requires Python 3.10 because of a number of bugs in Jedi which it uses to parse Python code. It will not work reliably if installed with any other versions of Python.

We recommend using [pipx](https://github.com/pypa/pipx) or Docker to easily install and run Vulnhuntr.

Using Docker:
```bash
docker build -t vulnhuntr https://github.com/protectai/vulnhuntr.git#main
```

Using pipx:
```bash
pipx install git+https://github.com/protectai/vulnhuntr.git --python python3.10
```

Alternatively you can install directly from source using poetry:
```bash
git clone https://github.com/protectai/vulnhuntr
cd vulnhuntr && poetry install
```

## Usage

This tool is designed to analyze a GitHub repository for potential remotely exploitable vulnerabilities. The tool requires an API key and the local path to a GitHub repository. You may also optionally specify a custom endpoint for the LLM service.

> [!CAUTION]
> Always set spending limits or closely monitor costs with the LLM provider you use. This tool has the potential to rack up hefty bills as it tries to fit as much code in the LLMs context window as possible. 

> [!TIP]
> We recommend using Claude for the LLM. Through testing we have had better results with it over GPT.

### Command Line Interface

```
usage: vulnhuntr [-h] -r ROOT [-a ANALYZE] [-l {claude,gpt,openrouter,ollama}] [-v]

Analyze a GitHub project for vulnerabilities. Export your ANTHROPIC_API_KEY/OPENAI_API_KEY/OPENROUTER_API_KEY before running.

options:
  -h, --help            show this help message and exit
  -r ROOT, --root ROOT  Path to the root directory of the project
  -a ANALYZE, --analyze ANALYZE
                        Specific path or file within the project to analyze
  -l {claude,gpt,openrouter,ollama}, --llm {claude,gpt,openrouter,ollama}
                        LLM client to use (default: claude)
  -v, --verbosity       Increase output verbosity (-v for INFO, -vv for DEBUG)
```
### Examples
From a pipx install, analyze the entire repository using Claude:

```bash
export ANTHROPIC_API_KEY="sk-1234"
vulnhuntr -r /path/to/target/repo/
```

> [!TIP]
> We recommend giving Vulnhuntr specific files that handle remote user input and scan them individually.

From a pipx install, analyze the `/path/to/target/repo/server.py` file using GPT-4o. Can also specify a subdirectory instead of a file:

```bash
export OPENAI_API_KEY="sk-1234"
vulnhuntr -r /path/to/target/repo/ -a server.py -l gpt
```

From a pipx install, analyze a specific file using OpenRouter with Claude:

```bash
export OPENROUTER_API_KEY="sk-or-1234"
vulnhuntr -r /path/to/target/repo/ -a server.py -l openrouter
```

From a pipx install, analyze using OpenRouter with GPT-4o:

```bash
export OPENROUTER_API_KEY="sk-or-1234"
export OPENROUTER_MODEL="openai/gpt-4o"
vulnhuntr -r /path/to/target/repo/ -a server.py -l openrouter
```

From a docker installation, run using Claude and a custom endpoint to analyze /local/path/to/target/repo/repo-subfolder/target-file.py:

```bash
docker run --rm -e ANTHROPIC_API_KEY=sk-1234 -e ANTHROPIC_BASE_URL=https://localhost:1234/api -v /local/path/to/target/repo:/repo vulnhuntr:latest -r /repo -a repo-subfolder/target-file.py
```

From a docker installation, run using OpenRouter:

```bash
docker run --rm -e OPENROUTER_API_KEY=sk-or-1234 -e OPENROUTER_MODEL=anthropic/claude-3.5-sonnet -v /local/path/to/target/repo:/repo vulnhuntr:latest -r /repo -a repo-subfolder/target-file.py -l openrouter
```

### OpenRouter Configuration

OpenRouter provides access to multiple LLM providers through a unified API. Popular model options include:

**Claude Models (Recommended):**
- `anthropic/claude-3.5-sonnet` - Latest Claude 3.5 Sonnet (default)
- `anthropic/claude-3-opus` - Most capable Claude model
- `anthropic/claude-3-haiku` - Fastest and most cost-effective

**OpenAI Models:**
- `openai/gpt-4o` - Latest GPT-4 Omni model
- `openai/chatgpt-4o-latest` - Latest ChatGPT-4o
- `openai/gpt-4-turbo` - GPT-4 Turbo

**Environment Variables:**
```bash
export OPENROUTER_API_KEY="sk-or-your-key-here"
export OPENROUTER_MODEL="anthropic/claude-3.5-sonnet"  # Optional, defaults to Claude 3.5 Sonnet
export OPENROUTER_BASE_URL="https://openrouter.ai/api/v1"  # Optional, uses default endpoint
```

**Benefits of using OpenRouter:**
- Unified access to multiple providers
- Automatic fallback if primary provider is unavailable
- Cost optimization through competitive pricing
- No need to manage multiple API keys

*Experimental*

Ollama is included as an option, however we haven't had success with the open source models structuring their output correctly.

```bash
export OLLAMA_BASE_URL=http://localhost:11434/api/generate
export OLLAMA_MODEL=llama3.2
vulnhuntr -r /path/to/target/repo/ -a server.py -l ollama
```

## Logic Flow
![VulnHuntr logic](https://github.com/user-attachments/assets/7757b053-36ff-425e-ab3d-ab0100c81d49)
- LLM summarizes the README and includes this in the system prompt
- LLM does initial analysis on an entire file and reports any potential vulnerabilities
- Vulnhuntr then gives the LLM a vulnerability-specific prompt for secondary analysis
- Each time the LLM analyzes the code, it requests additional context functions/classes/variables from other files in the project
- It continues doing this until the entire call chain from user input to server processing is complete then gives a final analysis
- The final analysis consists of it's reasoning, a proof of concept exploit, and a confidence score

>[!TIP]
> Generally confidence scores < 7 mean there's unlikely a vulnerability. Confidence scores of 7 mean it should be investigated, and confidence scores of 8+ mean it is very likely to be a valid vulnerability.

## Output

The tool generates a detailed report of the vulnerabilities found in the analyzed files. The report includes:

- Initial assessment results for each file.
- Secondary assessment results with context functions and class references.
- Confidence scores for vulnerabilities found.
- Logs of the analysis process.
- PoC exploit

Below is an example of a Vulnhuntr report describing a 0-day remote code execution vulnerability in [Ragflow](https://github.com/infiniflow/ragflow) (now fixed):

```
scratchpad:
  1. Analyzing the add_llm function in llm_app.py. 2. Identified user input used as keys to access dictionaries: EmbeddingModel, ChatModel, RerankModel,
CvModel, and TTSModel. 3. These dictionaries contain class references, which are instantiated with user-supplied parameters. 4. The factory variable is 
directly used from user input (req['llm_factory']) without proper validation. 5. The llm_name is also derived from user input in most cases. 6. The 
instantiation of these classes occurs in try-except blocks, but exceptions are only used for error messages, not preventing execution. 7. The api_key 
and other sensitive information are passed directly to these instantiated classes. 8. There's no comprehensive input validation or sanitization for the 
factory or llm_name variables. 9. The vulnerability is in a route decorated with @login_required, indicating it's accessible to authenticated users. 10.
Reviewing the EmbeddingModel, ChatModel, RerankModel, CvModel, and TTSModel dictionaries to understand their contents and potential for exploitation.
----------------------------------------

analysis:
  The add_llm function in llm_app.py contains a critical Remote Code Execution (RCE) vulnerability. The function uses user-supplied input 
(req['llm_factory'] and req['llm_name']) to dynamically instantiate classes from the EmbeddingModel, ChatModel, RerankModel, CvModel, and TTSModel 
dictionaries. This pattern of using user input as a key to access and instantiate classes is inherently dangerous, as it allows an attacker to 
potentially execute arbitrary code. The vulnerability is exacerbated by the lack of comprehensive input validation or sanitization on these 
user-supplied values. While there are some checks for specific factory types, they are not exhaustive and can be bypassed. An attacker could potentially
provide a malicious value for 'llm_factory' that, when used as an index to these model dictionaries, results in the execution of arbitrary code. The 
vulnerability is particularly severe because it occurs in a route decorated with @login_required, suggesting it's accessible to authenticated users, 
which might give a false sense of security.
----------------------------------------

poc:
  POST /add_llm HTTP/1.1
  Host: target.com
  Content-Type: application/json
  Authorization: Bearer <valid_token>
  
  {
      "llm_factory": "__import__('os').system",
      "llm_name": "id",
      "model_type": "EMBEDDING",
      "api_key": "dummy_key"
  }
  
  This payload attempts to exploit the vulnerability by setting 'llm_factory' to a string that, when evaluated, imports the os module and calls system. 
The 'llm_name' is set to 'id', which would be executed as a system command if the exploit is successful.
----------------------------------------

confidence_score:
  8
----------------------------------------

vulnerability_types:
  - RCE
----------------------------------------
```

## Logging

The tool logs the analysis process and results in a file named `vulhuntr.log`. This file contains detailed information about each step of the analysis, including the initial and secondary assessments.


## Authors

- Dan McInerney: dan@protectai.com, [@DanHMcinerney](https://x.com/DanHMcInerney)
- Marcello Salvati: marcello@protectai.com, [@byt3bl33d3r](https://x.com/byt3bl33d3r)
