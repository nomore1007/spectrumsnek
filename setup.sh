#!/bin/bash
# SpectrumSnek Setup Script - Self-Sustaining Version

echo "SpectrumSnek Setup"
echo "=================="
echo ""
echo "Setting up SpectrumSnek radio analysis toolkit..."
echo ""

# Install ADS-B decoder from source if not available
echo "Checking for ADS-B decoder..."
if ! command -v dump1090-mutability &> /dev/null && ! command -v dump1090-fa &> /dev/null && ! command -v dump1090 &> /dev/null; then
    echo "ADS-B decoder not found, building from source..."

    # Install build dependencies
    sudo apt update >/dev/null 2>&1
    sudo apt install -y build-essential git librtlsdr-dev libusb-1.0-0-dev pkg-config >/dev/null 2>&1

    # Build dump1090 from antirez repo
    TEMP_DIR=$(mktemp -d)
    cd "$TEMP_DIR"
    if git clone https://github.com/antirez/dump1090.git >/dev/null 2>&1; then
        cd dump1090
        if gcc -I. dump1090.c anet.c -o dump1090 -lm -lpthread -lrtlsdr -lusb-1.0 >/dev/null 2>&1; then
            sudo cp dump1090 /usr/local/bin/ >/dev/null 2>&1
            echo "✓ ADS-B decoder installed from source"
        else
            echo "⚠ Failed to compile ADS-B decoder"
        fi
    else
        echo "⚠ Failed to download ADS-B decoder source"
    fi
    cd /
    rm -rf "$TEMP_DIR"
else
    echo "✓ ADS-B decoder already available"
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
