#!/bin/bash
# SpectrumSnek Setup Script - Complete Installation

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
SYSTEM_PACKAGES="git build-essential python3-dev python3-venv python3-pip rtl-sdr libusb-1.0-0-dev pkg-config libncurses5-dev"
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

# Install ADS-B decoder
echo "Checking for ADS-B decoder..."

# Detect SDR type
sdr_type="unknown"
if command -v rtl_test &> /dev/null; then
    if timeout 10 rtl_test -t 2>&1 | grep -q "Found [0-9] device"; then
        sdr_type="rtlsdr"
        echo "RTL-SDR detected - will install compatible ADS-B decoder"
    fi
fi

if [ "$sdr_type" = "rtlsdr" ]; then
    # For RTL-SDR, prioritize dump1090-mutability for best compatibility
    if ! command -v dump1090-mutability &> /dev/null && ! command -v dump1090-fa &> /dev/null && ! command -v dump1090 &> /dev/null; then
        echo "Installing ADS-B decoder for RTL-SDR compatibility..."

        # Try installing dump1090-mutability first (best RTL-SDR support)
        if safe_apt_install dump1090-mutability; then
            echo "✓ ADS-B decoder (dump1090-mutability) installed for RTL-SDR"
        else
            echo "dump1090-mutability not available, trying dump1090-fa..."
            if safe_apt_install dump1090-fa; then
                echo "✓ ADS-B decoder (dump1090-fa) installed successfully"
            else
                # Try building dump1090 from source
                echo "Package installation failed, building from source..."
                if command -v git &> /dev/null && command -v make &> /dev/null; then
                    TEMP_DIR=$(mktemp -d)
                    cd "$TEMP_DIR"
                    if git clone https://github.com/antirez/dump1090.git >/dev/null 2>&1; then
                        cd dump1090
                        echo "Building dump1090..."
                        if gcc -I. dump1090.c anet.c -o dump1090 -lm -lpthread -lrtlsdr -lusb-1.0 -lncurses >/dev/null 2>&1; then
                            $SUDO_CMD cp dump1090 /usr/local/bin/ >/dev/null 2>&1
                            if command -v dump1090 &> /dev/null; then
                                echo "✓ ADS-B decoder (dump1090) built and installed from source"
                            else
                                echo "⚠ Build completed but dump1090 not found in PATH"
                            fi
                        else
                            echo "⚠ Failed to compile dump1090"
                        fi
                    else
                        echo "⚠ Failed to download dump1090 source"
                    fi
                    cd /
                    rm -rf "$TEMP_DIR"
                else
                    echo "⚠ git/make not available for source build"
                fi

                # Final check for successful installation
                if command -v dump1090-mutability &> /dev/null || command -v dump1090-fa &> /dev/null || command -v dump1090 &> /dev/null; then
                    echo "✓ ADS-B decoder installation completed successfully"
                else
                    echo "⚠ All automatic installation methods failed"
                    echo "ADS-B functionality will require manual decoder installation"
                fi
            fi
        fi
    else
        if command -v dump1090-mutability &> /dev/null; then
            echo "✓ RTL-SDR compatible ADS-B decoder (dump1090-mutability) already available"
        elif command -v dump1090-fa &> /dev/null; then
            echo "✓ RTL-SDR compatible ADS-B decoder (dump1090-fa) already available"
        else
            echo "✓ RTL-SDR compatible ADS-B decoder already available"
        fi
    fi
else
    # For other SDR types or unknown, install readsb
    if ! command -v readsb &> /dev/null; then
        echo "Installing readsb for general ADS-B compatibility..."
        safe_apt_install readsb

        if command -v readsb &> /dev/null; then
            echo "✓ ADS-B decoder (readsb) installed"
            echo "Note: readsb works best with dedicated ADS-B hardware"
        else
            echo "⚠ Failed to install ADS-B decoder"
        fi
    else
        echo "✓ ADS-B decoder already available"
    fi
fi

echo ""
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
