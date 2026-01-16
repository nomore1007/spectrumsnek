#!/bin/bash
# SpectrumSnek Launcher Script
# Activates virtual environment and runs the main application

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="$SCRIPT_DIR/venv"

# Function to check if required system packages are installed
check_system_dependencies() {
    local missing_packages=""

    # Check for required commands/packages
    if ! command -v python3 &> /dev/null; then
        missing_packages="$missing_packages python3"
    fi

    # Skip pip check - it's available via python3 -m pip if needed

    if ! dpkg -l | grep -q rtl-sdr; then
        missing_packages="$missing_packages rtl-sdr"
    fi

    # Check for Python dev headers (more flexible check)
    if ! dpkg -l | grep -q "python3.*dev" && ! dpkg -l | grep -q "python3.*headers"; then
        missing_packages="$missing_packages python3-dev"
    fi

    if [ -n "$missing_packages" ]; then
        echo "Missing required system packages:$missing_packages"
        echo "Running automatic setup to install dependencies..."
        return 1
    fi

    return 0
}

# Function to check if Python virtual environment has required packages
check_python_dependencies() {
    if [ ! -f "$VENV_DIR/bin/activate" ]; then
        echo "Virtual environment not properly set up."
        return 1
    fi

    # Activate venv temporarily to check packages
    source "$VENV_DIR/bin/activate"

    # Check critical Python packages
    if ! python -c "import rtlsdr" 2>/dev/null; then
        echo "RTL-SDR Python library not found in virtual environment."
        deactivate
        return 1
    fi

    if ! python -c "import numpy" 2>/dev/null; then
        echo "NumPy not found in virtual environment."
        deactivate
        return 1
    fi

    if ! python -c "import scipy" 2>/dev/null; then
        echo "SciPy not found in virtual environment."
        deactivate
        return 1
    fi

    deactivate
    return 0
}

# Check system dependencies
if ! check_system_dependencies; then
    if [ -f "./setup.sh" ]; then
        ./setup.sh --console
    else
        echo "Setup script not found. Please ensure setup.sh exists."
        exit 1
    fi
fi

# Check if virtual environment exists, auto-setup if needed
if [ ! -d "$VENV_DIR" ]; then
    echo "Virtual environment not found. Running automatic setup..."
    if [ -f "./setup.sh" ]; then
        ./setup.sh --console
    else
        echo "Setup script not found. Please ensure setup.sh exists."
        exit 1
    fi
fi

# Check Python dependencies
if ! check_python_dependencies; then
    echo "Python dependencies missing. Running automatic setup..."
    if [ -f "./setup.sh" ]; then
        ./setup.sh --console
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