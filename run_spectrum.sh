#!/bin/bash
# SpectrumSnek Launcher Script
# Activates virtual environment and runs the main application

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="$SCRIPT_DIR/venv"

# Check if virtual environment exists
if [ ! -d "$VENV_DIR" ]; then
    echo "Virtual environment not found. Please run ./setup.sh first."
    exit 1
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

# Activate virtual environment and run main.py
source "$VENV_DIR/bin/activate"
cd "$SCRIPT_DIR"
python main.py "$@"

# Deactivate when done (though this won't be reached in curses mode)
deactivate