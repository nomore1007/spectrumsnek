#!/bin/bash
# RTL-SDR Radio Scanner Launcher

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Virtual environment not found. Please run setup first."
    exit 1
fi

# Activate virtual environment
source venv/bin/activate

# Check for demo mode
if [[ "$1" == "--demo" ]]; then
    echo "Running in demo mode (no hardware required)..."
    shift  # Remove --demo from arguments
    python demo_scanner.py "$@"
# Check for interactive mode
elif [[ "$1" == "--interactive" ]]; then
    echo "Running RTL-SDR scanner in interactive mode..."
    shift  # Remove --interactive from arguments
    python rtl_scanner.py "$@"
# Check for web mode
elif [[ "$1" == "--web" ]]; then
    echo "Running RTL-SDR scanner in web interface mode..."
    python rtl_scanner.py "$@"
else
    # Run the radio scanner with provided arguments
    python radio_scanner.py "$@"
fi

# Deactivate virtual environment
deactivate