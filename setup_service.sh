#!/bin/bash
# SpectrumSnek Service Setup Script
# Run with sudo to set up the systemd service

echo "Setting up SpectrumSnek systemd service..."

# Detect the actual SpectrumSnek directory path
SPECTRUM_DIR=$(find /home -maxdepth 2 -type d -iname "*spectrum*" -exec test -x "{}/run_spectrum.sh" \; -print | head -1)
if [ -z "$SPECTRUM_DIR" ]; then
    echo "ERROR: Cannot find SpectrumSnek directory with run_spectrum.sh"
    echo "Make sure you're in the SpectrumSnek directory or it exists in /home"
    exit 1
fi

echo "Found SpectrumSnek directory: $SPECTRUM_DIR"

# Get the actual username
SERVICE_USER=${USER:-nomore}

# Create systemd service file
cat > /etc/systemd/system/spectrum-service.service << EOF
[Unit]
Description=SpectrumSnek Service 🐍📻
After=network.target bluetooth.service

[Service]
Type=simple
User=$SERVICE_USER
WorkingDirectory=$SPECTRUM_DIR
ExecStart=$SPECTRUM_DIR/run_spectrum.sh --service --host 0.0.0.0 --port 5000
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

echo "✓ Service file created"

# Reload systemd
systemctl daemon-reload
echo "✓ Systemd reloaded"

# Enable and start service
systemctl enable spectrum-service.service
echo "✓ Service enabled"

systemctl start spectrum-service.service
echo "✓ Service started"

# Check status
echo ""
echo "Service status:"
systemctl status spectrum-service.service --no-pager -l

echo ""
echo "🎉 SpectrumSnek service is now set up and running!"
echo "The console client should now connect to the service at boot."