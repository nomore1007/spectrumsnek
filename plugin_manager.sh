#!/usr/bin/env bash
# Install, update, list, and remove SpectrumSnek plugins.
set -u

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PLUGINS_DIR="$SCRIPT_DIR/plugins"
VENV_PIP="$SCRIPT_DIR/venv/bin/pip"
BUILTIN_PLUGINS=" rtl_scanner radio_scanner system_tools "

plugin_repo() {
    case "$1" in
        adsb_radar) printf '%s\n' "https://github.com/nomore1007/spectrumsnek-adsb.git" ;;
        oui_spy) printf '%s\n' "https://github.com/nomore1007/spectrumsnek-oui-spy.git" ;;
        lora_monitor) printf '%s\n' "https://github.com/nomore1007/spectrumsnek-lora.git" ;;
        analyzer) printf '%s\n' "https://github.com/nomore1007/spectrumsnek-analyzer.git" ;;
        scanner) printf '%s\n' "https://github.com/nomore1007/spectrumsnek-scanner.git" ;;
        *) return 1 ;;
    esac
}

plugin_label() {
    case "$1" in
        adsb_radar) printf '%s\n' "ADS-B Radar" ;;
        oui_spy) printf '%s\n' "OUI-Spy" ;;
        lora_monitor) printf '%s\n' "LoRa Monitor" ;;
        analyzer) printf '%s\n' "Analyzer" ;;
        scanner) printf '%s\n' "Radio Scanner" ;;
        *) printf '%s\n' "$1" ;;
    esac
}

plugin_is_installed() {
    [ -f "$PLUGINS_DIR/$1/__init__.py" ]
}

install_requirements() {
    local target="$1"
    [ -f "$target/requirements.txt" ] || return 0
    if [ -x "$VENV_PIP" ]; then
        "$VENV_PIP" install -r "$target/requirements.txt"
    else
        python3 -m pip install -r "$target/requirements.txt"
    fi
}

plugin_id_from_url() {
    local url="$1" path repo
    # Only accept normal HTTPS GitHub repository URLs, not arbitrary Git remotes.
    [[ "$url" =~ ^https://github\.com/[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+/?$ ]] || \
        [[ "$url" =~ ^https://github\.com/[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+\.git$ ]] || return 1
    path="${url#https://github.com/}"
    path="${path%/}"
    path="${path%.git}"
    repo="${path##*/}"
    repo="${repo%.git}"
    case "$path" in
        nomore1007/spectrumsnek-adsb) printf '%s\n' adsb_radar; return 0 ;;
        nomore1007/spectrumsnek-oui-spy) printf '%s\n' oui_spy; return 0 ;;
        nomore1007/spectrumsnek-lora) printf '%s\n' lora_monitor; return 0 ;;
        nomore1007/spectrumsnek-analyzer) printf '%s\n' analyzer; return 0 ;;
        nomore1007/spectrumsnek-scanner) printf '%s\n' scanner; return 0 ;;
    esac
    repo="${repo//-/_}"
    [[ "$repo" =~ ^[A-Za-z][A-Za-z0-9_]*$ ]] || return 1
    case "$BUILTIN_PLUGINS" in *" $repo "*) return 1 ;; esac
    printf '%s\n' "$repo"
}

install_plugin() {
    local id="$1" repo target current_remote
    repo="$(plugin_repo "$id")" || {
        echo "Unknown known plugin: $id" >&2
        return 2
    }
    install_from_url "$repo" "$id"
}

