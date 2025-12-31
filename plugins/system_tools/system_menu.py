#!/usr/bin/env python3
"""
System Tools Menu - SpectrumSnek 🐍📻

Submenu for system utilities including connectivity and updates.
"""

import curses
import subprocess
import time
import os
from typing import List, Dict, Any, Optional

class SystemTool:
    """Represents a system tool."""
    def __init__(self, name: str, description: str, action):
        self.name = name
        self.description = description
        self.action = action

class SystemMenu:
    """System tools submenu with curses interface."""

    def __init__(self):
        self.tools: List[SystemTool] = []
        self.selected_index = 0
        self.load_tools()

    def load_tools(self):
        """Load available system tools."""
        # WiFi Selector
        self.tools.append(SystemTool(
            "📶 WiFi Network Selector",
            "Scan and connect to WiFi networks",
            self.run_wifi_selector
        ))

        # Bluetooth Connector
        self.tools.append(SystemTool(
            "🔵 Bluetooth Device Connector",
            "Pair and connect to Bluetooth devices",
            self.run_bluetooth_connector
        ))

        # Audio Output Selector
        self.tools.append(SystemTool(
            "🔊 Audio Output Selector",
            "Select and test audio output devices including Bluetooth",
            self.run_audio_selector
        ))

        # TTY Display Settings
        self.tools.append(SystemTool(
            "🖥️ TTY Display Info",
            "Show terminal resolution and display settings",
            self.show_display_info
        ))

        # Update from GitHub
        self.tools.append(SystemTool(
            "⬆️ Update from GitHub",
            "Pull latest updates from repository",
            self.update_from_github
        ))

    def run_wifi_selector(self):
        """Launch WiFi selector."""
        try:
            import wifi_tool
            wifi_tool.run()
        except ImportError:
            print("WiFi tool not available")
            input("Press Enter to continue...")

    def run_bluetooth_connector(self):
        """Launch Bluetooth connector."""
        try:
            import bluetooth_tool
            bluetooth_tool.run()
        except ImportError:
            print("Bluetooth tool not available")
            input("Press Enter to continue...")

    def run_audio_selector(self):
        """Launch Audio output selector."""
        try:
            from .audio_output_selector import AudioOutputSelector
            selector = AudioOutputSelector()
            selector.run()
        except ImportError:
            print("Audio selector not available")
            input("Press Enter to continue...")

    def show_display_info(self):
        """Show TTY display information."""
        try:
            import os
            import curses

            # Get terminal info
            rows, cols = os.get_terminal_size()
            term = os.environ.get('TERM', 'unknown')
            colors = curses.COLORS if hasattr(curses, 'COLORS') else 'unknown'

            print("TTY Display Information")
            print("=" * 25)
            print(f"Terminal size: {cols} x {rows}")
            print(f"Terminal type: {term}")
            print(f"Color support: {colors} colors")
            print(f"Curses colors available: {'Yes' if curses.has_colors() else 'No'}")
            print(f"Curses can change color: {'Yes' if curses.can_change_color() else 'No'}")
            print()
            print("For handheld devices:")
            print("- Ensure terminal is at least 80x24 for full menus")
            print("- Use 'setterm -blank 0' to disable screen blanking")
            print("- Check /boot/config.txt for display settings")

        except Exception as e:
            print(f"Error getting display info: {e}")
        finally:
            input("\nPress Enter to continue...")

    def update_from_github(self):
        """Update from GitHub repository."""
        try:
            print("Updating from GitHub...")
            print("Running: git pull")

            # Change to repo directory if needed
            repo_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            os.chdir(repo_dir)

            result = subprocess.run(
                ["git", "pull"],
                capture_output=True, text=True, timeout=60
            )

            if result.returncode == 0:
                print("✅ Update successful!")
                print(result.stdout.strip())
                if "Already up to date" in result.stdout:
                    print("Your SpectrumSnek is already up to date.")
                else:
                    print("New updates installed. You may need to restart tools.")
            else:
                print("❌ Update failed!")
                print("Error:", result.stderr.strip())

        except subprocess.TimeoutExpired:
            print("❌ Update timeout")
        except Exception as e:
            print(f"❌ Update error: {e}")
        finally:
            input("\nPress Enter to continue...")

    def draw_menu(self, stdscr):
        """Draw the system tools menu."""
        stdscr.clear()
        height, width = stdscr.getmaxyx()

        # Title
        title = "System Tools 🐍📻"
        stdscr.addstr(0, (width - len(title)) // 2, title, curses.A_BOLD)

        # Subtitle
        subtitle = "Connectivity and maintenance utilities"
        stdscr.addstr(2, (width - len(subtitle)) // 2, subtitle)

        # Tools
        start_y = 4
        max_items = (height - 8) // 2  # 2 lines per item, reserve space for description
        start_idx = max(0, min(self.selected_index - max_items // 2, len(self.tools) - max_items))

        for i in range(max_items):
            idx = start_idx + i
            if idx >= len(self.tools):
                break
            tool = self.tools[idx]
            y = start_y + i * 2

            # Tool name with selection indicator
            if idx == self.selected_index:
                stdscr.addstr(y, 2, f"> {tool.name}", curses.A_REVERSE | curses.A_BOLD)
            else:
                stdscr.addstr(y, 2, f"  {tool.name}")

        # Description of selected item at bottom
        if self.tools:
            selected = self.tools[self.selected_index]
            desc_y = height - 3
            desc = selected.description[:width-4]
            stdscr.addstr(desc_y, 2, f"Description: {desc}", curses.A_DIM)

        # Instructions
        instructions = "↑↓ navigate, Enter select, 'b' back, 'q' quit"
        stdscr.addstr(height - 1, (width - len(instructions)) // 2, instructions, curses.A_DIM)

        stdscr.refresh()

    def run_menu(self, stdscr):
        """Run the system tools menu."""
        curses.curs_set(0)

        while True:
            self.draw_menu(stdscr)

            try:
                key = stdscr.getch()

                if key == ord('q') or key == ord('Q'):
                    return False  # Quit
                elif key == ord('b') or key == ord('B'):
                    return True  # Back to main menu
                elif key == curses.KEY_UP:
                    self.selected_index = max(0, self.selected_index - 1)
                elif key == curses.KEY_DOWN:
                    self.selected_index = min(len(self.tools) - 1, self.selected_index + 1)
                elif key == ord('\n') or key == ord('\r') or key == curses.KEY_ENTER:
                    tool = self.tools[self.selected_index]
                    # Run the tool - let it handle curses transition
                    tool.action()
                    # After tool returns, the menu will be redrawn in next loop iteration
                elif key == 27:  # ESC
                    return True  # Back

                time.sleep(0.05)

            except KeyboardInterrupt:
                return False

    def run(self):
        """Main run method."""
        print("System Tools")
        print("============")

        try:
            back_to_main = curses.wrapper(self.run_menu)
            if not back_to_main:
                print("\nSystem tools stopped by user")
        except KeyboardInterrupt:
            print("\nSystem tools stopped by user")
        except Exception as e:
            print(f"Error in system tools menu: {e}")

if __name__ == "__main__":
    menu = SystemMenu()
    menu.run()