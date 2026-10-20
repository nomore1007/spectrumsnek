#!/bin/bash
# SpectrumSnek Whiptail Launcher & Menu
# Installed plugins are discovered automatically from plugins/*/__init__.py.

set -u

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# Keep stderr visible while recording timestamped diagnostics for later review.
exec 2> >(while IFS= read -r error_line; do
    printf '[%s] [launcher] %s\n' "$(date '+%Y-%m-%d %H:%M:%S')" "$error_line" | tee -a "$SCRIPT_DIR/error.log" >&2
done)
VENV_DIR="$SCRIPT_DIR/venv"
PYTHON="python3"

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
    if ! git -C "$SCRIPT_DIR" fetch origin master; then
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
        if ! git -C "$SCRIPT_DIR" reset --hard origin/master; then
            whiptail --title "Update SpectrumSnek" --msgbox "Could not reset the checkout to origin/master. Inspect Git status before retrying." 10 72
            return
        fi
        if ! git -C "$SCRIPT_DIR" clean -fd; then
            whiptail --title "Update SpectrumSnek" --msgbox "The tracked files were updated, but some untracked files could not be removed. Inspect Git status." 10 72
            return
        fi
        whiptail --title "Update SpectrumSnek" --msgbox "Update installed successfully. Local tracked changes were overwritten and untracked non-ignored files were removed. Ignored files were preserved. Restart SpectrumSnek to use the newest launcher." 12 76
        return
    fi

    if whiptail --title "Update SpectrumSnek" --yesno "GitHub has $behind new commit(s). Install the update now?" 10 64; then
        if git -C "$SCRIPT_DIR" pull --ff-only origin master; then
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
                if bash "$SCRIPT_DIR/plugin_manager.sh" install "$id" >/dev/null; then
                    whiptail --title "Installed Plugins" --msgbox "$id installed successfully." 8 48
                else
                    whiptail --title "Installed Plugins" --msgbox "Could not install $id. Check the network, Git, and Python dependency errors, then retry." 10 68
                fi
            fi
        else
            if bash "$SCRIPT_DIR/plugin_manager.sh" list | awk -F '\t' -v id="$id" '$1 == id && $3 == "ON" { found=1 } END { exit !found }'; then
                if whiptail --title "Remove Plugin" --yesno "Remove $id from SpectrumSnek? Its plugin directory will be deleted. This does not remove shared core files." 10 68; then
                    if bash "$SCRIPT_DIR/plugin_manager.sh" remove "$id" >/dev/null; then
                        whiptail --title "Installed Plugins" --msgbox "$id removed." 8 42
                    else
                        whiptail --title "Installed Plugins" --msgbox "Could not remove $id." 8 42
                    fi
                fi
            fi
        fi
    done
}

utilities_menu() {
    while true; do
        utility_choice=$(whiptail --title "SpectrumSnek Utilities" --notags \
            --menu "Select a utility:" 14 72 5 \
            "update" "Check for and install updates" \
            "plugins" "Installed Plugins" \
            "back" "Return to main menu" \
            3>&1 1>&2 2>&3)
        utility_status=$?
        [ "$utility_status" -eq 0 ] || return
        case "$utility_choice" in
            update) update_spectrumsnek ;;
            plugins) installed_plugins_menu ;;
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
    done < <("$PYTHON" "$SCRIPT_DIR/plugin_menu.py" --list)

    CHOICE=$(whiptail --title "SpectrumSnek 🐍📻" \
        --notags \
        --menu "Use arrows to navigate and Enter to select:" 22 90 12 \
        "${MENU_ITEMS[@]}" \
        3>&1 1>&2 2>&3)
    STATUS=$?

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
        "builtin:utilities")
            utilities_menu
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
done

clear
echo "Goodbye!"
