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

stop_adsb_services() {
    pkill -f readsb 2>/dev/null
    pkill -f dump1090 2>/dev/null
    sleep 0.2
}

launch_adsb_with_decoder() {
    clear
    echo "--- Preparing ADS-B Session ---"
    stop_adsb_services
    
    # Robust readsb discovery
    READSB_PATH=$(command -v readsb || find /home -name readsb -type f -executable 2>/dev/null | head -n 1)
    if [ -z "$READSB_PATH" ]; then
        whiptail --title "Error" --msgbox "readsb executable not found in PATH or /home." 8 78
        return
    fi

    # Universally writable directory
    JSON_DIR="/tmp/spectrumsnek_readsb"
    mkdir -p "$JSON_DIR"
    rm -rf "$JSON_DIR"/*

    echo "Using '$JSON_DIR' for readsb output."
    $READSB_PATH --net --write-json "$JSON_DIR" --quiet --no-interactive --device-type rtlsdr --gain auto >/dev/null 2>&1 &
    READSB_PID=$!
    
    # Wait for data with timeout
    echo "Waiting for decoder data..."
    if ! timeout 10s bash -c "while ! [ -s '$JSON_DIR/aircraft.json' ]; do sleep 0.5; done" 2>/dev/null; then
        whiptail --title "Error" --msgbox "readsb started but no data received. Check SDR/Antenna." 8 78
        kill $READSB_PID 2>/dev/null
        return
    fi
    
    # Run the graphical radar
    "$SCRIPT_DIR/adsb_radar.py" --file "$JSON_DIR/aircraft.json"
    
    # Exit cleanup
    kill $READSB_PID 2>/dev/null
    stop_adsb_services
}

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
            python3 "$SCRIPT_DIR/plugins/rtl_scanner/scanner.py"
            ;;
        "2")
            python3 "$SCRIPT_DIR/plugins/radio_scanner/scanner.py"
            ;;
        "3")
            launch_adsb_with_decoder
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
