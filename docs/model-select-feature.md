# Feature: Support specifying Ollama model name as command line parameter

Users can select a different model than the one provided in the configuration file using the `-m` / `--model` flag.

## Usage

1. **Direct model override** — specify a model name explicitly:
   ```
   osh -m <model_name> <question>
   ```
   Example: `osh -m llama3.2 list files in current directory`

2. **Interactive model selection** — pass `-` to list available models and pick one:
   ```
   osh -m - <question>
   ```
   Example: `osh -m - list files in current directory`
   This queries the configured Ollama endpoint, displays a numbered list of available models, and prompts the user to select one before proceeding.

## Behavior

- If `-m` is not provided, the model from the config file is used (unchanged behavior).
- The `-m` flag overrides `config["model"]` for the current invocation only; it does not modify the config file.
- If `-` is used and Ollama returns no models, the application exits with an error message.
