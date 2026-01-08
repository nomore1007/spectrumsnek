#!/bin/bash
# Remote device verification script for TTY Display Control tool

echo "🔍 REMOTE DEVICE VERIFICATION: TTY Display Control Tool"
echo "======================================================="
echo

LOG_FILE="/tmp/spectrumsnek_display.log"
rm -f "$LOG_FILE"

echo "📋 System Information:"
echo "======================"
echo "Date: $(date)"
echo "Hostname: $(hostname)"
echo "Kernel: $(uname -a)"
echo "Python: $(python --version 2>&1)"
echo "TERM: $TERM"
echo "SSH_CLIENT: $SSH_CLIENT"
echo "SSH_TTY: $SSH_TTY"  
echo "SSH_CONNECTION: $SSH_CONNECTION"
echo

echo "🧪 Test 1: SystemMenu.run() - Should use text mode"
echo "=================================================="
echo "Expected: 'Remote session detected, using text menu...' then text menu"
echo

timeout 5 bash -c 'echo "4" | python -c "
from plugins.system_tools.system_menu import SystemMenu
menu = SystemMenu()
menu.run()
"' 2>&1 | head -15

echo
echo "🧪 Test 2: Direct TTY tool execution"
echo "===================================="
echo "Expected: Complete TFT guide, no curses errors"
echo

python -c "
from plugins.system_tools.system_menu import SystemMenu
menu = SystemMenu()
tools = menu.tools
if len(tools) >= 4:
    tty_tool = tools[3]
    print(f'Testing tool: {tty_tool.name}')
    tty_tool.action()
else:
    print('ERROR: TTY tool not found')
" 2>/dev/null | head -5

echo
echo "🧪 Test 3: Log file analysis"
echo "============================"
if [ -f "$LOG_FILE" ]; then
    echo "Log file exists. Analyzing..."
    
    # Check for the critical error
    critical_errors=$(grep -c "cannot access local variable.*curses" "$LOG_FILE" 2>/dev/null || echo "0")
    echo "Critical curses errors: $critical_errors"
    
    # Check for success
    successes=$(grep -c "Tool completed successfully" "$LOG_FILE" 2>/dev/null || echo "0")
    echo "Tool completions: $successes"
    
    # Show recent errors
    echo "Recent error lines:"
    grep -i error "$LOG_FILE" | tail -3
    
    echo "Recent completion lines:"
    grep "completed successfully" "$LOG_FILE" | tail -1
    
else
    echo "ERROR: Log file not created!"
fi

echo
echo "🎯 VERIFICATION RESULTS:"
echo "========================"

if [ -f "$LOG_FILE" ]; then
    if grep -q "Tool completed successfully" "$LOG_FILE" && ! grep -q "cannot access local variable.*curses" "$LOG_FILE"; then
        echo "✅ SUCCESS: Tool works correctly on this device"
        echo "✅ No curses scoping errors"
        echo "✅ Tool completes successfully"
    else
        echo "❌ FAILURE: Issues detected"
        if grep -q "cannot access local variable.*curses" "$LOG_FILE"; then
            echo "   - Curses scoping error still present"
        fi
        if ! grep -q "Tool completed successfully" "$LOG_FILE"; then
            echo "   - Tool did not complete successfully"
        fi
    fi
else
    echo "❌ INCOMPLETE: Cannot verify without log file"
fi

echo
echo "📁 Log file location: $LOG_FILE"
echo "📝 Please share the complete output above with the developer"
echo
