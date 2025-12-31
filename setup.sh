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
SERVICE_NAME="spectrum-service"
CONSOLE_SERVICE_NAME="spectrum-console"
ARCHITECTURE="console"  # console, headless, full
AUTOMATED=true

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
        # Debian/Ubuntu/Raspberry Pi OS
        OS="debian"
        RTLSDR_PKG="rtl-sdr"
        PYTHON_DEV_PKG="python3-dev python3-pip"
        PULSEAUDIO_PKG="pulseaudio pulseaudio-module-bluetooth alsa-utils"
        BLUEZ_PKG="bluez"
        BLUEZ_TOOLS_PKG="bluez-tools"
        BLUEZ_ALSA_PKG="bluez-alsa-utils"
        PORTAUDIO_PKG="portaudio19-dev"
        TMUX_PKG="tmux"
    elif [ -f /etc/redhat-release ]; then
        # RHEL/CentOS/Fedora
        OS="redhat"
        RTLSDR_PKG="rtl-sdr"
        PYTHON_DEV_PKG="python3-devel python3-pip"
        PULSEAUDIO_PKG="pulseaudio pulseaudio-module-bluetooth alsa-utils"
        BLUEZ_PKG="bluez"
        BLUEZ_TOOLS_PKG="bluez-tools"
        BLUEZ_ALSA_PKG="bluez-alsa"
        PORTAUDIO_PKG="portaudio-devel"
        TMUX_PKG="tmux"
    elif [ -f /etc/arch-release ]; then
        # Arch Linux
        OS="arch"
        RTLSDR_PKG="rtl-sdr"
        PYTHON_DEV_PKG="python python-pip"
        PULSEAUDIO_PKG="pulseaudio pulseaudio-bluetooth alsa-utils"
        BLUEZ_PKG="bluez"
        BLUEZ_TOOLS_PKG="bluez-tools"
        BLUEZ_ALSA_PKG="bluez-alsa"
        PORTAUDIO_PKG="portaudio"
        TMUX_PKG="tmux"
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
                $SUDO_CMD apt-get install -y $RTLSDR_PKG $PYTHON_DEV_PKG build-essential $PULSEAUDIO_PKG $BLUEZ_PKG $BLUEZ_TOOLS_PKG $BLUEZ_ALSA_PKG $PORTAUDIO_PKG $TMUX_PKG
                ;;
            redhat)
                $SUDO_CMD dnf install -y $RTLSDR_PKG $PYTHON_DEV_PKG gcc $PULSEAUDIO_PKG $BLUEZ_PKG $BLUEZ_TOOLS_PKG $BLUEZ_ALSA_PKG $PORTAUDIO_PKG $TMUX_PKG
                ;;
            arch)
                $SUDO_CMD pacman -S --noconfirm $RTLSDR_PKG $PYTHON_DEV_PKG base-devel $PULSEAUDIO_PKG $BLUEZ_PKG $BLUEZ_TOOLS_PKG $BLUEZ_ALSA_PKG $PORTAUDIO_PKG $TMUX_PKG
                ;;
        esac

        # Verify tmux installation
        if command -v tmux &> /dev/null; then
            print_status "tmux installed successfully"
            TMUX_AVAILABLE=true
        else
            print_warning "tmux installation failed - SpectrumSnek will run without tmux session management"
            TMUX_AVAILABLE=false
        fi

        if command -v rtl_test &> /dev/null; then
            print_status "RTL-SDR drivers installed successfully"
        else
            print_warning "RTL-SDR installation may have failed"
        fi
    else
        print_status "RTL-SDR drivers already installed"
    fi
}

