#!/bin/bash
# Fix SpectrumSnek systemd service

echo "Creating SpectrumSnek systemd service file..."

# Create systemd service file
cat > /etc/systemd/system/spectrum-service.service << 'SERVICE_EOF'
[Unit]
Description=SpectrumSnek Service 🐍📻
After=network.target bluetooth.service

[Service]
Type=simple
User=nomore
WorkingDirectory=/home/nomore/SpectrumSnek
ExecStart=/home/nomore/SpectrumSnek/run_spectrum.sh --service --host 0.0.0.0 --port 5000
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
SERVICE_EOF

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
echo "🎉 SpectrumSnek service is now properly configured!"
echo "The console client should now connect to the service on boot."
