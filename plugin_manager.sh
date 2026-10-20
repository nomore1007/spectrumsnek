#!/usr/bin/env bash
# Install, update, list, and remove the known SpectrumSnek plugins.
set -u

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PLUGINS_DIR="$SCRIPT_DIR/plugins"
VENV_PIP="$SCRIPT_DIR/venv/bin/pip"

plugin_repo() {
    case "$1" in
        adsb_radar) printf '%s\n' "https://github.com/nomore1007/spectrumsnek-adsb.git" ;;
        oui_spy) printf '%s\n' "https://github.com/nomore1007/spectrumsnek-oui-spy.git" ;;
        *) return 1 ;;
    esac
}

plugin_label() {
    case "$1" in
        adsb_radar) printf '%s\n' "ADS-B Radar" ;;
        oui_spy) printf '%s\n' "OUI-Spy" ;;
        *) return 1 ;;
    esac
}

plugin_is_installed() {
    [ -f "$PLUGINS_DIR/$1/__init__.py" ]
}

install_plugin() {
    local id="$1" repo target current_remote
    repo="$(plugin_repo "$id")" || {
        echo "Unknown plugin: $id" >&2
        return 2
    }
    target="$PLUGINS_DIR/$id"
    mkdir -p "$PLUGINS_DIR" || return 1

    if [ -d "$target/.git" ]; then
        current_remote="$(git -C "$target" remote get-url origin 2>/dev/null || true)"
        if [ "$current_remote" != "$repo" ]; then
            echo "Refusing to update $target: its origin is not the known plugin repository." >&2
            return 1
        fi
        echo "Updating $(plugin_label "$id")..."
        if ! git -C "$target" pull --ff-only origin main; then
            echo "Could not fast-forward $(plugin_label "$id"). Resolve its checkout and retry." >&2
            return 1
        fi
    elif [ -e "$target" ]; then
        echo "Refusing to overwrite existing non-Git plugin directory: $target" >&2
        echo "Back it up or remove it manually, then retry." >&2
        return 1
    else
        echo "Installing $(plugin_label "$id")..."
        if ! git clone --depth 1 --branch main "$repo" "$target"; then
            rm -rf -- "$target"
            echo "Failed to clone $(plugin_label "$id")." >&2
            return 1
        fi
    fi

    if [ -f "$target/requirements.txt" ]; then
        if [ -x "$VENV_PIP" ]; then
            "$VENV_PIP" install -r "$target/requirements.txt" || return 1
        else
            python3 -m pip install -r "$target/requirements.txt" || return 1
        fi
    fi
    echo "$(plugin_label "$id") is installed."
}

remove_plugin() {
    local id="$1" target
    plugin_repo "$id" >/dev/null || {
        echo "Unknown plugin: $id" >&2
        return 2
    }
    target="$PLUGINS_DIR/$id"
    if [ ! -e "$target" ]; then
        echo "$(plugin_label "$id") is not installed."
        return 0
    fi
    case "$(realpath -m "$target")" in
        "$PLUGINS_DIR/"*) ;;
        *) echo "Refusing to remove a path outside the plugins directory." >&2; return 1 ;;
    esac
    rm -rf -- "$target" || return 1
    echo "$(plugin_label "$id") was removed."
}

case "${1:-list}" in
    list)
        for id in adsb_radar oui_spy; do
            if plugin_is_installed "$id"; then state=ON; else state=OFF; fi
            printf '%s\t%s\t%s\n' "$id" "$(plugin_label "$id")" "$state"
        done
        ;;
    install)
        [ "$#" -eq 2 ] || { echo "Usage: $0 install <adsb_radar|oui_spy>" >&2; exit 2; }
        install_plugin "$2"
        ;;
    remove)
        [ "$#" -eq 2 ] || { echo "Usage: $0 remove <adsb_radar|oui_spy>" >&2; exit 2; }
        remove_plugin "$2"
        ;;
    *)
        echo "Usage: $0 {list|install <plugin>|remove <plugin>}" >&2
        exit 2
        ;;
esac
