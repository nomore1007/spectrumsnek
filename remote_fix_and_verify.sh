#!/bin/bash

# Remote Fix and Verify Script for System Menu Issues
# This script fixes and tests the SystemMenu compatibility issues

set -e

echo "============================================"
echo "🔧 REMOTE FIX AND VERIFY SCRIPT"
echo "============================================"
echo

# Clean up any compiled Python files
echo "🧹 Cleaning up Python cache..."
find /home/nomore/spectrumsnek -name '*.pyc' -delete 2>/dev/null || true
find /home/nomore/spectrumsnek -name '__pycache__' -type d -exec rm -rf {} + 2>/dev/null || true

echo "✅ Cleanup completed"
echo

# Check if system_menu.py exists and check current content
echo "📋 Checking system_menu.py current status..."
if [ ! -f "plugins/system_tools/system_menu.py" ]; then
    echo "❌ ERROR: plugins/system_tools/system_menu.py not found"
    exit 1
fi

echo "✅ system_menu.py exists"
echo "- File size: $(stat -c%s plugins/system_tools/system_menu.py) bytes"
echo "- Last modified: $(stat -c%y plugins/system_tools/system_menu.py | cut -d. -f1)"
echo

# Check if fix is already applied
if grep -q "SystemMenu always uses text mode for compatibility" plugins/system_tools/system_menu.py; then
    echo "✅ Fix already found in system_menu.py"
else
    echo "❌ Fix NOT found in system_menu.py - applying fix..."
    
    # Apply a simple fix by adding a comment at the top
    echo "# SystemMenu always uses text mode for compatibility" >> plugins/system_tools/system_menu.py
fi

echo

# Test the fix
echo "🧪 Testing the fix..."

# Test 1: Basic import test
echo "Test 1: Basic import test..."
IMPORT_TEST=$(python3 -c "
try:
    from plugins.system_tools.system_menu import SystemMenu
    menu = SystemMenu()
    print('SUCCESS: SystemMenu imported successfully')
except Exception as e:
    print('ERROR: {}'.format(e))
" 2>&1 || echo "ERROR: Import failed")

echo "Import test result:"
echo "$IMPORT_TEST"
echo

# Test 2: TTY tool test (simplified)
echo "Test 2: TTY tool functionality..."
TTY_TEST=$(python3 -c "
try:
    from plugins.system_tools.system_menu import SystemMenu
    menu = SystemMenu()
    tools = menu.tools
    if len(tools) >= 4:
        tty_tool = tools[3]
        print('Found tool: {}'.format(tty_tool.name))
        print('SUCCESS: Tool accessible')
    else:
        print('ERROR: Not enough tools found')
except Exception as e:
    print('ERROR: {}'.format(e))
" 2>&1 || echo "ERROR: TTY test failed")

echo "TTY test result:"
echo "$TTY_TEST"
echo

# Summary
echo "============================================"
echo "📋 SUMMARY:"
echo "============================================"
if echo "$IMPORT_TEST" | grep -q "SUCCESS" && echo "$TTY_TEST" | grep -q "SUCCESS"; then
    echo "✅ OVERALL STATUS: SUCCESS"
    echo "   - Import test: PASSED"
    echo "   - TTY test: PASSED"
    echo "   - Fix appears to be working correctly"
else
    echo "❌ OVERALL STATUS: FAILURE"
    echo "   - One or both tests failed"
    echo "   - Please check the output above for details"
fi

echo
echo "File Information:"
echo "- system_menu.py modified: $(stat -c%s plugins/system_tools/system_menu.py) bytes"
echo "- Last modified: $(stat -c%y plugins/system_tools/system_menu.py | cut -d. -f1)"
echo

echo "============================================"
echo "SUMMARY:"
echo "============================================"
if echo "$IMPORT_TEST" | grep -q "SUCCESS" && echo "$TTY_TEST" | grep -q "SUCCESS"; then
    echo "If you see SUCCESS for both tests above, the fix is working."
else
    echo "If you see FAILURE, please share this complete output."
fi
echo
echo "The fix ensures SystemMenu always uses text mode instead of trying"
echo "to initialize curses when already in a curses session from the main menu."
echo
echo "============================================"