#!/bin/bash
# SpectrumSnek Setup Script
# Comprehensive installation and configuration script for SpectrumSnek 🐍📻
# Features:
# - Python virtual environment setup
# - Dependency installation
# - RTL-SDR driver and permissions setup
# - Optional boot-time startup configuration

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="$SCRIPT_DIR/venv"
DEV_MODE=false
BOOT_SERVICE_NAME="radio-tools-loader"
BOOT_ENABLED=false

# Function to print colored output
print_status() {
    echo -e "${GREEN}✓${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

print_info() {
    echo -e "${BLUE}ℹ${NC} $1"
}

print_header() {
    echo -e "${BLUE}================================================${NC}"
    echo -e "${BLUE}  Radio Tools Suite Setup${NC}"
    echo -e "${BLUE}================================================${NC}"
}

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

# Function to install system dependencies
install_system_deps() {
    if [ "${SKIP_SYSTEM_DEPS:-false}" = true ]; then
        print_info "Skipping system dependency installation (--no-system-deps)"
        return
    fi

    print_info "Checking system dependencies..."

    # Detect OS
    if [ -f /etc/debian_version ]; then
        # Debian/Ubuntu
        OS="debian"
        RTLSDR_PKG="rtl-sdr"
        PYTHON_DEV_PKG="python3-dev"
    elif [ -f /etc/redhat-release ]; then
        # RHEL/CentOS/Fedora
        OS="redhat"
        RTLSDR_PKG="rtl-sdr"
        PYTHON_DEV_PKG="python3-devel"
    elif [ -f /etc/arch-release ]; then
        # Arch Linux
        OS="arch"
        RTLSDR_PKG="rtl-sdr"
        PYTHON_DEV_PKG="python"
    else
        print_warning "Unknown OS, skipping system dependency installation"
        return
    fi

    # Check if RTL-SDR is installed
    if ! command -v rtl_test &> /dev/null; then
        print_info "Installing RTL-SDR drivers..."
        SUDO_CMD=$(get_sudo)

        case $OS in
            debian)
                $SUDO_CMD apt-get update
                $SUDO_CMD apt-get install -y $RTLSDR_PKG $PYTHON_DEV_PKG build-essential
                ;;
            redhat)
                $SUDO_CMD dnf install -y $RTLSDR_PKG $PYTHON_DEV_PKG gcc
                ;;
            arch)
                $SUDO_CMD pacman -S --noconfirm $RTLSDR_PKG $PYTHON_DEV_PKG base-devel
                ;;
        esac

        if command -v rtl_test &> /dev/null; then
            print_status "RTL-SDR drivers installed successfully"
        else
            print_warning "RTL-SDR installation may have failed"
        fi
    else
        print_status "RTL-SDR drivers already installed"
    fi
}

# Function to setup udev rules
setup_udev_rules() {
    print_info "Setting up RTL-SDR device permissions..."

    if [ ! -f "$SCRIPT_DIR/rtl-sdr.rules" ]; then
        print_warning "rtl-sdr.rules file not found, creating it..."
        cat > "$SCRIPT_DIR/rtl-sdr.rules" << 'EOF'
# RTL-SDR udev rules for device access
SUBSYSTEMS=="usb", ATTRS{idVendor}=="0bda", ATTRS{idProduct}=="2838", MODE:="0666", SYMLINK+="rtl_sdr"
SUBSYSTEMS=="usb", ATTRS{idVendor}=="0bda", ATTRS{idProduct}=="2832", MODE:="0666", SYMLINK+="rtl_sdr"
EOF
    fi

    SUDO_CMD=$(get_sudo)

    # Install udev rules
    if $SUDO_CMD cp "$SCRIPT_DIR/rtl-sdr.rules" /etc/udev/rules.d/99-rtl-sdr.rules 2>/dev/null; then
        print_status "Udev rules installed"
    else
        print_warning "Failed to install udev rules (may need manual installation)"
    fi

    # Add user to plugdev group
    if $SUDO_CMD usermod -a -G plugdev $USER 2>/dev/null; then
        print_status "User added to plugdev group"
        print_info "Note: You may need to log out and back in for group changes to take effect"
    else
        print_warning "Failed to add user to plugdev group"
    fi

    # Reload udev rules
    if $SUDO_CMD udevadm control --reload-rules 2>/dev/null && $SUDO_CMD udevadm trigger 2>/dev/null; then
        print_status "Udev rules reloaded"
    else
        print_warning "Failed to reload udev rules"
    fi
}

