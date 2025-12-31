#!/bin/bash
# Radio Tools Suite Uninstaller
# Removes the Radio Tools Suite and all its components

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="$SCRIPT_DIR/venv"
BOOT_SERVICE_NAME="radio-tools-loader"

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

echo "Radio Tools Suite Uninstaller"
echo "============================="

read -p "This will remove the Radio Tools Suite and all its components. Continue? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Uninstallation cancelled."
    exit 0
fi

# Get sudo command
get_sudo() {
    if [ "$EUID" -eq 0 ]; then
        echo ""
    else
        if command -v sudo &> /dev/null; then
            echo "sudo"
        else
            echo ""
        fi
    fi
}

SUDO_CMD=$(get_sudo)

# Remove boot service
if [ -f "/etc/systemd/system/$BOOT_SERVICE_NAME.service" ]; then
    print_info "Removing boot service..."
    $SUDO_CMD systemctl disable $BOOT_SERVICE_NAME.service 2>/dev/null || true
    $SUDO_CMD rm -f /etc/systemd/system/$BOOT_SERVICE_NAME.service
    $SUDO_CMD systemctl daemon-reload
    print_status "Boot service removed"
fi

# Remove udev rules
if [ -f "/etc/udev/rules.d/99-rtl-sdr.rules" ]; then
    print_info "Removing udev rules..."
    $SUDO_CMD rm -f /etc/udev/rules.d/99-rtl-sdr.rules
    $SUDO_CMD udevadm control --reload-rules 2>/dev/null || true
    print_status "Udev rules removed"
fi

# Remove desktop shortcut
DESKTOP_FILE="$HOME/.local/share/applications/radio-tools.desktop"
if [ -f "$DESKTOP_FILE" ]; then
    print_info "Removing desktop shortcut..."
    rm -f "$DESKTOP_FILE"
    print_status "Desktop shortcut removed"
fi

# Remove virtual environment
if [ -d "$VENV_DIR" ]; then
    print_info "Removing virtual environment..."
    rm -rf "$VENV_DIR"
    print_status "Virtual environment removed"
fi

# Remove generated files
print_info "Cleaning up generated files..."
rm -f rtl-sdr.rules
print_status "Cleanup completed"

echo
print_status "Radio Tools Suite successfully uninstalled!"
echo
echo "Note: System packages (RTL-SDR drivers, Python, etc.) were not removed."
echo "      You can remove them manually if desired."