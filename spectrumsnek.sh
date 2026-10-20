#!/bin/bash
# SpectrumSnek Whiptail Launcher & Menu
# Installed plugins are discovered automatically from plugins/*/__init__.py.

set -u

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# Log errors without redirecting Whiptail's terminal UI.
log_error() {
    printf '[%s] [launcher] %s\n' "$(date '+%Y-%m-%d %H:%M:%S')" "$*" | tee -a "$SCRIPT_DIR/error.log" >&2
}

run_logged() {
    "$@" 2> >(while IFS= read -r error_line; do
        log_error "$error_line"
    done)
}
VENV_DIR="$SCRIPT_DIR/venv"
PYTHON="python3"

if [ ! -d "$VENV_DIR" ]; then
    log_error "Virtual environment not found at $VENV_DIR"
    echo "Please run ./setup.sh first."
    exit 1
fi
source "$VENV_DIR/bin/activate"
if [ -x "$VENV_DIR/bin/python" ]; then
    PYTHON="$VENV_DIR/bin/python"
fi

if ! command -v whiptail >/dev/null 2>&1; then
    log_error "'whiptail' is not installed."
    echo "Install it with: sudo apt install whiptail"
    exit 1
fi

update_spectrumsnek() {
    if ! command -v git >/dev/null 2>&1; then
        whiptail --title "Update SpectrumSnek" --msgbox "Git is not installed. Install it with: sudo apt install git" 10 68
        return
    fi
    if ! git -C "$SCRIPT_DIR" rev-parse --is-inside-work-tree >/dev/null 2>&1; then
        whiptail --title "Update SpectrumSnek" --msgbox "This installation is not a Git checkout, so it cannot update itself." 10 72
        return
    fi
    branch=$(git -C "$SCRIPT_DIR" branch --show-current)
    if [ "$branch" != "master" ]; then
        whiptail --title "Update SpectrumSnek" --msgbox "Updates are configured for the master branch. Current branch: $branch" 10 72
        return
    fi

    whiptail --title "Update SpectrumSnek" --infobox "Checking GitHub for updates..." 8 48
    if ! run_logged git -C "$SCRIPT_DIR" fetch origin master; then
        whiptail --title "Update SpectrumSnek" --msgbox "Could not contact GitHub or fetch master. Check your network and Git remote. No local files were changed." 10 72
        return
    fi

    behind=$(git -C "$SCRIPT_DIR" rev-list --count HEAD..origin/master 2>/dev/null || echo 0)
    if [ "$behind" -eq 0 ]; then
        whiptail --title "Update SpectrumSnek" --msgbox "SpectrumSnek is already up to date with origin/master." 8 58
        return
    fi

    if [ -n "$(git -C "$SCRIPT_DIR" status --porcelain)" ]; then
        if ! whiptail --title "Update SpectrumSnek" --yesno "GitHub has $behind new commit(s), but local changes or untracked files were found.\n\nOverwrite local changes and install the update?\n\nWARNING: This permanently discards changes to tracked files and deletes untracked, non-ignored files. Ignored files and plugin directories remain untouched. Back up anything you want to keep.\n\nChoose No to cancel without changing local files." 18 78; then
            return
        fi
        if ! run_logged git -C "$SCRIPT_DIR" reset --hard origin/master; then
            whiptail --title "Update SpectrumSnek" --msgbox "Could not reset the checkout to origin/master. Inspect Git status before retrying." 10 72
            return
        fi
        if ! run_logged git -C "$SCRIPT_DIR" clean -fd; then
            whiptail --title "Update SpectrumSnek" --msgbox "The tracked files were updated, but some untracked files could not be removed. Inspect Git status." 10 72
            return
        fi
        whiptail --title "Update SpectrumSnek" --msgbox "Update installed successfully. Local tracked changes were overwritten and untracked non-ignored files were removed. Ignored files were preserved. Restart SpectrumSnek to use the newest launcher." 12 76
        return
    fi

    if whiptail --title "Update SpectrumSnek" --yesno "GitHub has $behind new commit(s). Install the update now?" 10 64; then
        if run_logged git -C "$SCRIPT_DIR" pull --ff-only origin master; then
            whiptail --title "Update SpectrumSnek" --msgbox "Update installed successfully. Restart SpectrumSnek to use the newest launcher." 10 72
        else
            whiptail --title "Update SpectrumSnek" --msgbox "Update failed. The local branch was not fast-forwarded. Check the Git status before retrying." 10 72
        fi
    fi
}

