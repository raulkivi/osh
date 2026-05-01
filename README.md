# Oh Shell! (osh)

![Version](https://img.shields.io/badge/version-0.1-blue) ![License](https://img.shields.io/badge/license-MIT-green)

Learn and use Linux through natural language — powered by local LLMs via Ollama.

Describe what you want in plain English and get 3–6 executable command options, each with detailed explanations that break down every pipe, flag, and chained command so you understand what you're running.

## Features

- **Interactive shell mode** — Run `osh` with no arguments to enter a REPL; type queries continuously, use `!help` for commands, or `exit` / `!exit` to leave
- **Natural language to shell** — Describe what you want; get valid commands back
- **3–6 alternatives per query** — Shell commands plus one-liners in awk, perl, python3, etc.
- **Detailed explanations** — Each chained command (pipes, `&&`, `;`) explained on its own line
- **QA safety review** — Second-pass LLM review flags dangerous, incorrect, or imprecise commands
- **Command availability check** — Detects whether each suggested tool is installed before you run it
- **Language detection** — Auto-detects available scripting languages (bash, awk, perl, python3, ruby, node, etc.) and only suggests commands using what's installed
- **Cloud model support** — Use any Ollama cloud model by appending `:cloud` or `-cloud` to the model name (e.g. `llama3.2:cloud`); authenticates via `OLLAMA_API_KEY`
- **Per-invocation model override** — Use `-m <model>` to pick a different model without editing config; use `-m -` to select interactively from available Ollama models
- **Thinking model support** — Handles models that use a separate `thinking` field (e.g., gpt-oss, deepseek-r1) with automatic response extraction and reformatting
- **Clipboard support** — Copy any command to clipboard instead of executing
- **Retry on failure** — If a command fails or misses the question, refine and retry interactively
- **Daily log files** — All queries, responses, verdicts, and user actions logged to `~/.local/state/osh/YYYYMMDD.log`
- **XDG-compliant paths** — Config in `~/.config/osh/`, state in `~/.local/state/osh/`, app in `~/.local/osh/`
- **`ask` companion** — Pipe any text through `ask` for general-purpose LLM Q&A

## Requirements

- Python 3.11+
- [Ollama](https://ollama.ai) installed and running locally

## Quick Start

```bash
# Install
./install.sh

# Use
osh what is my public IP address
osh find all python files modified in the last 24 hours
osh show failed ssh login attempts grouped by IP
```

## Installation

```bash
./install.sh
```

The installer will:
1. Copy app files to `~/.local/osh/`
2. Create symlinks in `~/.local/bin/` (`osh`, `ask`, `computer`)
3. Prompt for Python environment (pyenv, venv, or system)
4. Install pip dependencies
5. Let you select an Ollama model
6. Save configuration to `~/.config/osh/config.json`

After installation, ensure `~/.local/bin` is in your PATH:

```bash
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.zshrc  # or ~/.bashrc
source ~/.zshrc
```

### Manual Install

```bash
pip3 install -r requirements.txt
chmod +x osh.py ask.py
mkdir -p ~/.local/bin
ln -s $(pwd)/osh.py ~/.local/bin/osh
ln -s $(pwd)/ask.py ~/.local/bin/ask
osh --init
```

## Usage

```bash
osh                         # Enter interactive shell mode (REPL)
osh <natural language query>
osh -a <query>              # Always prompt before executing
osh -m <model> <query>      # Use a specific model (overrides config)
osh -m - <query>            # Pick model interactively from Ollama
osh --config PATH <query>   # Use alternate config file
osh --init                  # Interactive configuration
osh --version               # Show version
```

### Shell Mode (REPL)

Running `osh` without arguments enters an interactive session where you can submit queries one after another without re-invoking the command.

```
$ osh
Oh Shell! - Interactive Shell Mode
Type your request in plain English, or '!help' for commands, '!' to exit.

osh> show disk usage of home directory
...
osh> !help
Available commands:
  !exit                Exit shell mode
  !quit                Exit shell mode
  !help                Show this help message
  !version             Show osh version
  !history             Show recent queries from today's session log
  !                    Exit shell mode (shorthand)

Or type any request in plain English.
osh> exit
Exiting shell mode.
```

| Input | Action |
|-------|--------|
| Any natural language | Translated to shell commands as normal |
| `exit`, `quit`, `bye`, `done`, … | Exit shell mode |
| `!exit` / `!quit` / `!` | Exit shell mode |
| `!help` | List available `!` commands |
| `!version` | Show osh version |
| `!history` | Show recent queries from today's session log |
| Ctrl-C / Ctrl-D | Exit shell mode |

### Example Session

```zsh
$ osh find all log files modified in the last 7 days and show their sizes

Checking command availability...
Running safety review...

Available commands:

  1. find /var/log -name '*.log' -mtime -7 -exec du -sh {} + [PASS]
     Find all .log files modified within 7 days and display their sizes
     find /var/log -name '*.log' -mtime -7: search for .log files modified in the last 7 days
     -exec du -sh {} +: calculate and display human-readable size for each match

  2. find /var/log -name '*.log' -mtime -7 | xargs du -sh [PASS]
     Same goal using pipe to xargs instead of -exec
     find /var/log -name '*.log' -mtime -7: locate recently modified .log files
     | xargs du -sh: pass found files to du for size display

  3. perl -e 'use File::Find; find(sub { print `du -sh $_` if /\.log$/ && -M $_ < 7 }, "/var/log")' [PASS]
     Perl one-liner using File::Find to traverse /var/log
     find(sub { ... }, "/var/log"): recursively walk the directory
     /\.log$/ && -M $_ < 7: match .log files modified within 7 days
     print `du -sh $_`: shell out to du for each match

Select command [1/2/3] [c]opy or [n]o ==>
```

### Selection Options

| Key | Action |
|-----|--------|
| **1–6** | Execute that command |
| **c** | Copy a command to clipboard |
| **n** / Enter | Cancel |

### QA Verdicts

Each command is tagged by the safety review:

| Verdict | Meaning |
|---------|---------|
| **PASS** (green) | Correct, safe, matches intent |
| **WARN** (yellow) | Works but has a concern — confirmation required |
| **MISS** (magenta) | Safe but doesn't precisely answer the question |
| **FAIL** (red) | Dangerous, incorrect, or insecure — execution blocked |

### Ask

Pipe text to `ask` for general-purpose Q&A:

```bash
ask "What is the capital of France?"
ask what is the capital of France?
echo "What is the capital of France?" | ask
cat error.log | ask "What went wrong?"
```

## Configuration

### Interactive Setup

```bash
osh --init
```

### Config File

`~/.config/osh/config.json`:

```json
{
  "api": "ollama",
  "model": "gpt-oss:latest",
  "temperature": 0.3,
  "max_tokens": 2400,
  "safety": true,
  "qa_review": true,
  "suggested_command_color": "blue",
  "python_venv": null,
  "ollama_endpoint": "http://localhost:11434",
  "ollama_cloud_endpoint": "https://ollama.com",
  "logging_enabled": true,
  "log_retention_days": 30
}
```

| Option | Description | Default |
|--------|-------------|---------|
| `model` | Ollama model name | `gpt-oss:latest` |
| `temperature` | Randomness (0.0–2.0) | `0.3` |
| `max_tokens` | Max response tokens (increase for thinking models) | `2400` |
| `safety` | Prompt before executing commands | `true` |
| `qa_review` | Enable second-pass safety review | `true` |
| `suggested_command_color` | Terminal color for displayed commands | `blue` |
| `python_venv` | `null`, `"pyenv:name"`, or `"venv:/path"` | `null` |
| `ollama_endpoint` | Local Ollama API URL | `http://localhost:11434` |
| `ollama_cloud_endpoint` | Ollama cloud API URL | `https://ollama.com` |
| `logging_enabled` | Enable daily log files | `true` |
| `log_retention_days` | Auto-delete logs older than N days | `30` |

### Custom Config Path

```bash
osh --config /path/to/config.json what is my username
```

### Python Virtual Environment

```json
{"python_venv": "pyenv:312"}
{"python_venv": "venv:/home/user/.venvs/myenv"}
{"python_venv": null}
```

### Cloud Models

Ollama cloud models can be used by appending `:cloud` or `-cloud` to any model name:

```bash
osh -m llama3.2:cloud list files modified today
osh -m llama3.2-cloud what is my public IP
```

Or set a cloud model as your default in `~/.config/osh/config.json`:

```json
{"model": "llama3.2:cloud"}
```

**Setup (one-time):**

1. Create a free account at [https://ollama.com](https://ollama.com)
2. Generate an API key in your account settings
3. Export the key in your shell profile (`~/.bashrc` or `~/.zshrc`):

```bash
export OLLAMA_API_KEY=<your-key>
```

If `OLLAMA_API_KEY` is not set when a cloud model is invoked, osh will exit with a clear error and setup instructions.

## Examples

```bash
# System
osh what is my current working directory
osh show me system uptime
osh check if port 8080 is open

# Files
osh find all files larger than 100MB
osh compress the logs directory
osh count lines in all python files recursively

# Network
osh what is my public IP address
osh list all IP addresses of NICs that start with wlp
osh show all open network connections

# Processes
osh is nginx running
osh show all python processes
osh kill process on port 3000

# Data processing
osh extract columns 1 and 3 from data.csv
osh count unique values in column 2 of users.csv sorted by frequency

# Log analysis
osh show failed ssh login attempts from auth.log grouped by IP
osh extract unique IPs from nginx access.log that returned 404
osh find all sudo commands in auth.log grouped by user
```

## Architecture

### Processing Pipeline

```
User query
  → LLM generates 3–6 command options (XML-tagged: <c1>...<e1>...)
  → Parse response (auto-reformat if thinking model produced verbose output)
  → Check command availability (shutil.which + shell builtins)
  → QA safety review (second LLM call evaluating each command)
  → Display options with verdicts
  → User selects → Execute
```

### Key Components

| File | Purpose |
|------|---------|
| `osh.py` | Main application — prompts, LLM interaction, parsing, execution |
| `ask.py` | Pipe-based general Q&A companion |
| `install.sh` | Interactive installer with venv and model selection |

### Thinking Model Handling

Models like gpt-oss place output in a `thinking` field instead of `content`. Osh automatically:
1. Extracts tagged commands from the thinking field if present
2. If no tags found, sends the raw thinking text through a reformat pass
3. Retries reformatting up to 5 times with increased token budget (3× configured max_tokens, minimum 2400)
4. Filters placeholder/garbage commands (literal "command", "echo 'Could not extract commands'")
5. Enforces minimum 3 valid options before accepting

### Language Detection

On startup, osh probes for available scripting languages:

```
bash, awk, sed, perl, python3, ruby, node, php, lua, Rscript
```

The detected list is injected into the system prompt so the model only suggests commands using tools actually installed on the system.

## Logging

Daily log files in `~/.local/state/osh/YYYYMMDD.log`:

```
2026-02-21 10:30:45 | INFO | USER_QUERY: find large files
2026-02-21 10:30:45 | INFO | MODEL: gpt-oss:latest | TEMPERATURE: 0.3 | MAX_TOKENS: 2400
2026-02-21 10:30:45 | INFO | AVAILABLE_LANGUAGES: bash, awk, sed, perl, python3, node
2026-02-21 10:30:47 | INFO | LLM_RESPONSE: <c1>find / -size +100M...</c1>...
2026-02-21 10:30:48 | INFO | COMMAND_CHECK: find | EXISTS: True
2026-02-21 10:30:49 | INFO | QA_REVIEW: Sending 3 commands for safety review
2026-02-21 10:30:50 | INFO | QA_RESPONSE: 1|PASS| | 2|PASS| | 3|WARN|Requires sudo
2026-02-21 10:30:52 | INFO | USER_SELECTED: Option 1 | COMMAND: find / -size +100M
2026-02-21 10:30:52 | INFO | ACTION: EXECUTE
```

Old logs auto-deleted after `log_retention_days` (default: 30).

## Uninstall

```bash
rm -rf ~/.local/osh ~/.config/osh ~/.local/state/osh
rm -f ~/.local/bin/osh ~/.local/bin/ask ~/.local/bin/computer
pip3 uninstall ollama termcolor pyperclip
```

## Ollama Setup

```bash
curl -fsSL https://ollama.ai/install.sh | sh
ollama pull llama3
```

## License

[MIT](LICENSE) © 2026 [Raul Kivi](https://www.linkedin.com/in/raulkivi/)
