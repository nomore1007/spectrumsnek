#!/bin/bash
# Install RTL-SDR udev rules for proper device access

echo "Installing RTL-SDR udev rules..."

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo "Please run this script with sudo:"
    echo "sudo $0"
    exit 1
fi

# Copy udev rules to /etc/udev/rules.d/
cp rtl-sdr.rules /etc/udev/rules.d/99-rtl-sdr.rules

# Reload udev rules
udevadm control --reload-rules
udevadm trigger

echo "RTL-SDR udev rules installed successfully!"
echo "Please unplug and re-plug your RTL-SDR device, or reboot your system."
echo ""
echo "You can verify the installation by running:"
echo "ls -la /dev/rtl_sdr"