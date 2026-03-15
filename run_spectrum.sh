#!/bin/bash
# SpectrumSnek Simple & Reliable Launcher

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="$SCRIPT_DIR/venv"

# --- Pre-flight Checks ---
if [ ! -d "$VENV_DIR" ]; then
    echo "ERROR: Virtual environment not found. Please run ./setup.sh first." >&2
    exit 1
fi
source "$VENV_DIR/bin/activate"
# --- End Pre-flight Checks ---

stop_adsb_services() {
    pkill -f readsb 2>/dev/null
    pkill -f dump1090 2>/dev/null
}

launch_adsb_with_decoder() {
    clear
    echo "--- Preparing ADS-B Session ---"
    stop_adsb_services
    
    READSB_PATH=$(command -v readsb || find /home -name readsb -type f -executable 2>/dev/null | head -n 1)
    if [ -z "$READSB_PATH" ]; then
        echo "ERROR: 'readsb' executable not found." && sleep 3
        return
    fi

    JSON_DIR="/tmp/spectrumsnek"
    mkdir -p "$JSON_DIR"
    rm -rf "$JSON_DIR"/*
    echo "Using '$JSON_DIR' for readsb output."

    $READSB_PATH --net --write-json "$JSON_DIR" --quiet --no-interactive --device-type rtlsdr --gain auto &
    READSB_PID=$!
    
    if ! timeout 10s bash -c "while ! [ -s '$JSON_DIR/aircraft.json' ]; do sleep 0.5; done"; then
        echo "ERROR: readsb started but failed to write data. Check SDR." && sleep 3
        kill $READSB_PID 2>/dev/null
        return
    fi
    
    "$SCRIPT_DIR/adsb_radar.py" --file "$JSON_DIR/aircraft.json"
    
    kill $READSB_PID 2>/dev/null
    stop_adsb_services
}

# --- Main Menu Loop ---
while true; do
    clear
    echo "======================================"
    echo " SpectrumSnek 🐍📻 - Main Menu"
    echo "======================================"
    options=(
        "RTL-SDR Spectrum Listener"
        "Traditional Radio Scanner"
        "ADS-B Radar (Full Session)"
        "WiFi Tool"
        "Bluetooth Tool"
        "System Tools"
        "Legacy Curses Menu (main.py)"
        "Quit"
    )
    
    select opt in "${options[@]}"; do
        case "$opt" in
            "RTL-SDR Spectrum Listener")
                python3 "$SCRIPT_DIR/plugins/rtl_scanner/scanner.py"
                break
                ;;
            "Traditional Radio Scanner")
                python3 "$SCRIPT_DIR/plugins/radio_scanner/scanner.py"
                break
                ;;
            "ADS-B Radar (Full Session)")
                launch_adsb_with_decoder
                break
                ;;
            "WiFi Tool")
                python3 "$SCRIPT_DIR/wifi_tool/wifi_selector.py"
                break
                ;;
            "Bluetooth Tool")
                python3 "$SCRIPT_DIR/bluetooth_tool/bluetooth_connector.py"
                break
                ;;
            "System Tools")
                python3 "$SCRIPT_DIR/plugins/system_tools/system_menu.py"
                break
                ;;
            "Legacy Curses Menu (main.py)")
                python3 "$SCRIPT_DIR/main.py"
                break
                ;;
            "Quit")
                echo "Goodbye!"
                exit 0
                ;;
            *) 
                echo "Invalid option $REPLY"
                ;;
        esac
    done
    echo
    read -p "Press Enter to return to menu..."
done
