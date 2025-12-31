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

# Activate virtual environment and run main.py
source "$VENV_DIR/bin/activate"
cd "$SCRIPT_DIR"
python main.py "$@"

# Deactivate when done (though this won't be reached in curses mode)
deactivate