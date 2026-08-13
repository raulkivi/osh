# Feature: Display model info at startup

At startup, show the user the host and model name currently in use.

## Behavior

- The host (Ollama endpoint URL) and model name are printed to the terminal before the first query is processed.
- Values are sourced from the active configuration (after any `-m` / `--model` override is applied).
