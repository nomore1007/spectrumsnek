#!/bin/bash
# SpectrumSnek Whiptail Launcher & Menu
# Modern launcher using whiptail for a better CLI experience.

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="$SCRIPT_DIR/venv"

# Ensure virtual environment is active
if [ -d "$VENV_DIR" ]; then
    source "$VENV_DIR/bin/activate"
else
    echo "Virtual environment not found. Please run ./setup.sh first."
    exit 1
fi

# Function to stop any running ADS-B services
stop_adsb_services() {
    pkill -f readsb 2>/dev/null
    pkill -f dump1090 2>/dev/null
    sleep 0.5
}

# Function to launch ADS-B Radar with its own decoder
launch_adsb_with_decoder() {
    clear
    echo "--- Preparing ADS-B Session ---"
    
    stop_adsb_services
    
    # 1. Find readsb
    READSB_PATH=$(command -v readsb)
    if [ -z "$READSB_PATH" ]; then
        # If not in PATH, check the home dir of the user who invoked sudo
        if [ -n "$SUDO_USER" ]; then
            USER_HOME=$(getent passwd "$SUDO_USER" | cut -d: -f6)
        else
            # Fallback for direct root login: find the primary non-root user (usually UID 1000)
            USER_HOME=$(getent passwd 1000 | cut -d: -f6)
        fi
        
        if [ -x "$USER_HOME/readsb" ]; then
            READSB_PATH="$USER_HOME/readsb"
        elif [ -x "$USER_HOME/readsb/readsb" ]; then
            READSB_PATH="$USER_HOME/readsb/readsb"
        else
            echo "ERROR: 'readsb' not found in PATH or in '$USER_HOME'."
            sleep 3
            return
        fi
    fi
    # 2. Determine and prepare the output directory
    JSON_DIR="/run/readsb"
    # Attempt to use the primary directory. If not writable, fallback to /tmp.
    if ! touch "$JSON_DIR/write_test" 2>/dev/null; then
        JSON_DIR="/tmp/spectrumsnek"
        mkdir -p "$JSON_DIR"
    else
        rm "$JSON_DIR/write_test"
    fi
    # Recursively remove contents to handle subdirectories
    rm -rf "$JSON_DIR"/*
    echo "Using '$JSON_DIR' for readsb output."

    # 3. Launch readsb
    $READSB_PATH --net --net-api-port 8080 --write-json "$JSON_DIR" --no-interactive --device-type rtlsdr --gain auto &
    READSB_PID=$!
    
    # 4. Verify readsb is running and writing data
    echo "Verifying readsb operation (PID: $READSB_PID)..."
    sleep 3
    
    if ! kill -0 $READSB_PID 2>/dev/null; then
        echo "ERROR: readsb process failed to start or exited immediately."
        sleep 3
        return
    fi

    # 5. Launch the display
    "$SCRIPT_DIR/adsb_radar.py" --file "$JSON_DIR/aircraft.json"
    
    # 6. Cleanup
    kill $READSB_PID 2>/dev/null
    stop_adsb_services
    echo "Session ended."
    sleep 1
}

# Main loop
while true; do
    if [ $# -gt 0 ]; then
        # Handle command line arguments for standalone launch
        cmd=$1
        shift
        case "$cmd" in
            spectrum|rtl_scanner) python3 "$SCRIPT_DIR/plugins/rtl_scanner/scanner.py" "$@" ; exit 0 ;;
            radio|scanner) python3 "$SCRIPT_DIR/plugins/radio_scanner/scanner.py" "$@" ; exit 0 ;;
            radar|adsb_radar) "$SCRIPT_DIR/adsb_radar.py" "$@" ; exit 0 ;;
            adsb_full) launch_adsb_with_decoder ; exit 0 ;;
            adsb_service) python3 "$SCRIPT_DIR/plugins/adsb_tool/adsb_service.py" "$@" ; exit 0 ;;
            main) python3 "$SCRIPT_DIR/main.py" "$@" ; exit 0 ;;
            *) echo "Unknown command: $cmd"; exit 1 ;;
        esac
    fi

    # Whiptail Menu
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

    EXIT_STATUS=$?
    if [ $EXIT_STATUS -ne 0 ]; then
        echo "Goodbye!";
        exit 0;
    fi

    case "$CHOICE" in
        1) python3 "$SCRIPT_DIR/plugins/rtl_scanner/scanner.py" ;;
        2) python3 "$SCRIPT_DIR/plugins/radio_scanner/scanner.py" ;;
        3) launch_adsb_with_decoder ;;
        4) python3 "$SCRIPT_DIR/wifi_tool/wifi_selector.py" ;;
        5) python3 "$SCRIPT_DIR/bluetooth_tool/bluetooth_connector.py" ;;
        6) python3 "$SCRIPT_DIR/plugins/system_tools/system_menu.py" ;;
        7) python3 "$SCRIPT_DIR/main.py" ;;
        8) python3 "$SCRIPT_DIR/plugins/adsb_tool/adsb_service.py" ;;
        *) echo "Goodbye!"; exit 0 ;;
    esac
done
