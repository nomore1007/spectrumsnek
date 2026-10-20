#!/bin/bash
# SpectrumSnek Whiptail Launcher & Menu
# Installed plugins are discovered automatically from plugins/*/__init__.py.

set -u

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="$SCRIPT_DIR/venv"
PYTHON="python3"

# --- Environment Setup ---
if [ ! -d "$VENV_DIR" ]; then
    echo "ERROR: Virtual environment not found at $VENV_DIR"
    echo "Please run ./setup.sh first."
    exit 1
fi
source "$VENV_DIR/bin/activate"
if [ -x "$VENV_DIR/bin/python" ]; then
    PYTHON="$VENV_DIR/bin/python"
fi

if ! command -v whiptail >/dev/null 2>&1; then
    echo "ERROR: 'whiptail' is not installed."
    echo "Install it with: sudo apt install whiptail"
    exit 1
fi

# --- Main Launcher Loop ---
while true; do
    MENU_ITEMS=(
        "builtin:rtl_scanner" "RTL-SDR Spectrum Listener (Scanner)"
        "builtin:radio_scanner" "Traditional Radio Scanner (Audio)"
        "builtin:wifi" "WiFi Tool"
        "builtin:bluetooth" "Bluetooth Tool"
        "builtin:system_tools" "System Tools"
    )

    # The helper emits plugin ID, display name, and description separated by tabs.
    # Plugin import failures are reported to stderr and do not break the menu.
    while IFS=$'\t' read -r plugin_id plugin_name plugin_description; do
        [ -n "${plugin_id:-}" ] || continue
        MENU_ITEMS+=("plugin:$plugin_id" "$plugin_name: $plugin_description")
    done < <("$PYTHON" "$SCRIPT_DIR/plugin_menu.py" --list)

    CHOICE=$(whiptail --title "SpectrumSnek 🐍📻" \
        --menu "Use arrows to navigate and Enter to select:" 22 90 12 \
        "${MENU_ITEMS[@]}" \
        3>&1 1>&2 2>&3)
    STATUS=$?

    # Cancel or Escape returns to the shell.
    if [ "$STATUS" -ne 0 ]; then
        break
    fi

    case "$CHOICE" in
        "builtin:rtl_scanner")
            "$PYTHON" "$SCRIPT_DIR/plugins/rtl_scanner/scanner.py"
            ;;
        "builtin:radio_scanner")
            "$PYTHON" "$SCRIPT_DIR/plugins/radio_scanner/scanner.py"
            ;;
        "builtin:wifi")
            "$PYTHON" "$SCRIPT_DIR/wifi_tool/wifi_selector.py"
            ;;
        "builtin:bluetooth")
            "$PYTHON" "$SCRIPT_DIR/bluetooth_tool/bluetooth_connector.py"
            ;;
        "builtin:system_tools")
            "$PYTHON" "$SCRIPT_DIR/plugins/system_tools/system_menu.py"
            ;;
        plugin:*)
            PLUGIN_ID="${CHOICE#plugin:}"
            "$PYTHON" "$SCRIPT_DIR/plugin_menu.py" --run "$PLUGIN_ID"
            ;;
        *)
            continue
            ;;
    esac

    RESULT=$?
    if [ "$RESULT" -ne 0 ]; then
        printf '\nTool exited with status %s.\n' "$RESULT"
    fi
    read -r -p "Press Enter to return to the menu..." _
done

clear
echo "Goodbye!"
