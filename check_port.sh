#!/bin/bash
# SpectrumSnek Port Check and Cleanup Script

PORT=5000
echo "Checking port $PORT usage..."

# Check what's using the port
echo "Processes using port $PORT:"
netstat -tulpn 2>/dev/null | grep ":$PORT " || echo "No processes found using netstat"

# Try lsof if available
if command -v lsof &> /dev/null; then
    echo ""
    echo "lsof output for port $PORT:"
    lsof -i :$PORT 2>/dev/null || echo "No processes found using lsof"
fi

echo ""
echo "SpectrumSnek-related processes:"
ps aux | grep -E "(spectrum|spectrum_service|main.py)" | grep -v grep || echo "No SpectrumSnek processes found"

echo ""
echo "Options to free port $PORT:"
echo "1. Kill existing SpectrumSnek processes:"
echo "   pkill -f spectrum_service"
echo "   pkill -f 'python main.py'"
echo ""
echo "2. Kill all processes using port $PORT:"
echo "   fuser -k $PORT/tcp 2>/dev/null || echo 'fuser not available'"
echo ""
echo "3. Use a different port:"
echo "   python main.py --service --port 5001"
echo ""
echo "4. Check systemd services:"
echo "   sudo systemctl list-units | grep spectrum"

echo ""
read -p "Do you want me to kill existing SpectrumSnek processes? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "Killing SpectrumSnek processes..."
    pkill -f spectrum_service
    pkill -f "python main.py"
    pkill -f "python3 main.py"
    sleep 2
    echo "Done. Try running SpectrumSnek again."
else
    echo "No processes killed. Use a different port or manually kill processes."
fi