install_from_url() {
    local url="$1" id="$2" branch="${3:-}" target current_remote cloned=0
    target="$PLUGINS_DIR/$id"
    mkdir -p "$PLUGINS_DIR" || return 1

    if [ -d "$target/.git" ]; then
        current_remote="$(git -C "$target" remote get-url origin 2>/dev/null || true)"
        if [ "$current_remote" != "$url" ] && [ "$current_remote" != "${url%.git}" ] && [ "$current_remote" != "${url%.git}.git" ]; then
            echo "Refusing to update $target: its origin does not match $url." >&2
            return 1
        fi
        if [ -n "$branch" ]; then
            fetch_plugin_branch_ref "$target" "$branch" || return 1
            checkout_plugin_branch "$target" "$branch" || return 1
            git -C "$target" pull --ff-only origin "$branch" || return 1
        else
            echo "Updating $(plugin_label "$id")..."
            git -C "$target" pull --ff-only || {
                echo "Could not fast-forward $(plugin_label "$id"). Check its Git state and upstream." >&2
                return 1
            }
        fi
    elif [ -e "$target" ]; then
        echo "Refusing to overwrite existing non-Git plugin directory: $target" >&2
        echo "Back it up or remove it manually, then retry." >&2
        return 1
    else
        echo "Installing $(plugin_label "$id") from $url..."
        if [ -n "$branch" ]; then
            if ! git clone --depth 1 --single-branch --branch "$branch" "$url" "$target"; then
                rm -rf -- "$target"
                echo "Failed to clone plugin branch $branch." >&2
                return 1
            fi
        elif ! git clone --depth 1 "$url" "$target"; then
            rm -rf -- "$target"
            echo "Failed to clone plugin repository." >&2
            return 1
        fi
        cloned=1
    fi

    if [ ! -f "$target/__init__.py" ]; then
        echo "Plugin repository must provide __init__.py at its root: $target" >&2
        if [ "$cloned" -eq 1 ]; then
            rm -rf -- "$target"
        fi
        return 1
    fi
    install_requirements "$target" || return 1
    echo "$(plugin_label "$id") is installed at plugins/$id."
}

list_branches() {
    local url="$1"
    git ls-remote --heads "$url" 2>/dev/null | sed -E 's#^[^[:space:]]+[[:space:]]+refs/heads/##' | sort -u
}

fetch_plugin_branch_ref() {
    local target="$1" branch="$2"
    # Force-update the exact remote-tracking ref, including slash-containing names.
    git -C "$target" fetch origin "+refs/heads/$branch:refs/remotes/origin/$branch" || return 1
    git -C "$target" show-ref --verify --quiet "refs/remotes/origin/$branch" || {
        echo "Fetched branch but remote-tracking ref is missing: origin/$branch" >&2
        return 1
    }
}

checkout_plugin_branch() {
    local target="$1" branch="$2"
    if git -C "$target" show-ref --verify --quiet "refs/heads/$branch"; then
        git -C "$target" switch "$branch" || return 1
    else
        # Create the local branch from the fetched commit first, then configure
        # upstream separately. This avoids coupling branch creation to Git's
        # automatic tracking inference for a fully qualified start-point.
        git -C "$target" switch --no-track -c "$branch" "refs/remotes/origin/$branch" || return 1
        git -C "$target" branch --set-upstream-to="origin/$branch" "$branch" || return 1
    fi
}

change_plugin_branch() {
    local id="$1" branch="$2" target current_remote expected_remote
    [[ "$branch" =~ ^[A-Za-z0-9][A-Za-z0-9._/-]*$ ]] || { echo "Invalid branch name: $branch" >&2; return 2; }
    target="$PLUGINS_DIR/$id"
    [ -d "$target/.git" ] || { echo "$id is not installed as a Git checkout." >&2; return 1; }
    expected_remote="$(plugin_repo "$id" 2>/dev/null || true)"
    current_remote="$(git -C "$target" remote get-url origin 2>/dev/null || true)"
    if [ -n "$expected_remote" ] && [ "$current_remote" != "$expected_remote" ]; then
        echo "Refusing to change branch: origin is $current_remote, expected $expected_remote." >&2
        return 1
    fi
    fetch_plugin_branch_ref "$target" "$branch" || return 1
    checkout_plugin_branch "$target" "$branch" || return 1
    git -C "$target" pull --ff-only origin "$branch" || return 1
    install_requirements "$target" || return 1
    echo "$id now uses branch $branch."
}

update_plugin_dir() {
    local id="$1" branch="${2:-}" target expected_remote current_remote
    target="$PLUGINS_DIR/$id"
    [ -d "$target/.git" ] || {
        echo "$id is not a Git checkout; cannot pull updates." >&2
        return 1
    }
    expected_remote="$(plugin_repo "$id" 2>/dev/null || true)"
    current_remote="$(git -C "$target" remote get-url origin 2>/dev/null || true)"
    if [ -n "$expected_remote" ] && [ "$current_remote" != "$expected_remote" ]; then
        echo "Refusing to update $id: origin is $current_remote, expected $expected_remote." >&2
        return 1
    fi
    if [ -n "$branch" ]; then
        change_plugin_branch "$id" "$branch"
        return $?
    fi
    echo "Updating $(plugin_label "$id")..."
    git -C "$target" pull --ff-only || return 1
    install_requirements "$target" || return 1
    echo "$(plugin_label "$id") is up to date."
}

