#!/bin/bash
# SpectrumSnek setup script.

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# Keep normal setup output in setup.log. Record timestamped stderr separately.
exec > >(tee -a "$SCRIPT_DIR/setup.log") 2> >(while IFS= read -r error_line; do
    printf '[%s] [setup] %s\n' "$(date '+%Y-%m-%d %H:%M:%S')" "$error_line" | tee -a "$SCRIPT_DIR/error.log" >&2
done)

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
    if $SUDO_CMD apt install -y "$@"; then
        return 0
    else
        return 1
    fi
}

# Function to safely run apt update
safe_apt_update() {
    if $SUDO_CMD apt update; then
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
SYSTEM_PACKAGES="git build-essential python3-dev python3-venv python3-pip rtl-sdr librtlsdr-dev libusb-1.0-0-dev zlib1g-dev pkg-config libncurses-dev libportaudio2 libasound2-dev"
if safe_apt_install $SYSTEM_PACKAGES; then
    echo "✓ System dependencies installed"
else
    echo "⚠ Some system dependencies may have failed to install"
fi

# Setup Python virtual environment
echo "Setting up Python virtual environment..."
cd "$SCRIPT_DIR"
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

# Install the ADS-B plugin from its independent repository. Its directory is
# ignored by the core repository so core updates do not overwrite plugin files.
echo "Installing the ADS-B Radar plugin..."
if bash "$SCRIPT_DIR/plugin_manager.sh" install adsb_radar; then
    echo "✓ ADS-B Radar plugin installed"
else
    echo "⚠ ADS-B Radar plugin installation failed. You can retry from Utilities > Installed Plugins."
fi

# Build readsb ourselves with RTL-SDR support. The distro's /usr/bin/readsb
# may be compiled without RTL-SDR, so SpectrumSnek uses this project-local copy.
echo "Building readsb with RTL-SDR support..."
READSB_SOURCE_DIR="$SCRIPT_DIR/.local/src/readsb"
READSB_INSTALL_DIR="$SCRIPT_DIR/.local/bin"
READSB_BIN="$READSB_INSTALL_DIR/readsb"

mkdir -p "$READSB_INSTALL_DIR" "$(dirname "$READSB_SOURCE_DIR")" || exit 1

if [ ! -d "$READSB_SOURCE_DIR/.git" ]; then
    if ! git clone https://github.com/wiedehopf/readsb.git "$READSB_SOURCE_DIR"; then
        echo "❌ Failed to clone the readsb source repository"
        exit 1
    fi
else
    echo "Updating existing readsb source..."
    if ! git -C "$READSB_SOURCE_DIR" pull --ff-only; then
        echo "❌ Could not fast-forward the existing readsb source checkout."
        echo "   Resolve that checkout in $READSB_SOURCE_DIR and rerun setup."
        exit 1
    fi
fi

if ! make -C "$READSB_SOURCE_DIR" clean; then
    echo "❌ Failed to clean the readsb build"
    exit 1
fi

# Pi Zero 2 W has four CPU cores but limited RAM; keep parallelism conservative.
if ! make -C "$READSB_SOURCE_DIR" -j2 RTLSDR=yes; then
    echo "❌ readsb compilation failed. Check setup.log for compiler output."
    exit 1
fi

if [ ! -x "$READSB_SOURCE_DIR/readsb" ]; then
    echo "❌ Compilation finished but the readsb executable was not created"
    exit 1
fi

if ! install -m 0755 "$READSB_SOURCE_DIR/readsb" "$READSB_BIN"; then
    echo "❌ Could not install the compiled readsb binary to $READSB_BIN"
    exit 1
fi

echo "✓ RTL-SDR-enabled readsb installed at: $READSB_BIN"
echo "  SpectrumSnek will prefer this binary over /usr/bin/readsb."

echo "SpectrumSnek setup complete!"
echo ""
echo "To start: ./spectrumsnek.sh"
echo ""
echo "Available tools:"
echo "  • RTL-SDR Spectrum Analyzer"
echo "  • ADS-B Aircraft Tracker"
echo "  • Traditional Radio Scanner"
echo "  • WiFi Network Selector"
echo "  • Bluetooth Device Connector"
echo "  • Audio Output Selector"
