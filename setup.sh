#!/bin/bash
# SpectrumSnek Setup Script - Self-Sustaining Version

echo "SpectrumSnek Setup"
echo "=================="
echo ""
echo "Setting up SpectrumSnek radio analysis toolkit..."
echo ""

# Install ADS-B decoder
echo "Checking for ADS-B decoder..."
if ! command -v dump1090-mutability &> /dev/null && ! command -v dump1090-fa &> /dev/null && ! command -v readsb &> /dev/null; then
    echo "ADS-B decoder not found, installing readsb..."

    # Install readsb which is available in Debian repos
    sudo apt update >/dev/null 2>&1
    sudo apt install -y readsb >/dev/null 2>&1

    if command -v readsb &> /dev/null; then
        echo "✓ ADS-B decoder (readsb) installed"
        echo "Note: readsb works best with dedicated ADS-B hardware"
        echo "For RTL-SDR, aircraft detection may be limited"
    else
        echo "⚠ Failed to install ADS-B decoder"
    fi
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