# Function to repair tmux issues
repair_tmux() {
    print_info "Attempting to repair tmux installation..."

    if ! command -v tmux &> /dev/null; then
        print_info "Installing tmux..."
        SUDO_CMD=$(get_sudo)

        # Detect OS and install tmux
        if [ -f /etc/debian_version ]; then
            $SUDO_CMD apt-get update && $SUDO_CMD apt-get install -y tmux
        elif [ -f /etc/redhat-release ]; then
            $SUDO_CMD dnf install -y tmux
        elif [ -f /etc/arch-release ]; then
            $SUDO_CMD pacman -S --noconfirm tmux
        fi
    fi

    if command -v tmux &> /dev/null; then
        print_status "tmux is now available"
        TMUX_AVAILABLE=true
    else
        print_error "Failed to install tmux - manual installation may be required"
        TMUX_AVAILABLE=false
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

# Function to setup architecture-specific services
setup_architecture() {
    SUDO_CMD=$(get_sudo)

    case $ARCHITECTURE in
        console)
            print_info "Configuring Console Architecture..."
            setup_console_service
            ;;
        headless)
            print_info "Configuring Headless Architecture..."
            setup_headless_service
            ;;
        full)
            print_info "Configuring Full Architecture..."
            setup_console_service
            setup_headless_service
            ;;
    esac
}

# Function to setup console autologin and tmux
setup_console_service() {
    print_info "Setting up console autologin and tmux session..."

    SUDO_CMD=$(get_sudo)

    # Enable autologin on tty1
    $SUDO_CMD mkdir -p /etc/systemd/system/getty@tty1.service.d
    cat > /tmp/autologin.conf << EOF
[Service]
ExecStart=
ExecStart=-/sbin/agetty --autologin $USER --noclear %I \$TERM
EOF
    $SUDO_CMD mv /tmp/autologin.conf /etc/systemd/system/getty@tty1.service.d/autologin.conf

    # Create robust start script with error handling
    cat > /tmp/start_spectrum.sh << EOF
#!/bin/bash
# SpectrumSnek startup script with error handling

echo "Starting SpectrumSnek..."
cd $SCRIPT_DIR

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "ERROR: Virtual environment not found. Run ./setup.sh first."
    exit 1
fi

# Check if run_spectrum.sh exists
if [ ! -x "run_spectrum.sh" ]; then
    echo "ERROR: run_spectrum.sh not found or not executable."
    exit 1
fi

# Start SpectrumSnek with error handling
echo "Launching SpectrumSnek service..."
if ./run_spectrum.sh --service 2>&1; then
    echo "SpectrumSnek exited successfully"
else
    echo "ERROR: SpectrumSnek exited with error code $?"
    echo "Common issues:"
    echo "  - Missing dependencies: Run 'pip install -r requirements.txt'"
    echo "  - RTL-SDR not connected: Check USB devices with 'lsusb'"
    echo "  - Permission issues: Run 'sudo usermod -a -G plugdev $USER'"
    echo ""
    echo "To retry manually: ./run_spectrum.sh"
    echo "To exit: Press Ctrl+C"
    echo ""
    echo "Session will remain active for 60 seconds for troubleshooting..."
    sleep 60
fi
EOF
    chmod +x /tmp/start_spectrum.sh
    mv /tmp/start_spectrum.sh $HOME/start_spectrum.sh

    # Configure .bashrc for tmux with graceful fallback
    print_info "Configuring bashrc for SpectrumSnek session management..."

    # Remove any existing SpectrumSnek tmux configuration
    sed -i '/# SpectrumSnek tmux console setup/,/fi/d' "$HOME/.bashrc"

    # Add robust tmux configuration
    cat >> "$HOME/.bashrc" << 'EOF'

# SpectrumSnek session management - Robust tmux handling
if [[ -z "$TMUX" ]]; then
    if [[ "$(tty)" == "/dev/tty1" ]]; then
        # Console autologin - prefer tmux, fallback to direct execution
        if command -v tmux &> /dev/null; then
            if ! tmux has-session -t spectrum 2>/dev/null; then
                tmux new-session -s spectrum -d
                tmux send-keys -t spectrum "~/start_spectrum.sh" C-m
            fi
            exec tmux attach-session -t spectrum
        else
            echo "tmux not found, running SpectrumSnek directly on console..."
            ~/start_spectrum.sh
        fi
    elif [[ -n "$SSH_CLIENT" ]] || [[ -n "$SSH_TTY" ]]; then
        # SSH connection - run directly to avoid session drops
        echo "SpectrumSnek SSH Session - $(date)"
        echo "Running SpectrumSnek directly (no tmux for stability)"
        echo "Press Ctrl+C to exit"
        echo ""
        ~/start_spectrum.sh
        echo ""
        echo "SpectrumSnek session ended. Type 'exit' to close SSH connection."
    fi
            # For SSH, don't use exec - let user return to shell if tmux exits
            tmux attach-session -t spectrum || echo "Tmux session ended. Type 'exit' to close SSH connection."
        else
            echo "tmux not found, running SpectrumSnek directly via SSH..."
            ~/start_spectrum.sh || echo "SpectrumSnek exited. Type 'exit' to close SSH connection."
        fi
    fi
fi
EOF

    print_status "Bashrc configured with robust session management"

    $SUDO_CMD systemctl daemon-reload
    $SUDO_CMD systemctl restart getty@tty1

    print_status "Console autologin and tmux configured"
    print_info "Console will start SpectrumSnek on boot"
}

