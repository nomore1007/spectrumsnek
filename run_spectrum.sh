#!/bin/bash
# SpectrumSnek Launcher Script
# Activates virtual environment and runs the main application

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="$SCRIPT_DIR/venv"

# Check if virtual environment exists, auto-setup if needed
if [ ! -d "$VENV_DIR" ]; then
    echo "Virtual environment not found. Running automatic setup..."
    if [ -f "./setup.sh" ]; then
        ./setup.sh --auto
    else
        echo "Setup script not found. Please ensure setup.sh exists."
        exit 1
    fi
fi

# Handle special commands
if [ "$1" = "--reinstall-deps" ]; then
    echo "Reinstalling Python dependencies..."
    source "$VENV_DIR/bin/activate"
    cd "$SCRIPT_DIR"
    pip install --upgrade pip setuptools --break-system-packages
    pip install -r requirements.txt --break-system-packages
    echo "Dependencies reinstalled successfully."
    exit 0
fi

cd "$SCRIPT_DIR"

# Use system Python in containerized environments (skip venv)
# Ensure user site-packages are in PYTHONPATH for pyModeS
export PYTHONPATH="$HOME/.local/lib/python3.12/site-packages:$PYTHONPATH"
python3 main.py "$@"

# Deactivate when done (though this won't be reached in curses mode)
deactivate