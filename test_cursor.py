#!/usr/bin/env python3
"""
Test script to verify cursor restoration after curses programs.
"""

import curses
import time
import sys
import os

def test_curses(stdscr):
    """Simple curses test."""
    stdscr.clear()
    stdscr.addstr(0, 0, "Testing cursor restoration...")
    stdscr.addstr(2, 0, "Press 'q' to quit, 'c' to crash test")
    stdscr.refresh()

    while True:
        key = stdscr.getch()
        if key == ord('q'):
            break
        elif key == ord('c'):
            # Simulate a crash
            raise Exception("Simulated crash for testing")

def restore_terminal():
    """Restore terminal to normal state."""
    try:
        curses.endwin()
    except:
        pass

    try:
        sys.stdout.write("\033[?25h")  # Show cursor
        sys.stdout.write("\033[0m")    # Reset colors/attributes
        sys.stdout.write("\033[2J")    # Clear screen
        sys.stdout.write("\033[H")     # Move to home position
        sys.stdout.write("\033[J")     # Clear to end of screen
        sys.stdout.write("\033[?1049l")  # Exit alternate screen if used
        sys.stdout.write("\033[?1l")   # Reset cursor keys
        sys.stdout.write("\033>")      # Reset numeric keypad
        sys.stdout.flush()

        # Try system reset as final fallback
        try:
            os.system("tput reset >/dev/null 2>&1")
        except:
            pass
    except:
        # Final fallback - try system reset
        try:
            os.system("tput reset >/dev/null 2>&1")
        except:
            pass

if __name__ == "__main__":
    print("Testing curses cursor restoration...")
    print("Cursor should be visible after program exits.")

    try:
        curses.wrapper(test_curses)
        restore_terminal()
        print("✓ Program exited normally - cursor should be restored")
    except KeyboardInterrupt:
        restore_terminal()
        print("✓ Program interrupted - cursor should be restored")
    except Exception as e:
        restore_terminal()
        print(f"✗ Program crashed: {e}")
        print("Cursor should still be restored via emergency cleanup")

    print("Test complete.")