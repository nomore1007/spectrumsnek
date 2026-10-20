#!/bin/bash
# Install and enable the SpectrumSnek web service.
# This script is intended to be called from Utilities -> Configure.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SERVICE_FILE="/etc/systemd/system/spectrum-service.service"

if [ "$EUID" -ne 0 ]; then
    exec sudo -E bash "$SCRIPT_DIR/setup_service.sh"
fi

if [ ! -x "$SCRIPT_DIR/venv/bin/python" ]; then
    echo "ERROR: Python virtual environment not found at $SCRIPT_DIR/venv"
    echo "Run ./setup.sh before configuring the web service."
    exit 1
fi

SERVICE_USER="$(stat -c '%U' "$SCRIPT_DIR")"
if [ -z "$SERVICE_USER" ] || [ "$SERVICE_USER" = "root" ]; then
    SERVICE_USER="${SUDO_USER:-nomore}"
fi

cat > "$SERVICE_FILE" <<EOF
[Unit]
Description=SpectrumSnek Web Service
After=network.target bluetooth.service

[Service]
Type=simple
User=$SERVICE_USER
WorkingDirectory=$SCRIPT_DIR
ExecStart=$SCRIPT_DIR/venv/bin/python $SCRIPT_DIR/spectrum_service.py
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable spectrum-service.service
systemctl restart spectrum-service.service
systemctl --no-pager --full status spectrum-service.service

echo
echo "SpectrumSnek web service is enabled and running."
echo "Open http://<raspberry-pi-address>:5000 from a device on the same network."
