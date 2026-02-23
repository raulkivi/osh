#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import re
import sys
from typing import Any

# Matches ANSI/VT escape sequences (CSI and single-char ESC) to prevent terminal injection
_ANSI_ESCAPE: re.Pattern[str] = re.compile(
    r'(?:\x1B[@-Z\\-_]|\x1B\[[0-?]*[ -/]*[@-~])'
)

# Default Configuration
DEFAULT_CONFIG: dict[str, Any] = {
    "api": "ollama",
    "model": "gpt-oss:latest",
    "temperature": 0.3,
    "max_tokens": 400,
    "python_venv": None,
    "ollama_endpoint": "http://localhost:11434",
}


def get_config_path() -> str:
    """Get config file path, respecting XDG_CONFIG_HOME."""
    config_home: str = os.environ.get(
        'XDG_CONFIG_HOME',
        os.path.expanduser('~/.config')
    )
    return os.path.join(config_home, 'osh', 'config.json')


def get_python_venv_early() -> str | None:
    """Early lightweight config read to get python_venv setting before imports.
    
    This runs before venv activation, so it can't use the full config system.
    Falls back to default if config is missing or malformed.
    """
    config_path: str = get_config_path()
    
    try:
        if os.path.exists(config_path):
            with open(config_path, 'r') as f:
                config: dict[str, Any] = json.load(f)
            return config.get('python_venv')
    except Exception:
        pass  # Fall through to default
    
    return DEFAULT_CONFIG['python_venv']


def load_config() -> dict[str, Any]:
    """Load configuration from JSON file, merging with defaults.
    
    Returns:
        Configuration dictionary with user settings merged over defaults
    """
    config_path: str = get_config_path()
    
    # Start with defaults
    config: dict[str, Any] = DEFAULT_CONFIG.copy()
    
    # Try to load user config
    if not os.path.exists(config_path):
        return config
    
    try:
        with open(config_path, 'r') as f:
            user_config: dict[str, Any] = json.load(f)
        # Merge user config over defaults
        config.update(user_config)
    except Exception as e:
        print(f"Warning: Error loading config from {config_path}: {e}", file=sys.stderr)
        print("Continuing with default configuration.", file=sys.stderr)
    
    return config

SYSTEM_PROMPT = """\
You are a helpful, highly skilled expert. Provide clear, accurate, and concise answers. \
When appropriate, include examples or explanations. Use plain text output without \
markdown formatting.\
"""


def check_and_activate_venv() -> None:
    """Check and activate configured virtual environment if specified."""
    python_venv: str | None = get_python_venv_early()
    if not python_venv:
        return

    expected_python: str
    venv_display_name: str = python_venv

    if python_venv.startswith('pyenv:'):
        venv_name: str = python_venv[6:]
        home: str = os.path.expanduser("~")
        pyenv_versions: str = os.path.realpath(os.path.join(home, ".pyenv", "versions"))
        candidate: str = os.path.realpath(os.path.join(pyenv_versions, venv_name))
        if not candidate.startswith(pyenv_versions + os.sep):
            print(
                f"Warning: Invalid pyenv environment name '{venv_name}': path traversal detected",
                file=sys.stderr,
            )
            return
        venv_path: str = candidate
        expected_python = os.path.join(venv_path, "bin", "python")
        venv_display_name = venv_name
    elif python_venv.startswith('venv:'):
        venv_path = os.path.expanduser(python_venv[5:])
        expected_python = os.path.join(venv_path, "bin", "python")
    else:
        venv_path = os.path.expanduser(python_venv)
        expected_python = os.path.join(venv_path, "bin", "python")

    # Check if already running in the expected environment
    if venv_display_name in sys.prefix or expected_python == sys.executable:
        return

    if os.path.exists(expected_python):
        os.execv(expected_python, [expected_python] + sys.argv)
    else:
        print(
            f"Warning: Configured Python venv not found at {expected_python}",
            file=sys.stderr
        )
        print(
            f"Continuing with current Python: {sys.executable}",
            file=sys.stderr
        )


check_and_activate_venv()

from ollama import ChatResponse, Client


def main() -> None:
    if sys.stdin.isatty():
        print("Usage: echo 'your question' | ask", file=sys.stderr)
        print("       some_command | ask", file=sys.stderr)
        sys.exit(1)

    MAX_STDIN_BYTES: int = 1 * 1024 * 1024  # 1 MB
    raw: str = sys.stdin.read(MAX_STDIN_BYTES)
    if len(raw) == MAX_STDIN_BYTES:
        print("Warning: input truncated at 1 MB.", file=sys.stderr)
    user_input: str = raw.strip()
    if not user_input:
        print("No input received.", file=sys.stderr)
        sys.exit(1)

    config: dict[str, Any] = load_config()
    client = Client(host=config.get("ollama_endpoint", "http://localhost:11434"))

    options: dict[str, Any] = {}
    if config.get('temperature') is not None:
        options['temperature'] = config['temperature']
    if config.get('max_tokens') is not None:
        options['num_predict'] = config['max_tokens']

    try:
        response: ChatResponse = client.chat(  # type: ignore[misc]
            model=config["model"],
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_input},
            ],
            options=options,
            stream=False,
        )
    except Exception as e:
        print(f"Error communicating with model: {e}", file=sys.stderr)
        sys.exit(1)

    content: str = getattr(response.message, 'content', None) or ""
    if not content.strip():
        print("Error: empty response from model.", file=sys.stderr)
        sys.exit(1)

    print(_ANSI_ESCAPE.sub('', content))


if __name__ == "__main__":
    main()
