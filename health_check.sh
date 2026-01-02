#!/bin/bash
# SpectrumSnek Service Health Check

echo "========================================"
echo "  SpectrumSnek Service Health Check"
echo "========================================"
echo ""

# Check if service is running via systemd
echo "1. Checking systemd service status..."
if systemctl is-active --quiet spectrum-service 2>/dev/null; then
    echo "✓ Systemd service is active"
    SERVICE_ACTIVE=true
else
    echo "✗ Systemd service is not active"
    SERVICE_ACTIVE=false
fi

# Check if process is running
echo ""
echo "2. Checking for running processes..."
SPECTRUM_PROCESSES=$(ps aux | grep -E "(spectrum|spectrum_service|main.py)" | grep -v grep | grep -v health_check)
if [ -n "$SPECTRUM_PROCESSES" ]; then
    echo "✓ Found running SpectrumSnek processes:"
    echo "$SPECTRUM_PROCESSES"
    PROCESS_RUNNING=true
else
    echo "✗ No SpectrumSnek processes found"
    PROCESS_RUNNING=false
fi

# Check port binding
echo ""
echo "3. Checking port 5000 binding..."
PORT_INFO=$(netstat -tulpn 2>/dev/null | grep :5000)
if [ -n "$PORT_INFO" ]; then
    echo "✓ Port 5000 is bound:"
    echo "$PORT_INFO"
    PORT_BOUND=true
else
    echo "✗ Port 5000 is not bound"
    PORT_BOUND=false
fi

# Test localhost connectivity
echo ""
echo "4. Testing localhost connectivity..."
if timeout 3 bash -c "</dev/tcp/127.0.0.1/5000" 2>/dev/null; then
    echo "✓ Can connect to localhost:5000"
    LOCALHOST_OK=true
else
    echo "✗ Cannot connect to localhost:5000"
    LOCALHOST_OK=false
fi

# Test service API
echo ""
echo "5. Testing service API..."
if command -v curl &> /dev/null; then
    API_RESPONSE=$(curl -s --max-time 3 http://127.0.0.1:5000/api/status 2>/dev/null)
    if [ -n "$API_RESPONSE" ]; then
        echo "✓ API responding:"
        echo "$API_RESPONSE" | python3 -c "import sys, json; print(json.dumps(json.load(sys.stdin), indent=2))" 2>/dev/null || echo "$API_RESPONSE"
        API_OK=true
    else
        echo "✗ API not responding"
        API_OK=false
    fi
else
    echo "⚠ curl not available, skipping API test"
    API_OK="unknown"
fi

# Summary and recommendations
echo ""
echo "========================================"
echo "  DIAGNOSIS SUMMARY"
echo "========================================"

ISSUES_FOUND=false

if [ "$SERVICE_ACTIVE" = false ]; then
    echo "❌ Service not active via systemd"
    echo "   → Start with: ./service_manager.sh start"
    ISSUES_FOUND=true
fi

if [ "$PROCESS_RUNNING" = false ]; then
    echo "❌ No SpectrumSnek processes running"
    echo "   → Start service or run manually: ./run_spectrum.sh --service"
    ISSUES_FOUND=true
fi

if [ "$PORT_BOUND" = false ]; then
    echo "❌ Port 5000 not bound"
    echo "   → Service may not be listening on correct interface"
    echo "   → Check: ./service_manager.sh status"
    ISSUES_FOUND=true
fi

if [ "$LOCALHOST_OK" = false ]; then
    echo "❌ Cannot connect to localhost:5000"
    echo "   → Firewall blocking local connections?"
    echo "   → Service bound to wrong interface (127.0.0.1 vs 0.0.0.0)?"
    ISSUES_FOUND=true
fi

if [ "$API_OK" = false ]; then
    echo "❌ Service API not responding"
    echo "   → Service may be starting up or crashed"
    echo "   → Check logs: ./service_manager.sh logs"
    ISSUES_FOUND=true
fi

if [ "$ISSUES_FOUND" = false ]; then
    echo "✅ All checks passed - service appears healthy!"
    echo ""
    echo "If clients still can't connect:"
    echo "  • Try restarting the service: ./service_manager.sh restart"
    echo "  • Check client logs: ~/spectrum_startup.log"
    echo "  • Verify client is using correct URL: http://127.0.0.1:5000"
fi

echo ""
echo "Quick fixes:"
echo "  Restart service: ./service_manager.sh restart"
echo "  Check logs:      ./service_manager.sh logs"
echo "  Test client:     ./run_spectrum.sh"
echo "  Manual start:    ./run_spectrum.sh --service --host 0.0.0.0"