#!/bin/bash
# SpectrumSnek Setup Script - Self-Sustaining Version

echo "SpectrumSnek Setup"
echo "=================="
echo ""
echo "Setting up SpectrumSnek radio analysis toolkit..."
echo ""

# Install ADS-B decoder compatible with detected SDR
echo "Checking for ADS-B decoder..."

# Detect SDR type
sdr_type="unknown"
if command -v rtl_test &> /dev/null; then
    if rtl_test -t 2>&1 | grep -q "Found [0-9] device"; then
        sdr_type="rtlsdr"
        echo "RTL-SDR detected - will install compatible ADS-B decoder"
    fi
fi

if [ "$sdr_type" = "rtlsdr" ]; then
    # For RTL-SDR, try to install dump1090-fa or build from source
    if ! command -v dump1090-fa &> /dev/null && ! command -v dump1090-mutability &> /dev/null; then
        echo "Installing dump1090-fa for RTL-SDR compatibility..."

        # Update package lists
        sudo apt update >/dev/null 2>&1

        # Try installing dump1090-fa
        if sudo apt install -y dump1090-fa >/dev/null 2>&1; then
            echo "✓ ADS-B decoder (dump1090-fa) installed for RTL-SDR"
        else
            echo "⚠ dump1090-fa not available, attempting to build compatible decoder..."

        # Provide manual installation instructions since automatic build is complex
        echo "⚠ Automatic ADS-B decoder installation failed"
        echo ""
        echo "To enable ADS-B functionality, please install manually:"
        echo "  sudo apt install dump1090-fa"
        echo "  # OR"
        echo "  sudo apt install dump1090-mutability"
        echo ""
        echo "For source installation:"
        echo "  git clone https://github.com/flightaware/dump1090.git"
        echo "  cd dump1090 && make && sudo make install"
        echo ""
        echo "ADS-B will work once a compatible decoder is installed."
        fi
    else
        echo "✓ RTL-SDR compatible ADS-B decoder already available"
    fi
else
    # For other SDR types or unknown, install readsb
    if ! command -v readsb &> /dev/null; then
        echo "Installing readsb for general ADS-B compatibility..."
        sudo apt update >/dev/null 2>&1
        sudo apt install -y readsb >/dev/null 2>&1

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
