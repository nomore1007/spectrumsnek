#!/bin/bash
# SpectrumSnek Runner Script
# Automatically activates virtual environment and runs the main menu

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="$SCRIPT_DIR/venv"

# Check if virtual environment exists
if [ ! -d "$VENV_DIR" ]; then
    echo "Error: Virtual environment not found at $VENV_DIR"
    echo "Please run setup.sh first to create the environment."
    exit 1
fi

# Set terminal if not set
if [ -z "$TERM" ]; then
    export TERM=linux
fi

# Activate virtual environment
echo "Activating virtual environment..."
source "$VENV_DIR/bin/activate"

# Run the main application
echo "Starting SpectrumSnek..."
python "$SCRIPT_DIR/main.py"

# Deactivate when done
deactivate