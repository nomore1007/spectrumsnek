#!/bin/bash
# SpectrumSnek Whiptail Launcher & Menu - FINAL CORRECTED VERSION

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="$SCRIPT_DIR/venv"

# --- Pre-flight Checks ---
if [ ! -d "$VENV_DIR" ]; then
    echo "ERROR: Virtual environment not found. Please run ./setup.sh first." >&2
    exit 1
fi
source "$VENV_DIR/bin/activate"

if ! command -v whiptail >/dev/null 2>&1; then
    echo "ERROR: 'whiptail' is not installed. Please run 'sudo apt-get install whiptail'." >&2
    exit 1
fi
# --- End Pre-flight Checks ---

stop_adsb_services() {
    pkill -f readsb 2>/dev/null
    pkill -f dump1090 2>/dev/null
}

launch_adsb_with_decoder() {
    clear
    READSB_PATH=$(command -v readsb || find /home -name readsb -type f -executable 2>/dev/null | head -n 1)
    if [ -z "$READSB_PATH" ]; then
        whiptail --title "Error" --msgbox "'readsb' executable not found. Please install it." 8 78
        return
    fi

    # Use /tmp as it's universally writable, avoiding all /run permission issues.
    JSON_DIR="/tmp/spectrumsnek_readsb"
    mkdir -p "$JSON_DIR"
    rm -rf "$JSON_DIR"/*
    
    echo "Starting readsb in background..."
    $READSB_PATH --net --write-json "$JSON_DIR" --quiet --no-interactive --device-type rtlsdr --gain auto &
    READSB_PID=$!
    
    # Verify readsb is running and writing data before proceeding
    if ! timeout 10s bash -c "while ! [ -s '$JSON_DIR/aircraft.json' ]; do sleep 0.5; done"; then
        whiptail --title "Error" --msgbox "readsb started but failed to write data. Check SDR connection and antenna." 10 78
        kill $READSB_PID 2>/dev/null
        return
    fi
    
    # Launch the display in the foreground
    "$SCRIPT_DIR/adsb_radar.py" --file "$JSON_DIR/aircraft.json"
    
    # Cleanup after display exits
    kill $READSB_PID 2>/dev/null
    stop_adsb_services
}

# --- Main Interactive Menu Loop ---
while true; do
    CHOICE=$(whiptail --title "SpectrumSnek 🐍📻" --menu "Select a tool (press Esc to quit):" 20 78 10 
        "1" "RTL-SDR Spectrum Listener" 
        "2" "Traditional Radio Scanner" 
        "3" "ADS-B Radar (Full Session)" 
        "4" "WiFi Tool" 
        "5" "Bluetooth Tool" 
        "6" "System Tools" 
        "7" "Legacy Curses Menu (main.py)" 
        3>&1 1>&2 2>&3)

    # Exit if user presses Esc or Cancel
    if [ $? -ne 0 ]; then
        break
    fi

    clear
    case "$CHOICE" in
        "1") python3 "$SCRIPT_DIR/plugins/rtl_scanner/scanner.py" ;;
        "2") python3 "$SCRIPT_DIR/plugins/radio_scanner/scanner.py" ;;
        "3") launch_adsb_with_decoder ;;
        "4") python3 "$SCRIPT_DIR/wifi_tool/wifi_selector.py" ;;
        "5") python3 "$SCRIPT_DIR/bluetooth_tool/bluetooth_connector.py" ;;
        "6") python3 "$SCRIPT_DIR/plugins/system_tools/system_menu.py" ;;
        "7") python3 "$SCRIPT_DIR/main.py" ;;
    esac
done

echo "Goodbye!"
