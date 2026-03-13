#!/bin/bash
# SpectrumSnek Bash Launcher & Menu
# Simplified launcher that handles environment and provides a standalone-capable menu.

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="$SCRIPT_DIR/venv"

# Ensure virtual environment is active
if [ -d "$VENV_DIR" ]; then
    source "$VENV_DIR/bin/activate"
else
    echo "Virtual environment not found. Please run ./setup.sh first."
    exit 1
fi

# Function to show the menu
show_menu() {
    clear
    echo "🐍📻 SpectrumSnek - Radio Tools Menu"
    echo "======================================"
    echo "1) RTL-SDR Spectrum Listener (RTL Scanner)"
    echo "2) Traditional Radio Scanner"
    echo "3) ADS-B Aircraft Tracker (Radar)"
    echo "4) ADS-B Service (readsb)"
    echo "5) WiFi Tool"
    echo "6) Bluetooth Tool"
    echo "7) System Tools"
    echo "8) Launch Original main.py (Legacy)"
    echo "q) Quit"
    echo ""
    read -p "Select an option: " choice
}

# Function to launch ADS-B Radar
launch_adsb_radar() {
    echo "Launching ADS-B Radar..."
    # Check if readsb is running
    if ! pgrep -f "readsb|dump1090" > /dev/null; then
        echo "Warning: No ADS-B decoder (readsb/dump1090) detected."
        echo "Radar might not show any planes. Start ADS-B Service first if needed."
        sleep 2
    fi
    ./adsb_radar.py
}

# Main loop
while true; do
    if [ $# -gt 0 ]; then
        # Handle command line arguments for standalone launch
        cmd=$1
        shift
        case "$cmd" in
            spectrum|rtl_scanner)
                python3 plugins/rtl_scanner/scanner.py "$@"
                exit 0
                ;;
            radio|scanner)
                python3 plugins/radio_scanner/scanner.py "$@"
                exit 0
                ;;
            radar|adsb_radar)
                ./adsb_radar.py "$@"
                exit 0
                ;;
            adsb_service)
                python3 plugins/adsb_tool/adsb_service.py "$@"
                exit 0
                ;;
            main)
                python3 main.py "$@"
                exit 0
                ;;
            *)
                echo "Unknown command: $cmd"
                echo "Usage: $0 [spectrum|radio|radar|adsb_service|main] [args]"
                exit 1
                ;;
        esac
    fi

    show_menu
    case "$choice" in
        1) python3 plugins/rtl_scanner/scanner.py ;;
        2) python3 plugins/radio_scanner/scanner.py ;;
        3) launch_adsb_radar ;;
        4) python3 plugins/adsb_tool/adsb_service.py ;;
        5) python3 wifi_tool/wifi_selector.py ;;
        6) python3 bluetooth_tool/bluetooth_connector.py ;;
        7) python3 plugins/system_tools/system_menu.py ;;
        8) python3 main.py ;;
        q|Q) echo "Goodbye!"; exit 0 ;;
        *) echo "Invalid option. Press enter to continue."; read ;;
    esac
done
