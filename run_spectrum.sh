#!/bin/bash
# SpectrumSnek Whiptail Launcher & Menu - FINAL VERIFIED
# This version corrects the menu logic and restores all options.

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
    echo "--- Preparing ADS-B Session ---"
    stop_adsb_services
    
    READSB_PATH=$(command -v readsb || find /home -name readsb -type f -executable 2>/dev/null | head -n 1)
    if [ -z "$READSB_PATH" ]; then
        whiptail --title "Error" --msgbox "'readsb' executable not found. Please install it." 8 78
        return
    fi

    JSON_DIR="/run/readsb"
    if ! touch "$JSON_DIR/write_test" 2>/dev/null; then
        JSON_DIR="/tmp/spectrumsnek"
        mkdir -p "$JSON_DIR"
    fi
    rm -rf "$JSON_DIR"/*

    echo "Using '$JSON_DIR' for readsb output."
    $READSB_PATH --net --write-json "$JSON_DIR" --quiet --no-interactive --device-type rtlsdr --gain auto &
    READSB_PID=$!
    
    if ! timeout 10s bash -c "while ! [ -s '$JSON_DIR/aircraft.json' ]; do sleep 0.5; done"; then
        whiptail --title "Error" --msgbox "readsb started but failed to write data. Check SDR." 8 78
        kill $READSB_PID 2>/dev/null
        return
    fi
    
    "$SCRIPT_DIR/adsb_radar.py" --file "$JSON_DIR/aircraft.json"
    
    kill $READSB_PID 2>/dev/null
    stop_adsb_services
}

# --- Main Execution Logic ---
if [ $# -gt 0 ]; then
    cmd=$1
    shift
    case "$cmd" in
        spectrum) exec python3 "$SCRIPT_DIR/plugins/rtl_scanner/scanner.py" "$@" ;;
        scanner) exec python3 "$SCRIPT_DIR/plugins/radio_scanner/scanner.py" "$@" ;;
        radar) exec "$SCRIPT_DIR/adsb_radar.py" "$@" ;;
        adsb_full) exec launch_adsb_with_decoder ;;
        *) echo "Unknown command: $cmd"; exit 1 ;;
    esac
    exit 0
fi

# --- Interactive Menu Loop ---
while true; do
    CHOICE=$(whiptail --title "SpectrumSnek 🐍📻" --menu "Select a tool:" 20 78 12 
        "1" "RTL-SDR Spectrum Listener" 
        "2" "Traditional Radio Scanner" 
        "3" "ADS-B Radar (Full Session)" 
        "4" "WiFi Tool" 
        "5" "Bluetooth Tool" 
        "6" "System Tools" 
        "7" "Legacy Curses Menu (main.py)" 
        "8" "ADS-B Service Only (for other apps)" 
        3>&1 1>&2 2>&3)

    # Exit if user presses Cancel or Esc
    if [ $? -ne 0 ]; then
        break
    fi

    clear
    case "$CHOICE" in
        "1")
            echo "Launching RTL-SDR Spectrum Listener..."
            python3 "$SCRIPT_DIR/plugins/rtl_scanner/scanner.py"
            ;;
        "2")
            echo "Launching Traditional Radio Scanner..."
            python3 "$SCRIPT_DIR/plugins/radio_scanner/scanner.py"
            ;;
        "3")
            echo "Launching Full ADS-B Session..."
            launch_adsb_with_decoder
            ;;
        "4")
            echo "Launching WiFi Tool..."
            python3 "$SCRIPT_DIR/wifi_tool/wifi_selector.py"
            ;;
        "5")
            echo "Launching Bluetooth Tool..."
            python3 "$SCRIPT_DIR/bluetooth_tool/bluetooth_connector.py"
            ;;
        "6")
            echo "Launching System Tools..."
            python3 "$SCRIPT_DIR/plugins/system_tools/system_menu.py"
            ;;
        "7")
            echo "Launching Legacy Curses Menu..."
            python3 "$SCRIPT_DIR/main.py"
            ;;
        "8")
            echo "Launching ADS-B Service Only..."
            python3 "$SCRIPT_DIR/plugins/adsb_tool/adsb_service.py"
            ;;
        *)
            # This case should not be reached with a properly constructed menu
            whiptail --title "Error" --msgbox "An unexpected error occurred." 8 78
            ;;
    esac
    echo
    echo "--- Task Ended. Press Enter to return to menu. ---"
    read -r
done

echo "Goodbye!"
