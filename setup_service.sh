#!/bin/bash
# SpectrumSnek Service Setup Script
# Run with sudo to set up the systemd service

echo "Setting up SpectrumSnek systemd service..."

# Create systemd service file
cat > /etc/systemd/system/spectrum-service.service << 'EOF'
[Unit]
Description=SpectrumSnek Service 🐍📻
After=network.target bluetooth.service

[Service]
Type=simple
User=nomore
WorkingDirectory=/home/nomore/SpectrumSnek
ExecStart=/home/nomore/SpectrumSnek/venv/bin/python /home/nomore/SpectrumSnek/main.py --service --host 0.0.0.0 --port 5000
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