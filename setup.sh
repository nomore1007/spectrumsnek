#!/bin/bash
# SpectrumSnek Setup Script - Complete Installation

# Enable logging
exec > >(tee setup.log) 2>&1

echo "SpectrumSnek Setup"
echo "=================="
echo ""
echo "Setting up SpectrumSnek radio analysis toolkit..."
echo ""

# Function to check if running as root
check_root() {
    if [ "$EUID" -eq 0 ]; then
        return 0
    else
        return 1
    fi
}

# Function to get sudo command
get_sudo() {
    if check_root; then
        echo ""
    else
        if command -v sudo &> /dev/null; then
            echo "sudo"
        else
            echo ""
        fi
    fi
}

# Set sudo command
SUDO_CMD=$(get_sudo)

# Function to safely install apt packages
safe_apt_install() {
    if $SUDO_CMD apt install -y "$@" 2>/dev/null; then
        return 0
    else
        return 1
    fi
}

# Function to safely run apt update
safe_apt_update() {
    if $SUDO_CMD apt update 2>/dev/null; then
        return 0
    else
        return 1
    fi
}

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is required but not found"
    exit 1
fi
echo "✓ Python 3 found"

# Update package lists
echo "Updating package lists..."
safe_apt_update

# Install system dependencies
echo "Installing system dependencies..."
SYSTEM_PACKAGES="git build-essential python3-dev python3-venv python3-pip rtl-sdr libusb-1.0-0-dev pkg-config libncurses5-dev libportaudio2 libasound2-dev"
if safe_apt_install $SYSTEM_PACKAGES; then
    echo "✓ System dependencies installed"
else
    echo "⚠ Some system dependencies may have failed to install"
fi

# Setup Python virtual environment
echo "Setting up Python virtual environment..."
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="$SCRIPT_DIR/venv"

if [ ! -d "$VENV_DIR" ]; then
    python3 -m venv "$VENV_DIR"
    if [ $? -eq 0 ]; then
        echo "✓ Virtual environment created"
    else
        echo "❌ Failed to create virtual environment"
        exit 1
    fi
else
    echo "✓ Virtual environment already exists"
fi

# Activate virtual environment and install Python packages
echo "Installing Python dependencies..."
source "$VENV_DIR/bin/activate"

# Upgrade pip
python -m pip install --upgrade pip setuptools wheel

# Install from requirements.txt
if [ -f "requirements.txt" ]; then
    if pip install -r requirements.txt; then
        echo "✓ Python dependencies installed from requirements.txt"
    else
        echo "⚠ Some Python dependencies may have failed to install"
    fi
else
    echo "⚠ requirements.txt not found"
fi

# Install the one supported ADS-B decoder: readsb.
# Decoder choice and lifecycle are centralized in sdr_manager.py.
echo "Checking for readsb..."
if ! command -v readsb >/dev/null 2>&1; then
    if safe_apt_install readsb; then
        echo "✓ readsb installed"
    else
        echo "⚠ readsb could not be installed automatically."
        echo "  Install readsb manually or set READSB_BIN to its executable path."
    fi
else
    echo "✓ readsb already available"
fi

echo "SpectrumSnek setup complete!"
echo ""
echo "To start: ./run_spectrum.sh"
echo ""
echo "Available tools:"
echo "  • RTL-SDR Spectrum Analyzer"
echo "  • ADS-B Aircraft Tracker"
echo "  • Traditional Radio Scanner"
echo "  • WiFi Network Selector"
echo "  • Bluetooth Device Connector"
echo "  • Audio Output Selector"
