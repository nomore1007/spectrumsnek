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
    print_info "Repairing tmux installation and recreating scripts..."

    # Install tmux if missing
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

    # Recreate the SSH scripts
    create_ssh_scripts
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

    # Create robust start script with comprehensive logging
    cat > /tmp/start_spectrum.sh << EOF
#!/bin/bash
# SpectrumSnek startup script with comprehensive error logging

LOG_FILE="\$HOME/spectrum_startup.log"
echo "=== SpectrumSnek Startup Log - \$(date) ===" >> "\$LOG_FILE"
echo "Starting SpectrumSnek client..." | tee -a "\$LOG_FILE"
cd $SCRIPT_DIR
echo "Working directory: \$(pwd)" >> "\$LOG_FILE"

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "ERROR: Virtual environment not found. Run ./setup.sh first." | tee -a "\$LOG_FILE"
    exit 1
fi
echo "✓ Virtual environment found" >> "\$LOG_FILE"

# Check if run_spectrum.sh exists
if [ ! -x "run_spectrum.sh" ]; then
    echo "ERROR: run_spectrum.sh not found or not executable." | tee -a "\$LOG_FILE"
    ls -la run_spectrum.sh >> "\$LOG_FILE" 2>&1
    exit 1
fi
echo "✓ run_spectrum.sh is executable" >> "\$LOG_FILE"

# Launch client (connects to service, doesn't start it)
echo "Launching SpectrumSnek client interface..." | tee -a "\$LOG_FILE"
echo "Command: ./run_spectrum.sh" >> "\$LOG_FILE"
echo "Note: This connects to the running service, it does not start one" >> "\$LOG_FILE"

if ./run_spectrum.sh 2>&1 | tee -a "\$LOG_FILE"; then
    echo "SpectrumSnek client exited successfully" | tee -a "\$LOG_FILE"
else
    EXIT_CODE=\$?
    echo "SpectrumSnek client exited with code \$EXIT_CODE" | tee -a "\$LOG_FILE"
    echo "This is normal when the client interface closes" | tee -a "\$LOG_FILE"
fi

echo "=== End Client Log ===" >> "\$LOG_FILE"
echo "Client log saved to: \$LOG_FILE"
EOF
    chmod +x /tmp/start_spectrum.sh
    mv /tmp/start_spectrum.sh $HOME/start_spectrum.sh

    # Create ultra-simple SSH test script
    print_info "Creating minimal SSH test script..."

    cat > "$HOME/spectrum_test.sh" << 'EOF'
#!/bin/bash
# Minimal test script to isolate SSH issues

LOG_FILE="$HOME/spectrum_debug.log"
echo "=== SSH Test - $(date) ===" > "$LOG_FILE"
echo "Script started successfully" >> "$LOG_FILE"
echo "PID: $$" >> "$LOG_FILE"
echo "User: $(whoami)" >> "$LOG_FILE"
echo "Working directory: $(pwd)" >> "$LOG_FILE"
echo "Home directory: $HOME" >> "$LOG_FILE"

echo "========================================"
echo "  SpectrumSnek SSH Test"
echo "  $(date)"
echo "========================================"
echo ""
echo "If you can see this, basic SSH is working!"
echo "Log file: $LOG_FILE"
echo ""

# Test basic commands
echo "Testing basic commands..." >> "$LOG_FILE"
which python3 >> "$LOG_FILE" 2>&1
echo "Python3 exit code: $?" >> "$LOG_FILE"

ls -la ~/spectrumsnek/ >> "$LOG_FILE" 2>&1
echo "Directory list exit code: $?" >> "$LOG_FILE"

echo "Test script completed successfully" >> "$LOG_FILE"
echo ""
echo "Test completed. Check $LOG_FILE for details."
echo "Press Enter to continue..."
read
EOF

    chmod +x "$HOME/spectrum_test.sh"
    print_status "Test script created at ~/spectrum_test.sh"

    # Create the full SSH script
    print_info "Creating full SSH entry point..."

    cat > "$HOME/spectrum_ssh.sh" << 'EOF'
#!/bin/bash
# SpectrumSnek SSH Entry Point with fail-safe logging

