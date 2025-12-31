#!/bin/bash
# SpectrumSnek Service Management Script

SERVICE_NAME="spectrum-service"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "SpectrumSnek Service Manager"
echo "============================"

# Check if running as root for service operations
if [ "$EUID" -eq 0 ]; then
    SUDO_CMD=""
else
    SUDO_CMD="sudo"
fi

case "$1" in
    status)
        echo "Service Status:"
        $SUDO_CMD systemctl status $SERVICE_NAME --no-pager -l
        echo ""
        echo "Process Check:"
        ps aux | grep -E "(spectrum|spectrum_service|main.py)" | grep -v grep || echo "No SpectrumSnek processes found"
        echo ""
        echo "Port Check:"
        netstat -tulpn 2>/dev/null | grep :5000 || echo "Port 5000 not in use"
        ;;

    start)
        echo "Starting SpectrumSnek service..."
        $SUDO_CMD systemctl start $SERVICE_NAME
        sleep 2
        $SUDO_CMD systemctl status $SERVICE_NAME --no-pager
        ;;

    stop)
        echo "Stopping SpectrumSnek service..."
        $SUDO_CMD systemctl stop $SERVICE_NAME
        $SUDO_CMD systemctl status $SERVICE_NAME --no-pager
        ;;

    restart)
        echo "Restarting SpectrumSnek service..."
        $SUDO_CMD systemctl restart $SERVICE_NAME
        sleep 2
        $SUDO_CMD systemctl status $SERVICE_NAME --no-pager
        ;;

    enable)
        echo "Enabling SpectrumSnek service to start on boot..."
        $SUDO_CMD systemctl enable $SERVICE_NAME
        ;;

    disable)
        echo "Disabling SpectrumSnek service from starting on boot..."
        $SUDO_CMD systemctl disable $SERVICE_NAME
        ;;

    logs)
        echo "Recent service logs:"
        $SUDO_CMD journalctl -u $SERVICE_NAME --no-pager -n 20
        ;;

    *)
        echo "Usage: $0 {status|start|stop|restart|enable|disable|logs}"
        echo ""
        echo "Commands:"
        echo "  status   - Show service status and processes"
        echo "  start    - Start the service"
        echo "  stop     - Stop the service"
        echo "  restart  - Restart the service"
        echo "  enable   - Enable service to start on boot"
        echo "  disable  - Disable service from starting on boot"
        echo "  logs     - Show recent service logs"
        echo ""
        echo "Manual control:"
        echo "  ./run_spectrum.sh --service  # Start manually"
        echo "  pkill -f spectrum_service    # Kill running instances"
        exit 1
        ;;
esac