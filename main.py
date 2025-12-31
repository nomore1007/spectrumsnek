#!/usr/bin/env python3
"""
SpectrumSnek 🐍📻
Main menu system for selecting and running various radio-related tools.
"""

import sys
import os
import curses
import time
from typing import List, Dict, Any

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

class ModuleInfo:
    """Information about a loadable module."""
    def __init__(self, name: str, description: str, module_path: str, run_function):
        self.name = name
        self.description = description
        self.module_path = module_path
        self.run_function = run_function

class RadioToolsLoader:
    """Main loader with menu system for radio tools."""

    def __init__(self):
        self.modules: List[ModuleInfo] = []
        self.selected_index = 0
        self.web_portal_enabled = True  # Global web portal toggle
        self.load_modules()

    def load_modules(self):
        """Load available modules."""
        # RTL-SDR Scanner module
        try:
            import rtl_scanner
            info = rtl_scanner.get_module_info()
            self.modules.append(ModuleInfo(
                info["name"],
                info["description"],
                "rtl_scanner",
                rtl_scanner.run
            ))
        except ImportError:
            # Module not available, skip
            pass

        # ADS-B Tool module
        try:
            import adsb_tool
            info = adsb_tool.get_module_info()
            self.modules.append(ModuleInfo(
                info["name"],
                info["description"],
                "adsb_tool",
                adsb_tool.run
            ))
        except ImportError:
            # Module not available, skip
            pass

        # Traditional Radio Scanner module
        try:
            import radio_scanner
            info = radio_scanner.get_module_info()
            self.modules.append(ModuleInfo(
                info["name"],
                info["description"],
                "radio_scanner",
                radio_scanner.run
            ))
        except ImportError:
            # Module not available, skip
            pass

        # System Tools module
        try:
            import system_tools
            info = system_tools.get_module_info()
            self.modules.append(ModuleInfo(
                info["name"],
                info["description"],
                "system_tools",
                system_tools.run
            ))
        except ImportError:
            # Module not available, skip
            pass

        # Demo spectrum analyzer
        self.modules.append(ModuleInfo(
            "Spectrum Analyzer (Demo)",
            "Basic spectrum analysis demonstration",
            "demo_spectrum",
            self.run_demo_spectrum
        ))

        # Web portal toggle (special menu item)
        self.modules.append(ModuleInfo(
            f"Web Portal: {'ON' if self.web_portal_enabled else 'OFF'}",
            "Toggle web interfaces for all tools",
            "web_toggle",
            self.toggle_web_portal
        ))

    def run_demo_spectrum(self):
        """Run demo spectrum analyzer."""
        try:
            import demo_scanner
            # Run with default parameters
            sys.argv = ['demo_scanner', '--freq', '100', '--mode', 'spectrum', '--duration', '10']
            demo_scanner.main()
        except ImportError:
            print("Demo scanner not available")
        except Exception as e:
            print(f"Error running demo spectrum: {e}")

    def toggle_web_portal(self):
        """Toggle web portal on/off."""
        self.web_portal_enabled = not self.web_portal_enabled
        print(f"Web portal {'enabled' if self.web_portal_enabled else 'disabled'} globally")
        print("This affects all tools that support web interfaces.")
        input("Press Enter to continue...")

        # Update the menu item name
        for module in self.modules:
            if module.module_path == "web_toggle":
                module.name = f"Web Portal: {'ON' if self.web_portal_enabled else 'OFF'}"
                break

    def draw_menu(self, stdscr):
        """Draw the main menu."""
        stdscr.clear()
        height, width = stdscr.getmaxyx()

        # Title
        title = "SpectrumSnek 🐍📻"
        stdscr.addstr(0, (width - len(title)) // 2, title, curses.A_BOLD)

        # Subtitle
        subtitle = "Choose your radio adventure!"
        stdscr.addstr(2, (width - len(subtitle)) // 2, subtitle)

        # Draw modules
        start_y = 4
        for i, module in enumerate(self.modules):
            y = start_y + i * 3

            # Module name with selection indicator
            if i == self.selected_index:
                stdscr.addstr(y, 4, f"> {module.name}", curses.A_REVERSE | curses.A_BOLD)
            else:
                stdscr.addstr(y, 4, f"  {module.name}")

            # Description
            if y + 1 < height:
                desc = module.description[:width-8]
                # Highlight web portal status
                if "Web Portal" in module.name:
                    if self.web_portal_enabled:
                        stdscr.addstr(y + 1, 6, desc, curses.A_BOLD | curses.color_pair(1) if curses.has_colors() else curses.A_BOLD)
                    else:
                        stdscr.addstr(y + 1, 6, desc, curses.A_DIM)
                else:
                    stdscr.addstr(y + 1, 6, desc)

        # Instructions
        instructions = "Use ↑↓ to navigate, Enter to select, 'q' to quit"
        stdscr.addstr(height - 2, (width - len(instructions)) // 2, instructions, curses.A_DIM)

        stdscr.refresh()

    def run_menu(self, stdscr):
        """Run the menu system."""
        curses.curs_set(0)  # Hide cursor
        curses.start_color()
        curses.init_pair(1, curses.COLOR_GREEN, curses.COLOR_BLACK)  # Web portal enabled
        stdscr.nodelay(True)  # Non-blocking input

        while True:
            self.draw_menu(stdscr)

            # Handle input
            try:
                key = stdscr.getch()

                if key == ord('q') or key == ord('Q'):
                    return None  # Quit
                elif key == curses.KEY_UP:
                    self.selected_index = max(0, self.selected_index - 1)
                elif key == curses.KEY_DOWN:
                    self.selected_index = min(len(self.modules) - 1, self.selected_index + 1)
                elif key == ord('\n') or key == ord('\r') or key == curses.KEY_ENTER:
                    return self.modules[self.selected_index]  # Selected module
                elif key == 27:  # ESC
                    return None  # Quit

                time.sleep(0.05)  # Small delay to prevent high CPU usage

            except KeyboardInterrupt:
                return None

    def run_selected_module(self, module: ModuleInfo):
        """Run the selected module."""
        print(f"\nStarting {module.name}...")
        print(f"Description: {module.description}")
        print("Press Ctrl+C to stop\n")

        try:
            # Restore terminal for module execution
            curses.endwin()
            module.run_function()
        except KeyboardInterrupt:
            print(f"\n{module.name} stopped by user")
        except Exception as e:
            print(f"Error running {module.name}: {e}")
        finally:
            print(f"\nReturned to Radio Tools Loader")

    def run(self):
        """Main run loop."""
        def menu_main(stdscr):
            while True:
                selected_module = self.run_menu(stdscr)
                if selected_module is None:
                    break  # Quit

                self.run_selected_module(selected_module)

                # Brief pause before returning to menu
                print("\nPress Enter to return to menu...")
                input()

        if not self.modules:
            print("No modules available!")
            print("Make sure RTL-SDR dependencies are installed.")
            return

        try:
            curses.wrapper(menu_main)
        except KeyboardInterrupt:
            print("\nRadio Tools Loader stopped by user")
        except Exception as e:
            print(f"Error in menu system: {e}")

def check_dependencies():
    """Check if basic dependencies are available."""
    missing_deps = []

    try:
        import numpy
    except ImportError:
        missing_deps.append("numpy")

    try:
        import scipy
    except ImportError:
        missing_deps.append("scipy")

    if missing_deps:
        print("Missing dependencies:")
        for dep in missing_deps:
            print(f"  - {dep}")
        print("Run: pip install -r requirements.txt")
        return False

    return True

def main():
    """Main entry point."""
    print("Radio Tools Loader")
    print("=" * 20)

    # Check if we have a controlling terminal for interactive mode
    if not sys.stdout.isatty():
        print("Error: Interactive mode requires a controlling terminal (TTY).")
        print("This program uses curses for the menu interface.")
        print("")
        print("Please run directly in a terminal:")
        print("  python main.py")
        print("")
        print("For headless operation, consider starting individual tools:")
        print("  python -m rtl_scanner.web_scanner  # Web RTL-SDR interface")
        print("  python -m adsb_tool.adsb_tracker --web  # Web ADS-B interface")
        sys.exit(1)

    if not check_dependencies():
        sys.exit(1)

    loader = RadioToolsLoader()

    if len(sys.argv) > 1:
        # Direct module execution
        module_name = sys.argv[1]

        if module_name == "rtl_scanner" or module_name == "scanner":
            print("Starting RTL-SDR Scanner directly...")
            try:
                import rtl_scanner
                rtl_scanner.run()
            except ImportError:
                print("RTL-SDR scanner not available. Run setup.sh first.")
                sys.exit(1)
        elif module_name == "adsb" or module_name == "adsb_tool":
            print("Starting ADS-B Aircraft Tracker directly...")
            try:
                import adsb_tool
                adsb_tool.run()
            except ImportError:
                print("ADS-B tool not available. Run setup.sh first.")
                sys.exit(1)
        elif module_name == "demo":
            print("Starting demo spectrum...")
            loader.run_demo_spectrum()
        else:
            print(f"Unknown module: {module_name}")
            print("Available modules: rtl_scanner, adsb_tool, demo")
            sys.exit(1)
    else:
        # Interactive menu
        loader.run()

if __name__ == "__main__":
    main()