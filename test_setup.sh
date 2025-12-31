#!/bin/bash
# Test RTL-SDR setup and permissions

echo "Testing RTL-SDR setup..."

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found. Run ./setup.sh first."
    exit 1
fi

# Activate virtual environment
source venv/bin/activate

echo "Checking Python dependencies..."
python -c "import rtlsdr, numpy, matplotlib, scipy; print('✅ All Python dependencies installed')"

echo "Checking RTL-SDR device permissions..."
if lsusb | grep -q "RTL2838\|RTL2832"; then
    echo "✅ RTL-SDR USB device detected"
else
    echo "❌ No RTL-SDR USB device detected"
    echo "   Make sure your RTL-SDR dongle is plugged in"
    exit 1
fi

echo "Testing RTL-SDR access..."
python -c "
try:
    from rtlsdr import RtlSdr
    sdr = RtlSdr()
    print('✅ RTL-SDR device accessible')
    print('   Device info:', sdr.get_tuner_type(), 'tuner')
    sdr.close()
except Exception as e:
    print('❌ Cannot access RTL-SDR device')
    print('   Error:', e)
    print('')
    print('   Solutions:')
    print('   1. Install udev rules: sudo ./install_udev_rules.sh')
    print('   2. Add your user to the plugdev group: sudo usermod -a -G plugdev \$USER')
    print('   3. Reboot or unplug/re-plug the device')
    import sys
    sys.exit(1)
"

echo ""
echo "🎉 RTL-SDR setup test passed! You can now run:"
echo "   ./run_scanner.sh --freq 100 --mode spectrum"