# Function to create systemd service for boot startup
create_boot_service() {
    if [ "$BOOT_ENABLED" = true ]; then
        print_info "Setting up boot-time startup..."

        SUDO_CMD=$(get_sudo)

        # Create systemd service file
        SERVICE_FILE="/etc/systemd/system/$BOOT_SERVICE_NAME.service"

        cat > /tmp/$BOOT_SERVICE_NAME.service << EOF
[Unit]
Description=SpectrumSnek Radio Tools Loader 🐍📻
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$SCRIPT_DIR
ExecStart=$SCRIPT_DIR/venv/bin/python $SCRIPT_DIR/main.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

        if $SUDO_CMD mv /tmp/$BOOT_SERVICE_NAME.service $SERVICE_FILE; then
            $SUDO_CMD systemctl daemon-reload
            $SUDO_CMD systemctl enable $BOOT_SERVICE_NAME.service
            print_status "Boot service created and enabled"
            print_info "The Radio Tools Loader will start automatically on boot"
        else
            print_warning "Failed to create boot service"
        fi
    fi
}

# Function to create desktop shortcut (optional)
create_desktop_shortcut() {
    print_info "Creating desktop shortcut..."

    DESKTOP_FILE="$HOME/.local/share/applications/radio-tools.desktop"

    mkdir -p "$(dirname "$DESKTOP_FILE")"

    cat > "$DESKTOP_FILE" << EOF
[Desktop Entry]
Name=SpectrumSnek
Comment=Python-powered radio spectrum analysis toolkit 🐍📻
Exec=$SCRIPT_DIR/venv/bin/python $SCRIPT_DIR/main.py
Icon=applications-system
Terminal=true
Type=Application
Categories=Utility;HamRadio;
EOF

    chmod +x "$DESKTOP_FILE"
    print_status "Desktop shortcut created"
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --boot)
            BOOT_ENABLED=true
            shift
            ;;
        --no-system-deps)
            SKIP_SYSTEM_DEPS=true
            shift
            ;;
        --dev)
            DEV_MODE=true
            shift
            ;;
        --help)
            echo "SpectrumSnek Setup Script 🐍📻"
            echo ""
            echo "Usage: $0 [options]"
            echo ""
            echo "Options:"
            echo "  --boot            Enable boot-time startup of the loader"
            echo "  --no-system-deps  Skip installation of system dependencies"
            echo "  --dev             Install development dependencies (pytest, flake8, etc.)"
            echo "  --help            Show this help message"
            echo ""
            echo "This script will:"
            echo "  - Create a Python virtual environment"
            echo "  - Install system dependencies (RTL-SDR, etc.)"
            echo "  - Install Python dependencies"
            echo "  - Set up RTL-SDR device permissions"
            echo "  - Create desktop shortcuts"
            echo "  - Optionally configure boot-time startup"
            echo ""
            echo "Uninstallation: ./uninstall.sh"
            exit 0
            ;;
        *)
            print_error "Unknown option: $1"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

# Main setup process
main() {
    print_header

    if [ "$BOOT_ENABLED" = true ]; then
        print_info "Boot-time startup will be configured"
    fi

    # Check Python
    if ! command -v python3 &> /dev/null; then
        print_error "Python 3 is required but not found"
        exit 1
    fi
    print_status "Python 3 found"

    # Install system dependencies
    install_system_deps

    # Create virtual environment
    print_info "Setting up Python virtual environment..."
    if [ ! -d "$VENV_DIR" ]; then
        python3 -m venv "$VENV_DIR"
        print_status "Virtual environment created"
    else
        print_status "Virtual environment already exists"
    fi

    # Activate virtual environment
    source "$VENV_DIR/bin/activate"

    # Upgrade pip
    print_info "Upgrading pip..."
    pip install --upgrade pip
    print_status "Pip upgraded"

    # Install Python dependencies
    print_info "Installing Python dependencies..."
    pip install -r "$SCRIPT_DIR/requirements.txt"
    print_status "Python dependencies installed"

    # Install development dependencies if requested
    if [ "$DEV_MODE" = true ]; then
        print_info "Installing development dependencies..."
        pip install -r "$SCRIPT_DIR/requirements-dev.txt"
        print_status "Development dependencies installed"
    fi

    # Setup udev rules and permissions
    setup_udev_rules

    # Create boot service if requested
    create_boot_service

    # Create desktop shortcut
    create_desktop_shortcut

    # Deactivate virtual environment
    deactivate

    # Final summary
    echo ""
    print_status "SpectrumSnek setup completed! 🐍📻"
    echo ""
    echo "Available tools:"
    echo "  • RTL-SDR Scanner - Full radio spectrum analysis"
    echo "  • ADS-B Aircraft Tracker - Real-time aircraft surveillance"
    echo "  • Spectrum Analyzer (Demo) - Basic spectrum demonstration"
    echo ""

    if [ "$BOOT_ENABLED" = true ]; then
        echo "Boot configuration:"
        echo "  • Service: $BOOT_SERVICE_NAME"
        echo "  • Status: $(systemctl is-enabled $BOOT_SERVICE_NAME 2>/dev/null || echo 'unknown')"
        echo ""
    fi

    echo "Usage:"
    echo "  • Interactive: python main.py"
    echo "  • Direct RTL-SDR: ./run_scanner.sh --interactive --freq 100"
    echo "  • Direct ADS-B: python -m adsb_tool.adsb_tracker --freq 1090"
    echo ""

    if [ "$EUID" -ne 0 ]; then
        echo "Note: Some features may require running with sudo for hardware access"
        echo "Run 'sudo ./setup.sh' if you encounter permission issues"
    fi
}