# Create log file immediately
LOG_FILE="$HOME/spectrum_ssh.log"
exec > >(tee -a "$LOG_FILE") 2>&1
echo "=== SpectrumSnek SSH Session - $(date) ==="

echo "========================================"
echo "  SpectrumSnek SSH Session"
echo "  $(date)"
echo "========================================"
echo ""
echo "All output is being logged to: $LOG_FILE"
echo ""

# Basic system check
echo "System check:"
echo "User: $(whoami)"
echo "PID: $$"
echo "Working directory: $(pwd)"
echo "Home: $HOME"
echo ""

# Check if we can access SpectrumSnek directory
if cd ~/spectrumsnek 2>/dev/null; then
    echo "✓ Can access ~/spectrumsnek"
    echo "Directory contents:"
    ls -la
    echo ""
else
    echo "✗ Cannot access ~/spectrumsnek directory"
    echo "This might be the issue!"
    echo ""
    echo "Log saved to: $LOG_FILE"
    exit 1
fi

# Check virtual environment
if [ -d "venv" ]; then
    echo "✓ Virtual environment exists"
else
    echo "✗ Virtual environment missing"
    echo "Run: ./setup.sh --full"
fi

# Check run script
if [ -x "run_spectrum.sh" ]; then
    echo "✓ run_spectrum.sh is executable"
else
    echo "✗ run_spectrum.sh missing or not executable"
    ls -la run_spectrum.sh
fi

echo ""
echo "Attempting to start SpectrumSnek..."
echo "(If this fails, check $LOG_FILE for details)"
echo ""

# Try to run SpectrumSnek
if ~/start_spectrum.sh; then
    echo "SpectrumSnek completed successfully"
else
    EXIT_CODE=$?
    echo ""
    echo "SpectrumSnek failed with exit code: $EXIT_CODE"
    echo "Full error details in: $LOG_FILE"
    echo ""
    echo "You can still troubleshoot:"
    echo "  ./run_spectrum.sh     - Manual start"
    echo "  cat $LOG_FILE         - View full logs"
    echo "  pip list             - Check packages"
fi

echo ""
echo "=== Session End ==="
echo "Log file: $LOG_FILE"
EOF

    chmod +x "$HOME/spectrum_ssh.sh"
    print_status "SSH scripts created with comprehensive logging"

    # Configure .bashrc for console only (much simpler)
    print_info "Configuring bashrc for console autologin..."

    # Remove any existing SpectrumSnek configuration
    sed -i '/# SpectrumSnek/,/fi/d' "$HOME/.bashrc"

    # Add SpectrumSnek configuration
    cat >> "$HOME/.bashrc" << 'EOF'

# SpectrumSnek autologin configuration
if [[ -z "$TMUX" ]]; then
    # Console autologin (tty1)
    if [[ "$(tty)" == "/dev/tty1" ]]; then
        if command -v tmux &> /dev/null; then
            tmux has-session -t spectrum 2>/dev/null || tmux new-session -s spectrum -d ~/start_spectrum.sh
            exec tmux attach-session -t spectrum
        else
            ~/start_spectrum.sh
        fi
EOF

    # Add SSH autologin if enabled
    if [[ "${SSH_AUTOLOGIN:-false}" == "true" ]]; then
        cat >> "$HOME/.bashrc" << 'EOF'
    # SSH autologin
    elif [[ -n "$SSH_CLIENT" ]] || [[ -n "$SSH_TTY" ]]; then
        if command -v tmux &> /dev/null; then
            tmux has-session -t spectrum 2>/dev/null || tmux new-session -s spectrum -d ~/start_spectrum.sh
            exec tmux attach-session -t spectrum
        else
            ~/start_spectrum.sh
        fi
EOF
    fi

    cat >> "$HOME/.bashrc" << 'EOF'
    fi
fi
EOF

    print_status "Console autologin configured"

    $SUDO_CMD systemctl daemon-reload
    $SUDO_CMD systemctl restart getty@tty1

    print_status "Console autologin and tmux configured"
    print_info "Console will start SpectrumSnek on boot"
}