remove_plugin() {
    local id="$1" target
    [[ "$id" =~ ^[A-Za-z][A-Za-z0-9_]*$ ]] || {
        echo "Invalid plugin ID: $id" >&2
        return 2
    }
    case "$BUILTIN_PLUGINS" in *" $id "*) echo "Refusing to remove built-in plugin $id." >&2; return 1 ;; esac
    target="$PLUGINS_DIR/$id"
    if [ ! -e "$target" ]; then
        echo "$(plugin_label "$id") is not installed."
        return 0
    fi
    [ -d "$target" ] || { echo "Plugin path is not a directory: $target" >&2; return 1; }
    case "$(realpath -m "$target")" in
        "$PLUGINS_DIR/"*) ;;
        *) echo "Refusing to remove a path outside the plugins directory." >&2; return 1 ;;
    esac
    rm -rf -- "$target" || return 1
    echo "$(plugin_label "$id") was removed."
}

case "${1:-list}" in
    list)
        # Stable TSV protocol retained for the existing Whiptail checklist.
        for id in adsb_radar oui_spy lora_monitor analyzer scanner; do
            if plugin_is_installed "$id"; then state=ON; else state=OFF; fi
            printf '%s\t%s\t%s\n' "$id" "$(plugin_label "$id")" "$state"
        done
        ;;
    branches)
        [ "$#" -eq 2 ] || { echo "Usage: $0 branches <plugin-id>" >&2; exit 2; }
        repo="$(plugin_repo "$2" 2>/dev/null || true)"
        if [ -z "$repo" ]; then
            repo="$(git -C "$PLUGINS_DIR/$2" remote get-url origin 2>/dev/null || true)"
        fi
        [ -n "$repo" ] || { echo "Cannot determine repository for $2." >&2; exit 1; }
        list_branches "$repo"
        ;;
    install)
        [ "$#" -ge 2 ] && [ "$#" -le 3 ] || { echo "Usage: $0 install <adsb_radar|oui_spy|lora_monitor|analyzer|scanner> [branch]" >&2; exit 2; }
        repo="$(plugin_repo "$2")" || { echo "Unknown known plugin: $2" >&2; exit 2; }
        install_from_url "$repo" "$2" "${3:-}"
        ;;
    install-url)
        [ "$#" -ge 2 ] && [ "$#" -le 3 ] || { echo "Usage: $0 install-url <https://github.com/owner/repo> [branch]" >&2; exit 2; }
        id="$(plugin_id_from_url "$2")" || {
            echo "Invalid URL. Use https://github.com/owner/repository (GitHub repositories only)." >&2
            exit 2
        }
        install_from_url "$2" "$id" "${3:-}"
        ;;
    branch)
        [ "$#" -eq 3 ] || { echo "Usage: $0 branch <plugin-id> <branch>" >&2; exit 2; }
        change_plugin_branch "$2" "$3"
        ;;
    update)
        [ "$#" -ge 2 ] && [ "$#" -le 3 ] || { echo "Usage: $0 update <plugin-id|all> [branch]" >&2; exit 2; }
        if [ "$2" = all ]; then
            failed=0
            found=0
            for target in "$PLUGINS_DIR"/*; do
                [ -d "$target/.git" ] || continue
                id="${target##*/}"
                found=1
                update_plugin_dir "$id" || failed=1
            done
            [ "$found" -eq 1 ] || echo "No Git-based plugins are installed."
            [ "$failed" -eq 0 ] || exit 1
        else
            [[ "$2" =~ ^[A-Za-z][A-Za-z0-9_]*$ ]] || { echo "Invalid plugin ID: $2" >&2; exit 2; }
            update_plugin_dir "$2" "${3:-}"
        fi
        ;;
    remove)
        [ "$#" -eq 2 ] || { echo "Usage: $0 remove <plugin-id>" >&2; exit 2; }
        remove_plugin "$2"
        ;;
    *)
        echo "Usage: $0 {list|branches <plugin-id>|install <known-plugin> [branch]|install-url <GitHub-URL> [branch]|branch <plugin-id> <branch>|update <plugin-id|all> [branch]|remove <plugin-id>}" >&2
        exit 2
        ;;
esac
