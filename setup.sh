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
    # For RTL-SDR, try multiple installation methods
    if ! command -v dump1090-fa &> /dev/null && ! command -v dump1090-mutability &> /dev/null && ! command -v dump1090 &> /dev/null; then
        echo "Installing ADS-B decoder for RTL-SDR compatibility..."

        # Update package lists
        sudo apt update >/dev/null 2>&1

        # Method 1: Try installing dump1090-fa
        echo "Trying dump1090-fa..."
        if sudo apt install -y dump1090-fa >/dev/null 2>&1; then
            echo "✓ ADS-B decoder (dump1090-fa) installed successfully"
        else
            # Method 2: Try installing dump1090-mutability
            echo "dump1090-fa not available, trying dump1090-mutability..."
            if sudo apt install -y dump1090-mutability >/dev/null 2>&1; then
                echo "✓ ADS-B decoder (dump1090-mutability) installed successfully"
            else
                # Method 3: Try building dump1090-fa from source
                echo "Package installation failed, building from source..."
                if command -v git &> /dev/null && command -v make &> /dev/null; then
                    TEMP_DIR=$(mktemp -d)
                    cd "$TEMP_DIR"

                    echo "Trying alternative ADS-B decoder installation..."

                    # Try the antirez dump1090 (simpler build)
                    if git clone https://github.com/antirez/dump1090.git >/dev/null 2>&1; then
                        cd dump1090
                        echo "Building dump1090 (simpler version)..."
                        # Make sure we have all required libraries
                        sudo apt install -y libncurses5-dev >/dev/null 2>&1
                        if gcc -I. dump1090.c anet.c -o dump1090 -lm -lpthread -lrtlsdr -lusb-1.0 -lncurses >/dev/null 2>&1; then
                            sudo cp dump1090 /usr/local/bin/ >/dev/null 2>&1
                            if command -v dump1090 &> /dev/null; then
                                echo "✓ ADS-B decoder (dump1090) built and installed from source"
                                # Test if it can at least show help
                                if dump1090 --help >/dev/null 2>&1; then
                                    echo "✓ dump1090 basic functionality verified"
                                else
                                    echo "⚠ dump1090 installed but basic test failed"
                                fi
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
                if command -v dump1090-fa &> /dev/null || command -v dump1090-mutability &> /dev/null || command -v dump1090 &> /dev/null; then
                    echo "✓ ADS-B decoder installation completed successfully"
                else
                    echo "⚠ All automatic installation methods failed"
                    echo "ADS-B functionality will require manual decoder installation"
                fi
            fi
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