# Function to create SSH diagnostic scripts
create_ssh_scripts() {
    # Create ultra-simple SSH test script
    cat > "$HOME/spectrum_test.sh" << 'EOF'
#!/bin/bash
# Minimal test script to isolate SSH issues

LOG_FILE="$HOME/spectrum_debug.log"
echo "=== SSH Test - $(date) ===" > "$LOG_FILE"
echo "Script started successfully" >> "$LOG_FILE"
echo "PID: $$" >> "$LOG_FILE"
echo "User: $(whoami)" >> "$LOG_FILE"
echo "Working directory: $(pwd)" >> "$LOG_FILE"
echo "Home directory: $HOME" >> "$LOG_FILE"

echo "========================================"
echo "  SpectrumSnek SSH Test"
echo "  $(date)"
echo "========================================"
echo ""
echo "If you can see this, basic SSH is working!"
echo "Log file: $LOG_FILE"
echo ""

# Test basic commands
echo "Testing basic commands..." >> "$LOG_FILE"
which python3 >> "$LOG_FILE" 2>&1
echo "Python3 exit code: $?" >> "$LOG_FILE"

ls -la ~/spectrumsnek/ >> "$LOG_FILE" 2>&1
echo "Directory list exit code: $?" >> "$LOG_FILE"

echo "Test script completed successfully" >> "$LOG_FILE"
echo ""
echo "Test completed. Check $LOG_FILE for details."
echo "Press Enter to continue..."
read
EOF

    chmod +x "$HOME/spectrum_test.sh"

    # Create the full SSH script
    cat > "$HOME/spectrum_ssh.sh" << 'EOF'
#!/bin/bash
# SpectrumSnek SSH Entry Point with service detection

# Create log file immediately
LOG_FILE="$HOME/spectrum_ssh.log"
exec > >(tee -a "$LOG_FILE") 2>&1
echo "=== SpectrumSnek SSH Session - $(date) ==="

echo "========================================"
echo "  SpectrumSnek SSH Session"
echo "  $(date)"
echo "========================================"
echo ""
echo "All output is being logged to: $LOG_FILE"
echo ""

# Check if SpectrumSnek service is already running
echo "Checking for existing SpectrumSnek service..."
if systemctl is-active --quiet spectrum-service 2>/dev/null; then
    echo "✓ SpectrumSnek service is running"
    SERVICE_RUNNING=true

    # Try to connect to the service
    if curl -s http://localhost:5000/api/status >/dev/null 2>&1; then
        echo "✓ Service is responding on port 5000"
        echo ""
        echo "Opening SpectrumSnek web interface..."
        echo "Access at: http://localhost:5000"
        echo ""
        echo "To access from another computer:"
        echo "http://YOUR_PI_IP:5000"
        echo ""
        echo "Available tools:"
        curl -s http://localhost:5000/api/tools | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    for name, info in data.get('tools', {}).items():
        status = info.get('status', 'unknown')
        desc = info.get('info', {}).get('description', 'No description')
        print(f'  • {name}: {desc} ({status})')
except:
    print('  Could not retrieve tool list')
"
        echo ""
        echo "Press Enter to exit SSH session..."
        read
        echo "=== SSH Session End ==="
        exit 0
    else
        echo "⚠ Service is running but not responding on port 5000"
        echo "This might indicate a service issue."
    fi
else
    echo "ℹ SpectrumSnek service is not running"
    SERVICE_RUNNING=false
fi

echo ""

# Basic system check
echo "System check:"
echo "User: $(whoami)"
echo "PID: $$"
echo "Working directory: $(pwd)"
echo "Home: $HOME"
echo ""

# Check if we can access SpectrumSnek directory
if cd ~/spectrumsnek 2>/dev/null; then
    echo "✓ Can access ~/spectrumsnek"
    echo "Directory contents:"
    ls -la
    echo ""
else
    echo "✗ Cannot access ~/spectrumsnek directory"
    echo "This might be the issue!"
    echo ""
    echo "Log saved to: $LOG_FILE"
    exit 1
fi

# Check virtual environment
if [ -d "venv" ]; then
    echo "✓ Virtual environment exists"
else
    echo "✗ Virtual environment missing"
    echo "Run: ./setup.sh --full"
fi

# Check run script
if [ -x "run_spectrum.sh" ]; then
    echo "✓ run_spectrum.sh is executable"
else
    echo "✗ run_spectrum.sh missing or not executable"
    ls -la run_spectrum.sh
fi

echo ""
if [ "$SERVICE_RUNNING" = true ]; then
    echo "Service appears to have issues. Attempting to restart SpectrumSnek..."
else
    echo "Attempting to start SpectrumSnek..."
fi
echo "(If this fails, check $LOG_FILE for details)"
echo ""

# Try to run SpectrumSnek
if ~/start_spectrum.sh; then
    echo "SpectrumSnek completed successfully"
else
    EXIT_CODE=$?
    echo ""
    echo "SpectrumSnek failed with exit code: $EXIT_CODE"
    echo "Full error details in: $LOG_FILE"
    echo ""
    echo "Troubleshooting options:"
    if [ "$SERVICE_RUNNING" = true ]; then
        echo "  Service is running but unresponsive:"
        echo "  sudo systemctl restart spectrum-service"
    fi
    echo "  ./run_spectrum.sh     - Manual start attempt"
    echo "  cat $LOG_FILE         - View full error logs"
    echo "  ./check_port.sh       - Check port conflicts"
    echo "  pip list             - Check installed packages"
fi

echo ""
echo "=== Session End ==="
echo "Log file: $LOG_FILE"
EOF

    chmod +x "$HOME/spectrum_ssh.sh"
    print_status "SSH diagnostic scripts created"
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
ExecStart=$SCRIPT_DIR/venv/bin/python $SCRIPT_DIR/main.py --service --host 0.0.0.0 --port 5000
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
        --ssh-autologin)
            SSH_AUTOLOGIN=true
            echo "  --ssh-autologin       Enable tmux autologin for SSH connections"
            ;;
        --repair-tmux)
            repair_tmux
            exit 0
            ;;
        --ssh-autologin)
            SSH_AUTOLOGIN=true
            shift
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
            if [[ "${SSH_AUTOLOGIN:-false}" == "true" ]]; then
                print_info "SSH autologin enabled - tmux will start automatically on SSH connections"
            fi
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

    # Configure firewall for web access
    print_info "Configuring firewall for web access..."
    if command -v ufw &> /dev/null; then
        # UFW firewall
        if $SUDO_CMD ufw status | grep -q "Status: active"; then
            $SUDO_CMD ufw allow 5000/tcp 2>/dev/null && print_status "UFW firewall configured for port 5000"
        else
            print_info "UFW firewall is not active - SpectrumSnek web interface may not be accessible remotely"
        fi
    elif command -v firewall-cmd &> /dev/null; then
        # Firewalld
        if $SUDO_CMD firewall-cmd --state 2>/dev/null | grep -q "running"; then
            $SUDO_CMD firewall-cmd --permanent --add-port=5000/tcp 2>/dev/null && \
            $SUDO_CMD firewall-cmd --reload 2>/dev/null && \
            print_status "Firewalld configured for port 5000"
        else
            print_info "Firewalld is not running - SpectrumSnek web interface may not be accessible remotely"
        fi
    else
        # Try iptables directly
        if command -v iptables &> /dev/null; then
            $SUDO_CMD iptables -C INPUT -p tcp --dport 5000 -j ACCEPT 2>/dev/null || \
            $SUDO_CMD iptables -A INPUT -p tcp --dport 5000 -j ACCEPT 2>/dev/null && \
            print_status "IPTables configured for port 5000"
        else
            print_warning "No firewall management tool found - manual firewall configuration may be required"
            print_warning "To allow remote access: iptables -A INPUT -p tcp --dport 5000 -j ACCEPT"
        fi
    fi
        print_status "Bluetooth service enabled"
    else
        print_warning "Failed to enable Bluetooth service"
    fi

    # Setup architecture-specific configuration
    setup_architecture

    # Always create SSH diagnostic scripts
    print_info "Creating SSH diagnostic scripts..."
    create_ssh_scripts

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
            if [[ "${SSH_AUTOLOGIN:-false}" == "true" ]]; then
                echo "  • SSH autologin configured"
            fi
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
            echo "  • SSH: Run '~/spectrum_ssh.sh' for stable access"
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