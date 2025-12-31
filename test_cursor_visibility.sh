#!/bin/bash
# Test cursor visibility after RTL-SDR scanner

echo "Testing cursor visibility after RTL-SDR scanner..."
echo "Current cursor should be visible."

# Run the scanner for 2 seconds
echo "Running scanner for 2 seconds..."
timeout 2 ./run_scanner.sh --interactive --freq 100 --gain auto 2>/dev/null

# Check if we're back to normal
echo ""
echo "Scanner finished. Cursor should be visible now."
echo "If cursor is not visible, you can run: reset"
echo "Test complete."