# Function to setup headless service
setup_headless_service() {
    print_info "Setting up headless service..."

    SUDO_CMD=$(get_sudo)

    # Create systemd service for spectrum service
    SERVICE_FILE="/etc/systemd/system/$SERVICE_NAME.service"

    cat > /tmp/$SERVICE_NAME.service << EOF
[Unit]
Description=SpectrumSnek Service 🐍📻
After=network.target bluetooth.service

[Service]
Type=simple
User=$USER
WorkingDirectory=$SCRIPT_DIR
ExecStart=$SCRIPT_DIR/venv/bin/python $SCRIPT_DIR/main.py --service
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

    if $SUDO_CMD mv /tmp/$SERVICE_NAME.service $SERVICE_FILE; then
        $SUDO_CMD systemctl daemon-reload
        $SUDO_CMD systemctl enable $SERVICE_NAME.service
        $SUDO_CMD systemctl start $SERVICE_NAME.service
        print_status "Headless service configured and started"
        print_info "Service running on http://localhost:5000"
        print_info "Web interfaces available for tools"
    else
        print_warning "Failed to create headless service"
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
        --console)
            ARCHITECTURE="console"
            shift
            ;;
        --headless)
            ARCHITECTURE="headless"
            shift
            ;;
        --full)
            ARCHITECTURE="full"
            shift
            ;;
        --no-system-deps)
            SKIP_SYSTEM_DEPS=true
            shift
            ;;
        --dev)
            DEV_MODE=true
            echo "  --dev                 Enable development mode (install dev dependencies)"
            ;;
        --repair-tmux)
            repair_tmux
            exit 0
            ;;
        --interactive)
            AUTOMATED=false
            shift
            ;;
        --help)
            print_header
            echo "SpectrumSnek Setup Script 🐍📻"
            echo ""
            echo "Usage: $0 [architecture] [options]"
            echo ""
            echo "Architectures:"
            echo "  --console         Interactive console mode (default)"
            echo "  --headless        Headless service mode (web/API access)"
            echo "  --full            Both console and headless modes"
            echo ""
            echo "Options:"
            echo "  --no-system-deps  Skip installation of system dependencies"
            echo "  --dev             Install development dependencies"
            echo "  --interactive     Prompt for configuration choices"
            echo "  --help            Show this help message"
            echo ""
            echo "Console Mode:"
            echo "  - Interactive menu on HDMI/console"
            echo "  - Autologin and tmux for session persistence"
            echo "  - SSH access to shared tmux session"
            echo ""
            echo "Headless Mode:"
            echo "  - Background service with REST API"
            echo "  - Web interface access"
            echo "  - No console UI, remote control only"
            echo ""
            echo "Full Mode:"
            echo "  - Both console and headless features"
            echo "  - Complete SpectrumSnek experience"
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

    case $ARCHITECTURE in
        console)
            print_info "Setting up Console Architecture (Interactive HDMI/SSH)"
            ;;
        headless)
            print_info "Setting up Headless Architecture (Service + Web)"
            ;;
        full)
            print_info "Setting up Full Architecture (Console + Headless)"
            ;;
    esac

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

    # Upgrade pip and setuptools using venv python
    print_info "Upgrading pip and setuptools..."
    "$VENV_DIR/bin/python" -m pip install --upgrade pip setuptools
    print_status "Pip and setuptools upgraded"

    # Install Python dependencies
    print_info "Installing Python dependencies..."
    "$VENV_DIR/bin/python" -m pip install -r "$SCRIPT_DIR/requirements.txt"
    print_status "Python dependencies installed"

    # Install development dependencies if requested
    if [ "$DEV_MODE" = true ]; then
        print_info "Installing development dependencies..."
        "$VENV_DIR/bin/python" -m pip install -r "$SCRIPT_DIR/requirements-dev.txt"
        print_status "Development dependencies installed"
    fi

    # Setup udev rules and permissions
    setup_udev_rules

    # Enable Bluetooth service
    print_info "Enabling Bluetooth service..."
    SUDO_CMD=$(get_sudo)
    if $SUDO_CMD systemctl enable bluetooth.service 2>/dev/null; then
        $SUDO_CMD systemctl start bluetooth.service 2>/dev/null
        print_status "Bluetooth service enabled"
    else
        print_warning "Failed to enable Bluetooth service"
    fi

    # Setup architecture-specific configuration
    setup_architecture

    # Create desktop shortcut (for console/headless with desktop)
    if [ "$ARCHITECTURE" != "headless" ]; then
        create_desktop_shortcut
    fi

    # Virtual environment commands completed

    # Final summary
    echo ""
    print_status "SpectrumSnek setup completed! 🐍📻"
    echo ""
    echo "Architecture: $ARCHITECTURE"
    echo ""

    case $ARCHITECTURE in
        console)
            echo "Console Mode Setup:"
            echo "  • Autologin configured on tty1"
            echo "  • tmux session for HDMI/SSH access"
            echo "  • Reboot to activate console menu"
            echo ""
            echo "SSH Access:"
            echo "  • ssh user@hostname (attaches to tmux session)"
            ;;
        headless)
            echo "Headless Mode Setup:"
            echo "  • Service running: $SERVICE_NAME"
            echo "  • API available: http://localhost:5000"
            echo "  • Web interfaces for all tools"
            echo ""
            echo "Remote Access:"
            echo "  • Web UI: http://hostname:5000 (if port forwarded)"
            echo "  • API: http://hostname:5000/api/"
            ;;
        full)
            echo "Full Mode Setup:"
            echo "  • Console autologin + tmux on tty1"
            echo "  • Background service for web access"
            echo "  • Complete local and remote access"
            echo ""
            echo "Access Methods:"
            echo "  • HDMI: Automatic menu on boot"
            echo "  • SSH: Shared tmux session"
            echo "  • Web: http://localhost:5000"
            ;;
    esac

    echo ""
    echo "Available tools:"
    echo "  • RTL-SDR Spectrum Analyzer"
    echo "  • ADS-B Aircraft Tracker"
    echo "  • Traditional Radio Scanner"
    echo "  • WiFi Network Selector"
    echo "  • Bluetooth Device Connector"
    echo "  • Audio Output Selector"
    echo ""

    if [ "$EUID" -ne 0 ]; then
        echo "Note: Some features may require sudo for hardware access"
        echo "Run 'sudo ./setup.sh' if you encounter permission issues"
    fi
        echo ""

    echo "Usage:"
    echo "  • Interactive: ./run_spectrum.sh"
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

# Virtual environment commands completed

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