installed_plugins_menu() {
    local selected status adsb_state oui_state id label state
    adsb_state=OFF
    oui_state=OFF
    while IFS=$'\t' read -r id label state; do
        case "$id" in
            adsb_radar) adsb_state="$state" ;;
            oui_spy) oui_state="$state" ;;
        esac
    done < <(bash "$SCRIPT_DIR/plugin_manager.sh" list)

    selected=$(whiptail --title "Installed Plugins" --separate-output \
        --checklist "Select the plugins you want installed. Deselecting an installed plugin offers to remove it." 16 76 8 \
        "adsb_radar" "ADS-B Radar" "$adsb_state" \
        "oui_spy" "OUI-Spy" "$oui_state" \
        3>&1 1>&2 2>&3)
    status=$?
    [ "$status" -eq 0 ] || return

    for id in adsb_radar oui_spy; do
        if printf '%s\n' "$selected" | grep -Fxq "$id"; then
            if ! bash "$SCRIPT_DIR/plugin_manager.sh" list | awk -F '\t' -v id="$id" '$1 == id && $3 == "ON" { found=1 } END { exit !found }'; then
                whiptail --title "Installed Plugins" --infobox "Installing $id..." 8 42
                if run_logged bash "$SCRIPT_DIR/plugin_manager.sh" install "$id" >/dev/null; then
                    whiptail --title "Installed Plugins" --msgbox "$id installed successfully." 8 48
                else
                    whiptail --title "Installed Plugins" --msgbox "Could not install $id. Check the network, Git, and Python dependency errors, then retry." 10 68
                fi
            fi
        else
            if bash "$SCRIPT_DIR/plugin_manager.sh" list | awk -F '\t' -v id="$id" '$1 == id && $3 == "ON" { found=1 } END { exit !found }'; then
                if whiptail --title "Remove Plugin" --yesno "Remove $id from SpectrumSnek? Its plugin directory will be deleted. This does not remove shared core files." 10 68; then
                    if run_logged bash "$SCRIPT_DIR/plugin_manager.sh" remove "$id" >/dev/null; then
                        whiptail --title "Installed Plugins" --msgbox "$id removed." 8 42
                    else
                        whiptail --title "Installed Plugins" --msgbox "Could not remove $id." 8 42
                    fi
                fi
            fi
        fi
    done
}

rtl_sdr_detected() {
    # Check common RTL2832U-based dongles without opening the device.
    # This avoids briefly stealing the SDR from a running scanner.
    command -v lsusb >/dev/null 2>&1 || return 1
    lsusb 2>/dev/null | grep -Eiq 'ID (0bda:283[1-8]|0bda:0129|1d19:1101|1f4d:b803|1f4d:c803|0458:001a|185b:0620|0ccd:00a9|0ccd:00b3|0ccd:00d3|0ccd:00e0|0ccd:00e1|0ccd:00e2|0ccd:00e3|0ccd:00e4|0ccd:00e5|0ccd:00e6|0ccd:00e7|0ccd:00e8|0ccd:00e9|0ccd:00ea|0ccd:00eb|0ccd:00ec|0ccd:00ed|0ccd:00ef|0ccd:00f0|0ccd:00f1|0ccd:00f2|0ccd:00f3|0ccd:00f4|0ccd:00f5|0ccd:00f6|0ccd:00f7|0ccd:00f8|0ccd:00f9|0ccd:00fa|0ccd:00fb|0ccd:00fc|0ccd:00fd|0ccd:00fe|0ccd:00ff)'
}

