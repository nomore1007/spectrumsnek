#!/bin/bash
# SpectrumSnek Whiptail Launcher & Menu
# Optimized for Raspberry Pi and root environments.

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="$SCRIPT_DIR/venv"

# --- Environment Setup ---
if [ ! -d "$VENV_DIR" ]; then
    echo "ERROR: Virtual environment not found at $VENV_DIR"
    echo "Please run ./setup.sh first."
    exit 1
fi
source "$VENV_DIR/bin/activate"

# Ensure whiptail is available
if ! command -v whiptail >/dev/null 2>&1; then
    echo "ERROR: 'whiptail' is not installed."
    exit 1
fi

# --- Main Launcher Loop ---
while true; do
    # Capture tag ("1", "2", etc.) from whiptail
    CHOICE=$(whiptail --title "SpectrumSnek 🐍📻" \
        --menu "Use arrows to navigate and Enter to select:" 20 78 10 \
        "1" "RTL-SDR Spectrum Listener (Scanner)" \
        "2" "Traditional Radio Scanner (Audio)" \
        "3" "ADS-B Radar (Full Session: readsb + UI)" \
        "4" "WiFi Tool" \
        "5" "Bluetooth Tool" \
        "6" "System Tools" \
        "7" "Legacy Curses Menu (main.py)" \
        3>&1 1>&2 2>&3)

    # Exit if user hits Cancel or Escape
    if [ $? -ne 0 ]; then
        break
    fi

    case "$CHOICE" in
        "1")
            python "$SCRIPT_DIR/plugins/rtl_scanner/scanner.py"
            ;;
        "2")
            python3 "$SCRIPT_DIR/plugins/radio_scanner/scanner.py"
            ;;
        "3")
            PYTHONPATH="$SCRIPT_DIR" python -m plugins.adsb_radar
            ;;
        "4")
            python3 "$SCRIPT_DIR/wifi_tool/wifi_selector.py"
            ;;
        "5")
            python3 "$SCRIPT_DIR/bluetooth_tool/bluetooth_connector.py"
            ;;
        "6")
            python3 "$SCRIPT_DIR/plugins/system_tools/system_menu.py"
            ;;
        "7")
            python3 "$SCRIPT_DIR/main.py"
            ;;
        *)
            # Should not happen with whiptail tags
            continue
            ;;
    esac
done

clear
echo "Goodbye!"
