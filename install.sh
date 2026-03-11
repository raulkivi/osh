#!/bin/bash
set -euo pipefail

# Installer for Oh Shell! (osh) following XDG Base Directory specification

APP_DIR="$HOME/.local/osh"
BIN_DIR="$HOME/.local/bin"
CONFIG_DIR="$HOME/.config/osh"

echo "Hello. Installing Oh Shell! (osh)..."

# Check if ~/.local/bin is in PATH
if [[ ":$PATH:" != *":$BIN_DIR:"* ]]; then
  echo ""
  echo "Warning: $BIN_DIR is not in your PATH."
  echo "After installation, add it to your shell configuration:"
  echo ""
  echo "  # For bash (~/.bashrc or ~/.bash_profile):"
  echo "  export PATH=\"\$HOME/.local/bin:\$PATH\""
  echo ""
  echo "  # For zsh (~/.zshrc):"
  echo "  export PATH=\"\$HOME/.local/bin:\$PATH\""
  echo ""
fi

echo "- Cleaning up old installation..."
if [ -d "$APP_DIR" ]; then
  read -rp "  Remove existing installation at $APP_DIR? [Y/n]: " confirm_rm
  if [[ ! "$confirm_rm" =~ ^[Nn]$ ]]; then
    rm -rf "$APP_DIR"
  else
    echo "Installation cancelled."
    exit 1
  fi
fi
# Also clean up legacy installation if it exists
if [ -d "$HOME/osh" ]; then
  echo "  Found old installation at ~/osh, removing..."
  rm -rf "$HOME/osh"
fi

echo "- Creating directories..."
mkdir -p "$APP_DIR"
mkdir -p "$BIN_DIR"
mkdir -p "$CONFIG_DIR"

echo "- Copying application files..."
cp osh.py "$APP_DIR/"
cp ask.py "$APP_DIR/"
chmod +x "$APP_DIR/osh.py"
chmod +x "$APP_DIR/ask.py"

echo "- Creating executable links in $BIN_DIR..."
ln -sf "$APP_DIR/osh.py" "$BIN_DIR/osh"
ln -sf "$APP_DIR/ask.py" "$BIN_DIR/ask"
# Also create 'computer' alias for osh
ln -sf "$APP_DIR/osh.py" "$BIN_DIR/computer"

echo ""
echo "Python Virtual Environment Setup"
echo "================================="
echo ""
echo "Select Python environment for osh:"
echo "  1) pyenv virtual environment"
echo "  2) Standard Python venv"
echo "  3) System Python (no virtual environment)"
echo ""
read -rp "Choice [1/2/3]: " venv_choice

PYTHON_CMD="python3"
VENV_CONFIG=""
PYENV_VERSION_NAME=""

case $venv_choice in
  1)
    # pyenv option
    echo ""
    if ! command -v pyenv >/dev/null 2>&1; then
      echo "Error: pyenv not found. Please install pyenv or choose a different option."
      exit 1
    fi

    echo "Available pyenv versions:"
    pyenv versions --bare
    echo ""
    read -rp "Enter pyenv version name (e.g., py312): " pyenv_name

    if ! pyenv versions --bare | grep -q "^${pyenv_name}$"; then
      echo "Warning: pyenv version '$pyenv_name' not found."
      read -rp "Continue anyway? [y/N]: " confirm
      if [[ ! "$confirm" =~ ^[Yy]$ ]]; then
        exit 1
      fi
    fi

    PYTHON_CMD="pyenv exec python"
    PYENV_VERSION_NAME="$pyenv_name"
    VENV_CONFIG="pyenv:$pyenv_name"
    echo "Using pyenv environment: $pyenv_name"
    ;;

  2)
    # venv option
    echo ""
    read -rp "Enter path to venv directory (e.g., ~/venvs/osh): " venv_path
    venv_path="${venv_path/#\~/$HOME}"  # Expand ~ to full path

    if [ ! -d "$venv_path" ]; then
      echo ""
      read -rp "Virtual environment doesn't exist. Create it? [Y/n]: " create_venv
      if [[ ! "$create_venv" =~ ^[Nn]$ ]]; then
        echo "Creating virtual environment at $venv_path..."
        python3 -m venv "$venv_path"
      else
        echo "Installation cancelled."
        exit 1
      fi
    fi

    PYTHON_CMD="$venv_path/bin/python"
    VENV_CONFIG="venv:$venv_path"
    echo "Using venv at: $venv_path"
    ;;

  3)
    # System Python
    PYTHON_CMD="python3"
    VENV_CONFIG=""
    echo "Using system Python"
    ;;

  *)
    echo "Invalid choice. Please re-run and enter 1, 2, or 3."
    exit 1
    ;;
