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

# Activate virtual environment and run main.py
if [ -f "$VENV_DIR/bin/activate" ]; then
    source "$VENV_DIR/bin/activate"
else
    echo "Virtual environment activation script not found. Recreating venv..."
    python3 -m venv "$VENV_DIR" --clear
    source "$VENV_DIR/bin/activate"
    pip install -r requirements.txt --break-system-packages
fi

# Export virtual environment variables explicitly for sudo compatibility
export PATH="$VENV_DIR/bin:$PATH"
export PYTHONPATH="$SCRIPT_DIR:$PYTHONPATH"
export VIRTUAL_ENV="$VENV_DIR"

python main.py "$@"

# Deactivate when done (though this won't be reached in curses mode)
deactivate