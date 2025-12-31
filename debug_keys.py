#!/usr/bin/env python3
"""
Debug script to check key codes in curses.
Run this to see what codes arrow keys produce.
"""

import curses
import time

def main(stdscr):
    stdscr.clear()
    stdscr.addstr(0, 0, "Arrow Key Debug - Press keys to see codes")
    stdscr.addstr(2, 0, "Press 'q' to quit")
    stdscr.refresh()

    curses.cbreak()
    curses.noecho()
    stdscr.keypad(True)
    stdscr.nodelay(False)  # Blocking input for debugging

    while True:
        key = stdscr.getch()
        if key == ord('q'):
            break

        stdscr.clear()
        stdscr.addstr(0, 0, "Arrow Key Debug - Press keys to see codes")
        stdscr.addstr(2, 0, "Press 'q' to quit")
        stdscr.addstr(4, 0, f"Key code: {key} (0x{key:02x})")

        # Check for common arrow key codes
        if key == curses.KEY_UP:
            stdscr.addstr(5, 0, "Detected: UP ARROW (curses.KEY_UP)")
        elif key == curses.KEY_DOWN:
            stdscr.addstr(5, 0, "Detected: DOWN ARROW (curses.KEY_DOWN)")
        elif key == curses.KEY_LEFT:
            stdscr.addstr(5, 0, "Detected: LEFT ARROW (curses.KEY_LEFT)")
        elif key == curses.KEY_RIGHT:
            stdscr.addstr(5, 0, "Detected: RIGHT ARROW (curses.KEY_RIGHT)")
        elif key == 27:  # ESC sequence start
            stdscr.addstr(5, 0, "Detected: ESCAPE SEQUENCE (arrow key?)")
            # Try to read more characters
            stdscr.nodelay(True)
            ch1 = stdscr.getch()
            ch2 = stdscr.getch()
            stdscr.nodelay(False)
            if ch1 != -1 and ch2 != -1:
                stdscr.addstr(6, 0, f"ESC sequence: {ch1} (0x{ch1:02x}), {ch2} (0x{ch2:02x})")
        else:
            stdscr.addstr(5, 0, f"Other key: {chr(key) if 32 <= key <= 126 else 'non-printable'}")

        stdscr.refresh()

if __name__ == "__main__":
    curses.wrapper(main)