esac

echo ""
echo "- Installing Python dependencies..."
if [ -n "$PYENV_VERSION_NAME" ]; then
  PYENV_VERSION="$PYENV_VERSION_NAME" pyenv exec python -m pip install -q -r requirements.txt
elif [ "$PYTHON_CMD" = "python3" ]; then
  "$PYTHON_CMD" -m pip install -q --user -r requirements.txt
else
  "$PYTHON_CMD" -m pip install -q -r requirements.txt
fi

# Ollama Model Selection
echo ""
echo "Ollama Model Selection"
echo "======================"
echo ""

SELECTED_MODEL=""
if command -v ollama >/dev/null 2>&1; then
  echo "Available Ollama models:"
  echo ""

  mapfile -t MODELS < <(ollama list | tail -n +2 | awk '{print $1}' | grep -v '^$')

  if [ ${#MODELS[@]} -eq 0 ]; then
    echo "No models found. Please install a model first using:"
    echo "  ollama pull llama3"
    echo ""
    read -rp "Skip model selection? [Y/n]: " skip_model
    if [[ "$skip_model" =~ ^[Nn]$ ]]; then
      exit 1
    fi
  else
    # Display models with numbers
    for i in "${!MODELS[@]}"; do
      printf "  %d) %s\n" $((i+1)) "${MODELS[$i]}"
    done
    echo ""
    echo "Recommended: llama3:latest (fast, reliable)"
    echo "Note: Avoid reasoning models like deepseek-r1 for shell commands"
    echo ""
    read -rp "Select model number [or press Enter to skip]: " model_choice

    if [ -n "$model_choice" ] && \
       [[ "$model_choice" =~ ^[0-9]+$ ]] && \
       [ "$model_choice" -ge 1 ] && \
       [ "$model_choice" -le "${#MODELS[@]}" ]; then
      SELECTED_MODEL="${MODELS[$((model_choice-1))]}"
      echo "Selected model: $SELECTED_MODEL"
    else
      echo "No model selected, will use default configuration"
    fi
  fi
else
  echo "Warning: ollama not found. Install it from https://ollama.com"
  echo "Skipping model selection..."
fi

# Save configuration
echo ""
read -rp "Save configuration to osh config? [Y/n]: " save_config
if [[ ! "$save_config" =~ ^[Nn]$ ]]; then
  mkdir -p "$CONFIG_DIR"

  # Pass shell values via environment variables — no shell interpolation inside Python source
  selected_model="$SELECTED_MODEL" venv_config="$VENV_CONFIG" config_dir="$CONFIG_DIR" \
  python3 - <<'PYEOF'
import json, os
from pathlib import Path

config_path = Path(os.environ["config_dir"]) / "config.json"
venv_config  = os.environ.get("venv_config", "")
selected_model = os.environ.get("selected_model", "")

try:
    config = json.loads(config_path.read_text())
except Exception:
    config = {
        "api": "ollama",
        "temperature": 0.3,
        "max_tokens": 2400,
        "safety": True,
        "modify": False,
        "qa_review": True,
        "suggested_command_color": "blue",
        "ollama_endpoint": "http://localhost:11434",
        "ollama_cloud_endpoint": "https://ollama.com",
        "logging_enabled": True,
        "log_retention_days": 30,
    }

if venv_config:
    config["python_venv"] = venv_config
if selected_model:
    config["model"] = selected_model
elif "model" not in config:
    config["model"] = "llama3:latest"

config_path.write_text(json.dumps(config, indent=2) + "\n")

print(f"Configuration saved to: {config_path}")
if selected_model:
    print(f"Model: {selected_model}")
if venv_config:
    print(f"Python environment: {venv_config}")
PYEOF
else
  echo "Configuration not saved. Run 'osh --init' to configure later."
fi

echo ""
echo "Installation complete!"
echo ""
echo "Next steps:"
if [ -f "$CONFIG_DIR/config.json" ]; then
  echo "  1. Review your configuration: $CONFIG_DIR/config.json"
  echo "     (Run 'osh --init' to reconfigure)"
else
  echo "  1. Configure osh by running: osh --init"
fi
echo "  2. If $BIN_DIR is not in your PATH, add it to your shell config"
echo "  3. Restart your shell or run: source ~/.bashrc (or ~/.zshrc)"
echo ""
echo "Usage:"
echo "  osh what is my username"
echo "  echo 'your question' | ask"
echo ""
