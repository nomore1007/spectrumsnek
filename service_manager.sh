#!/bin/bash
# SpectrumSnek web service management.

set -u
SERVICE_NAME="spectrum-service"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if [ "$EUID" -eq 0 ]; then
    SUDO_CMD=()
else
    SUDO_CMD=(sudo)
fi

case "${1:-}" in
    status)
        "${SUDO_CMD[@]}" systemctl status "$SERVICE_NAME" --no-pager -l
        ;;
    start|stop|restart|enable|disable)
        "${SUDO_CMD[@]}" systemctl "$1" "$SERVICE_NAME"
        ;;
    logs)
        "${SUDO_CMD[@]}" journalctl -u "$SERVICE_NAME" --no-pager -n 40
        ;;
    *)
        echo "Usage: $0 {status|start|stop|restart|enable|disable|logs}"
        exit 2
        ;;
esac
