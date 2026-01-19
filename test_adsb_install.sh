#!/bin/bash
echo "ADS-B Installation Test Script"
echo "=============================="
echo ""

# Check if dump1090-mutability is installed
echo "Checking for ADS-B decoder..."
if command -v dump1090-mutability &> /dev/null; then
    echo "✅ dump1090-mutability is installed"
    echo ""
    echo "Testing ADS-B functionality..."
    python3 -c "
import plugins.adsb_tool.adsb_service as service
s = service.ADSBService()
result = s._check_readsb()
print(f'Decoder detection: {result}')
if result:
    print('✅ ADS-B system ready for real aircraft data!')
else:
    print('❌ Decoder detection failed')
"
elif command -v readsb &> /dev/null; then
    echo "✅ readsb is installed"
    echo "ADS-B system should work"
elif command -v dump1090-fa &> /dev/null; then
    echo "✅ dump1090-fa is installed"  
    echo "ADS-B system should work"
elif command -v dump1090 &> /dev/null; then
    echo "✅ dump1090 is installed"
    echo "ADS-B system should work"
else
    echo "❌ No ADS-B decoder found"
    echo ""
    echo "To install, run:"
    echo "sudo ./setup.sh --full"
    echo ""
    echo "Or manually:"
    echo "sudo apt install dump1090-mutability"
fi

echo ""
echo "Test completed."