# Run main setup
main "$@"

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip

# Install dependencies
echo "Installing Python dependencies..."
pip install -r requirements.txt

# Check if RTL-SDR drivers are installed
echo "Checking for RTL-SDR drivers..."
if ! command -v rtl_test &> /dev/null; then
    echo "Warning: rtl_test command not found."
    echo "Please install RTL-SDR drivers:"
    echo "  Ubuntu/Debian: sudo apt-get install rtl-sdr"
    echo "  Fedora/CentOS: sudo dnf install rtl-sdr"
    echo "  macOS: brew install rtl-sdr"
    echo "  Windows: Use Zadig to install WinUSB drivers"
else
    echo "RTL-SDR drivers found."
fi

# Install RTL-SDR udev rules and setup user permissions
echo "Setting up RTL-SDR device permissions..."

# Check if running as root
if [ "$EUID" -eq 0 ]; then
    # Running as root, no need for sudo
    SUDO=""
else
    # Not running as root, check if sudo is available
    if command -v sudo &> /dev/null; then
        SUDO="sudo"
        echo "Requesting sudo permissions for device setup..."
    else
        echo "Warning: sudo not available and not running as root."
        echo "You may need to manually install udev rules and add user to plugdev group."
        SUDO=""
    fi
fi

# Install udev rules
if [ -f "rtl-sdr.rules" ]; then
    echo "Installing udev rules..."
    $SUDO cp rtl-sdr.rules /etc/udev/rules.d/99-rtl-sdr.rules 2>/dev/null
    if [ $? -eq 0 ]; then
        echo "✓ Udev rules installed successfully"
    else
        echo "⚠ Failed to install udev rules (may require manual installation)"
    fi
else
    echo "⚠ rtl-sdr.rules file not found, skipping udev rules installation"
fi

# Add user to plugdev group
echo "Adding user to plugdev group..."
$SUDO usermod -a -G plugdev $USER 2>/dev/null
if [ $? -eq 0 ]; then
    echo "✓ User added to plugdev group"
    echo "  Note: You may need to log out and back in for group changes to take effect"
else
    echo "⚠ Failed to add user to plugdev group (may require manual setup)"
fi

# Reload udev rules
echo "Reloading udev rules..."
$SUDO udevadm control --reload-rules 2>/dev/null
$SUDO udevadm trigger 2>/dev/null
if [ $? -eq 0 ]; then
    echo "✓ Udev rules reloaded"
else
    echo "⚠ Failed to reload udev rules (may require manual reload)"
fi

echo ""
echo "Setup complete!"
echo ""
echo "Next steps:"
echo "1. If RTL-SDR hardware is connected, unplug and re-plug it"
echo "2. Log out and back in (or reboot) for group changes to take effect"
echo "3. Test the setup: ./test_setup.sh"
echo ""
echo "To run the scanner:"
echo "  ./run_scanner.sh --freq 100 --mode spectrum"
echo ""
echo "For demo mode (no hardware required):"
echo "  ./run_scanner.sh --demo --freq 100 --mode spectrum"
echo ""
echo "For help:"
echo "  ./run_scanner.sh --help"

# Deactivate virtual environment
deactivate

echo ""
echo "Setup Summary:"
echo "- ✓ Virtual environment created/updated"
echo "- ✓ Python dependencies installed"
echo "- ✓ RTL-SDR drivers checked"
echo "- ⚠ Device permissions setup attempted (may require manual completion)"
echo ""
echo "If you see permission warnings above, run:"
echo "  sudo ./install_udev_rules.sh"
echo "  sudo usermod -a -G plugdev \$USER"
echo "Then log out and back in (or reboot)"