wifi_detected() {
    # Detect a driver-backed wireless interface without requiring an active connection.
    for iface in /sys/class/net/*; do
        [ -e "$iface/wireless" ] && return 0
    done
    command -v iw >/dev/null 2>&1 && iw dev 2>/dev/null | grep -q 'Interface '
}

bluetooth_detected() {
    # Look for a registered Bluetooth controller without changing its power state.
    for controller in /sys/class/bluetooth/hci*; do
        [ -e "$controller" ] && return 0
    done
    command -v bluetoothctl >/dev/null 2>&1 && bluetoothctl list 2>/dev/null | grep -q 'Controller '
}

configure_service_menu() {
    while true; do
        service_choice=$(whiptail --title "Configure Web Service" --notags \
            --menu "Manage the SpectrumSnek web service:" 17 74 7 \
            "setup" "Install and enable service at boot" \
            "start" "Start service now" \
            "stop" "Stop service" \
            "restart" "Restart service" \
            "status" "Show service status" \
            "logs" "View recent service logs" \
            "back" "Return to Utilities" \
            3>&1 1>&2 2>&3)
        service_status=$?
        [ "$service_status" -eq 0 ] || return
        case "$service_choice" in
            setup)
                if run_logged bash "$SCRIPT_DIR/setup_service.sh"; then
                    whiptail --title "Configure Web Service" --msgbox "The web service has been installed, enabled at boot, and started." 9 68
                else
                    whiptail --title "Configure Web Service" --msgbox "Service setup failed. Review error.log and setup output." 9 68
                fi
                ;;
            start|stop|restart|status|logs)
                service_output=$(bash "$SCRIPT_DIR/service_manager.sh" "$service_choice" 2>&1)
                service_result=$?
                if [ "$service_choice" = "logs" ] || [ "$service_choice" = "status" ]; then
                    whiptail --title "Web Service: $service_choice" --scrolltext --msgbox "$service_output" 22 78
                elif [ "$service_result" -eq 0 ]; then
                    whiptail --title "Configure Web Service" --msgbox "$service_output" 10 70
                else
                    whiptail --title "Configure Web Service" --msgbox "The service command failed:\n\n$service_output" 12 72
                fi
                ;;
            back) return ;;
        esac
    done
}

utilities_menu() {
    while true; do
        utility_choice=$(whiptail --title "SpectrumSnek Utilities" --notags \
            --menu "Select a utility:" 15 74 6 \
            "update" "Check for and install updates" \
            "plugins" "Installed Plugins" \
            "textual" "Try Textual interface (experimental)" \
            "configure" "Configure web service" \
            "back" "Return to main menu" \
            3>&1 1>&2 2>&3)
        utility_status=$?
        [ "$utility_status" -eq 0 ] || return
        case "$utility_choice" in
            update) update_spectrumsnek ;;
            plugins) installed_plugins_menu ;;
            textual) run_logged "$PYTHON" "$SCRIPT_DIR/textual_menu.py" ;;
            configure) configure_service_menu ;;
            back) return ;;
        esac
    done
}

while true; do
    MENU_ITEMS=(
        "builtin:rtl_scanner" "RTL-SDR Spectrum Listener (Scanner)"
        "builtin:radio_scanner" "Traditional Radio Scanner (Audio)"
        "builtin:wifi" "WiFi Tool"
        "builtin:bluetooth" "Bluetooth Tool"
        "builtin:system_tools" "System Tools"
        "builtin:utilities" "Utilities"
    )

    # Keep internal plugin IDs as hidden tags; show only friendly names.
    while IFS=$'\t' read -r plugin_id plugin_name; do
        [ -n "${plugin_id:-}" ] || continue
        MENU_ITEMS+=("plugin:$plugin_id" "$plugin_name")
    done < <(run_logged "$PYTHON" "$SCRIPT_DIR/plugin_menu.py" --list)

    MENU_PROMPT="Use arrows to navigate and Enter to select:"
    STATUS_LABEL=""
    if rtl_sdr_detected; then STATUS_LABEL="RTL-SDR"; fi
    if wifi_detected; then
        [ -n "$STATUS_LABEL" ] && STATUS_LABEL="${STATUS_LABEL}  "
        STATUS_LABEL="${STATUS_LABEL}WiFi"
    fi
    if bluetooth_detected; then
        [ -n "$STATUS_LABEL" ] && STATUS_LABEL="${STATUS_LABEL}  "
        STATUS_LABEL="${STATUS_LABEL}Bluetooth"
    fi
    if [ -n "$STATUS_LABEL" ]; then
        STATUS_PADDING=$(printf "%*s" "$((74 - ${#STATUS_LABEL}))" "")
        MENU_PROMPT="${MENU_PROMPT}\n${STATUS_PADDING}${STATUS_LABEL}"
    fi

    CHOICE=$(whiptail --title "SpectrumSnek 🐍📻" \
        --notags \
        --menu "$MENU_PROMPT" 22 90 12 \
        "${MENU_ITEMS[@]}" \
        3>&1 1>&2 2>&3)
    STATUS=$?

    if [ "$STATUS" -ne 0 ]; then
        break
    fi

    case "$CHOICE" in
        "builtin:rtl_scanner")
            run_logged "$PYTHON" "$SCRIPT_DIR/plugins/rtl_scanner/scanner.py"
            ;;
        "builtin:radio_scanner")
            run_logged "$PYTHON" "$SCRIPT_DIR/plugins/radio_scanner/scanner.py"
            ;;
        "builtin:wifi")
            run_logged "$PYTHON" "$SCRIPT_DIR/wifi_tool/wifi_selector.py"
            ;;
        "builtin:bluetooth")
            run_logged "$PYTHON" "$SCRIPT_DIR/bluetooth_tool/bluetooth_connector.py"
            ;;
        "builtin:system_tools")
            run_logged "$PYTHON" "$SCRIPT_DIR/plugins/system_tools/system_menu.py"
            ;;
        "builtin:utilities")
            utilities_menu
            ;;
        plugin:*)
            PLUGIN_ID="${CHOICE#plugin:}"
            run_logged "$PYTHON" "$SCRIPT_DIR/plugin_menu.py" --run "$PLUGIN_ID"
            ;;
        *)
            continue
            ;;
    esac

    RESULT=$?
    if [ "$RESULT" -ne 0 ]; then
        printf '\nTool exited with status %s.\n' "$RESULT"
        printf '[%s] [launcher] Selected tool exited with status %s.\n' "$(date '+%Y-%m-%d %H:%M:%S')" "$RESULT" | tee -a "$SCRIPT_DIR/error.log"
    fi
done

clear
echo "Goodbye!"
