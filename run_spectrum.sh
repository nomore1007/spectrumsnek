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
    # Try multiple ways to stop decoders
    pkill -f readsb 2>/dev/null
    pkill -f dump1090 2>/dev/null
    # Also stop any python-based services
    pkill -f adsb_service.py 2>/dev/null
    sleep 1
}

# Function to launch ADS-B Radar with its own decoder
launch_adsb_with_decoder() {
    clear
    echo "Stopping existing services to free SDR..."
    stop_adsb_services
    
    echo "Starting ADS-B Decoder (readsb)..."
    # Ensure the JSON directory exists
    mkdir -p /run/readsb
    
    # Launch readsb in background with logging
    # --no-interactive might help when running as root
    readsb --net --net-api-port 8080 --write-json /run/readsb --quiet --no-interactive --device-type rtlsdr --gain auto > /tmp/readsb.log 2>&1 &
    READSB_PID=$!
    
    # Wait for readsb to initialize and start writing JSON
    echo "Waiting for decoder to start..."
    for i in {1..10}; do
        if [ -f "/run/readsb/aircraft.json" ]; then
            echo "Decoder started successfully."
            break
        fi
        if ! kill -0 $READSB_PID 2>/dev/null; then
            echo "ERROR: Decoder failed to start. Check /tmp/readsb.log"
            cat /tmp/readsb.log
            sleep 5
            return
        fi
        sleep 1
    done
    
    echo "Launching Radar Display..."
    # Launch the graphical radar
    ./adsb_radar.py
    
    echo "Stopping ADS-B Decoder..."
    kill $READSB_PID 2>/dev/null
    stop_adsb_services
    echo "Done."
    sleep 1
}

# Main loop
while true; do
    if [ $# -gt 0 ]; then
        # Handle command line arguments for standalone launch
        cmd=$1
        shift
        case "$cmd" in
            spectrum|rtl_scanner)
                python3 "$SCRIPT_DIR/plugins/rtl_scanner/scanner.py" "$@"
                exit 0
                ;;
            radio|scanner)
                python3 "$SCRIPT_DIR/plugins/radio_scanner/scanner.py" "$@"
                exit 0
                ;;
            radar|adsb_radar)
                "$SCRIPT_DIR/adsb_radar.py" "$@"
                exit 0
                ;;
            adsb_full)
                launch_adsb_with_decoder
                exit 0
                ;;
            adsb_service)
                python3 "$SCRIPT_DIR/plugins/adsb_tool/adsb_service.py" "$@"
                exit 0
                ;;
            main)
                python3 "$SCRIPT_DIR/main.py" "$@"
                exit 0
                ;;
            *)
                echo "Unknown command: $cmd"
                echo "Usage: $0 [spectrum|radio|radar|adsb_full|adsb_service|main] [args]"
                exit 1
                ;;
        esac
    fi

    # Whiptail Menu
    CHOICE=$(whiptail --title "SpectrumSnek 🐍📻" --menu "Select a tool to launch:" 18 65 10 \
        "1" "RTL-SDR Spectrum Listener" \
        "2" "Traditional Radio Scanner" \
        "3" "ADS-B Radar (Full: readsb + display)" \
        "4" "ADS-B Service Only (readsb)" \
        "5" "WiFi Tool" \
        "6" "Bluetooth Tool" \
        "7" "System Tools" \
        "8" "Launch Original main.py (Legacy)" \
        "q" "Quit" 3>&1 1>&2 2>&3)

    case "$CHOICE" in
        1) python3 "$SCRIPT_DIR/plugins/rtl_scanner/scanner.py" ;;
        2) python3 "$SCRIPT_DIR/plugins/radio_scanner/scanner.py" ;;
        3) launch_adsb_with_decoder ;;
        4) python3 "$SCRIPT_DIR/plugins/adsb_tool/adsb_service.py" ;;
        5) python3 "$SCRIPT_DIR/wifi_tool/wifi_selector.py" ;;
        6) python3 "$SCRIPT_DIR/bluetooth_tool/bluetooth_connector.py" ;;
        7) python3 "$SCRIPT_DIR/plugins/system_tools/system_menu.py" ;;
        8) python3 "$SCRIPT_DIR/main.py" ;;
        q|"") echo "Goodbye!"; exit 0 ;;
        *) exit 0 ;;
    esac
done
