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
        echo "ERROR: 'readsb' command not found."
        sleep 3
        return
    fi
    echo "Found readsb at: $READSB_PATH"

    # 2. Determine and prepare the output directory
    JSON_DIR="/run/readsb"
    # Create the directory if it doesn't exist
    mkdir -p "$JSON_DIR"
    # Attempt to take ownership to ensure write access. This is the most reliable way under root.
    chown root:root "$JSON_DIR"
    
    # Check if we can write to the primary directory. If not, fallback to /tmp.
    if ! touch "$JSON_DIR/write_test" 2>/dev/null; then
        echo "WARNING: Cannot write to '$JSON_DIR'. Falling back to /tmp/spectrumsnek."
        JSON_DIR="/tmp/spectrumsnek"
        mkdir -p "$JSON_DIR"
    else
        # Cleanup the test file if successful
        rm "$JSON_DIR/write_test"
    fi
    # Ensure the chosen directory is clean
    rm -f "$JSON_DIR"/*
    echo "Using '$JSON_DIR' for readsb output."

    # 3. Launch readsb
    echo "--- Starting readsb ---"
    $READSB_PATH --net --net-api-port 8080 --write-json "$JSON_DIR" --no-interactive --device-type rtlsdr --gain auto &
    READSB_PID=$!
    
    # 4. Verify readsb is running and writing data
    echo "Verifying readsb operation (PID: $READSB_PID)..."
    sleep 3 # Give it time to start
    
    if ! kill -0 $READSB_PID 2>/dev/null; then
        echo "ERROR: readsb process failed to start or exited immediately."
        sleep 3
        return
    fi

    echo "Waiting for aircraft.json to be created..."
    for i in {1..7}; do
        if [ -s "$JSON_DIR/aircraft.json" ]; then
            echo "SUCCESS: aircraft.json found and is not empty."
            break
        fi
        echo -n "."
        sleep 1
    done

    if ! [ -s "$JSON_DIR/aircraft.json" ]; then
        echo "ERROR: readsb is running, but aircraft.json is missing or empty."
        echo "Please check SDR connection and antenna."
        sleep 3
        kill $READSB_PID 2>/dev/null
        return
    fi

    # 5. Launch the display
    echo "--- Launching Radar Display ---"
    "$SCRIPT_DIR/adsb_radar.py" --file "$JSON_DIR/aircraft.json"
    
    # 6. Cleanup
    echo "--- Cleaning up ---"
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
    CHOICE=$(whiptail --title "SpectrumSnek 🐍📻" --menu "Select a tool:" 18 65 10 
        "1" "RTL-SDR Spectrum Listener" 
        "2" "Traditional Radio Scanner" 
        "3" "ADS-B Radar (Full Session)" 
        "4" "ADS-B Service Only" 
        "q" "Quit" 3>&1 1>&2 2>&3)

    case "$CHOICE" in
        1) python3 "$SCRIPT_DIR/plugins/rtl_scanner/scanner.py" ;;
        2) python3 "$SCRIPT_DIR/plugins/radio_scanner/scanner.py" ;;
        3) launch_adsb_with_decoder ;;
        4) python3 "$SCRIPT_DIR/plugins/adsb_tool/adsb_service.py" ;;
        q|"") echo "Goodbye!"; exit 0 ;;
        *) exit 0 ;;
    esac
done
