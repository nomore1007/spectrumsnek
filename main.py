#!/usr/bin/env python3
"""
SpectrumSnek 🐍📻
Main menu system for selecting and running various radio-related tools.
"""

import sys
import os
import time
import curses
try:

    from textual.app import App, ComposeResult

    from textual.widgets import OptionList, Header, Footer

    TEXTUAL_AVAILABLE = True

    class SpectrumMenu(App):

        def __init__(self, modules):

            super().__init__()

            self.modules = modules

            self.selected_module = None

        def compose(self) -> ComposeResult:

            yield Header("SpectrumSnek Tools")

            options = [f"{module.name}: {module.description}" for module in self.modules]

            yield OptionList(*options)

            yield Footer()

        def on_option_list_option_selected(self, event):
            index = event.option_index
            if 0 <= index < len(self.modules):
                self.selected_module = self.modules[index]
                self.exit()

        def on_key(self, event):
            if event.key == "q" or event.key == "Q":
                self.exit()
            elif event.key == "b" or event.key == "B" or event.key == "escape":
                self.exit()

except ImportError:

    TEXTUAL_AVAILABLE = False
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

    def __init__(self, service_url='http://127.0.0.1:5000'):
        self.service_url = service_url
        self.modules: List[ModuleInfo] = []
        self.selected_index = 0
        self.web_portal_enabled = True  # Global web portal toggle
        self.load_modules()

    def load_modules(self):
        """Load available tools from service API with retry logic."""
        try:
            import requests
        except ImportError:
            print("⚠ Requests library not available, using local mode")
            self.load_local_modules()
            return

        # Try multiple times to connect to service (handles startup timing)
        max_retries = 3
        for attempt in range(max_retries):
            try:
                print(f"Attempting to connect to SpectrumSnek service at {self.service_url}... (attempt {attempt + 1}/{max_retries})")
                response = requests.get(f"{self.service_url}/api/tools", timeout=5)
                if response.status_code == 200:
                    print("✓ Successfully connected to service")
                    data = response.json()
                    for tool_name, tool_data in data['tools'].items():
                        info = tool_data['info']
                        self.modules.append(ModuleInfo(
                            info["name"],
                            info["description"],
                            tool_name,
                            lambda name=tool_name: self.start_tool(name)
                        ))
                    print(f"✓ Loaded {len(data.get('tools', {}))} tools from service")
                    return  # Success, exit the retry loop
                else:
                    print(f"⚠ Service responded with status {response.status_code}")
                    if attempt < max_retries - 1:
                        print("   Retrying in 2 seconds...")
                        time.sleep(2)
                    else:
                        print("   Falling back to local mode")
                        self.load_local_modules()
            except requests.exceptions.ConnectionError as e:
                if attempt < max_retries - 1:
                    print(f"⚠ Cannot connect to service (attempt {attempt + 1}), retrying in 2 seconds...")
                    time.sleep(2)
                else:
                    print(f"⚠ Cannot connect to service after {max_retries} attempts, using local mode")
                    self.load_local_modules()
            except requests.exceptions.Timeout:
                if attempt < max_retries - 1:
                    print(f"⚠ Service connection timed out (attempt {attempt + 1}), retrying in 2 seconds...")
                    time.sleep(2)
                else:
                    print("⚠ Service connection timed out, using local mode")
                    self.load_local_modules()
            except Exception as e:
                if attempt < max_retries - 1:
                    print(f"⚠ Service connection failed (attempt {attempt + 1}): {e}, retrying in 2 seconds...")
                    time.sleep(2)
                else:
                    print(f"⚠ Service connection failed after {max_retries} attempts, using local mode")
                    self.load_local_modules()

        # Web portal toggle (special menu item)
        self.modules.append(ModuleInfo(
            f"Web Portal: {'ON' if self.web_portal_enabled else 'OFF'}",
            "Toggle web interfaces for all tools",
            "web_toggle",
            self.toggle_web_portal
        ))

    def load_local_modules(self):
        """Fallback: Load available modules locally."""
        plugins_dir = "plugins"

        # Load plugins dynamically
        if os.path.exists(plugins_dir):
            for item in os.listdir(plugins_dir):
                plugin_path = os.path.join(plugins_dir, item)
                if os.path.isdir(plugin_path) and not item.startswith('__') and item != "system_tools":
                    try:
                        # Import the plugin module
                        plugin_module = __import__(f"{plugins_dir}.{item}", fromlist=[item])
                        info = plugin_module.get_module_info()
                        self.modules.append(ModuleInfo(
                            info["name"],
                            info["description"],
                            f"{plugins_dir}.{item}",
                            plugin_module.run
                        ))
                    except ImportError:
                        # Plugin not available, skip silently
                        pass
                    except Exception:
                        # Other errors, skip silently
                        pass
                    except ImportError:
                        # Plugin not available, skip silently
                        pass
                    except Exception:
                        # Other errors, skip silently
                        pass

        # Web portal toggle (special menu item)
        self.modules.append(ModuleInfo(
            f"Web Portal: {'ON' if self.web_portal_enabled else 'OFF'}",
            "Toggle web interfaces for all tools",
            "web_toggle",
            self.toggle_web_portal
        ))

    def run_local_tool(self, tool_name):
        """Run a tool locally for interaction."""
        try:
            if tool_name in ["rtl_scanner", "adsb_tool", "radio_scanner"]:
                import importlib
                mod = importlib.import_module(f"plugins.{tool_name}")
                mod.run()
            elif tool_name == "audio_tool":
                from system_tools.audio_output_selector import AudioOutputSelector
                AudioOutputSelector().run()
            else:
                print(f"Local run not available for {tool_name}")
        except ImportError as e:
            print(f"Cannot run {tool_name} locally: {e}")
        except Exception as e:
            print(f"Error running {tool_name}: {e}")

    def start_tool(self, tool_name):
        """Start a tool via service API or locally."""
        if self.service_url == 'http://127.0.0.1:5000':
            # Run locally for interaction
            self.run_local_tool(tool_name)
            print("Returning to menu in 3 seconds...")
            time.sleep(3)
            return

        try:
            import requests
            response = requests.post(f"{self.service_url}/api/tools/{tool_name}/start", timeout=10)
            if response.status_code == 200:
                print(f"Started {tool_name}")
            else:
                print(f"Failed to start {tool_name}: {response.text}")
        except Exception as e:
            print(f"Failed to start {tool_name}: {e}")
        print("Returning to menu in 3 seconds...")
        time.sleep(3)

    def toggle_web_portal(self):
        """Toggle web portal on/off."""
        self.web_portal_enabled = not self.web_portal_enabled
        print(f"Web portal {'enabled' if self.web_portal_enabled else 'disabled'} globally")
        print("This affects all tools that support web interfaces.")
        print("Returning to menu in 3 seconds...")
        time.sleep(3)

        # Update the menu item name
        for module in self.modules:
            if module.module_path == "web_toggle":
                module.name = f"Web Portal: {'ON' if self.web_portal_enabled else 'OFF'}"
                break

    def draw_menu(self, stdscr):
        """Draw the main menu."""
        stdscr.clear()
        height, width = stdscr.getmaxyx()

        # Fallback for narrow terminals
        if width < 40:
            width = 80  # Default fallback

        # Title
        title = "SpectrumSnek 🐍📻"
        stdscr.addstr(0, (width - len(title)) // 2, title, curses.A_BOLD)

        # Subtitle
        subtitle = "Choose your radio adventure!"
        stdscr.addstr(2, (width - len(subtitle)) // 2, subtitle)

        # Simple layout for all connections
        start_y = 4
        for i, module in enumerate(self.modules):
            y = start_y + i
            if y >= height:
                break

            # Module name with selection indicator
            if i == self.selected_index:
                stdscr.addstr(y, 2, f"> {module.name}", curses.A_REVERSE | curses.A_BOLD)
            else:
                stdscr.addstr(y, 2, f"  {module.name}")

        # Instructions
        instructions = "↑↓ navigate, Enter select, 'q' quit"
        stdscr.addstr(height - 1, (width - len(instructions)) // 2, instructions, curses.A_DIM)

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
            print(f"\nReturning to Radio Tools Loader")
            time.sleep(2)

    def run(self):
        """Main run loop."""
        if TEXTUAL_AVAILABLE:
            while True:
                app = SpectrumMenu(self.modules)
                app.run()
                if app.selected_module:
                    self.run_selected_module(app.selected_module)
                else:
                    break
        else:
            self.text_menu_loop()

    def getch(self):
        """Read a single key, handling escape sequences for arrows."""
        import sys
        import tty
        import termios
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        try:
            tty.setraw(sys.stdin.fileno())
            ch = sys.stdin.read(1)
            if ch == '\x1b':
                ch2 = sys.stdin.read(1)
                if ch2 == '[':
                    ch3 = sys.stdin.read(1)
                    if ch3 == 'A': return 'up'
                    elif ch3 == 'B': return 'down'
                    elif ch3 == 'C': return 'right'
                    elif ch3 == 'D': return 'left'
            return ch
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)

    def text_menu_loop(self):
        """Text-based menu loop for when curses fails."""
        selected = 0
        while True:
            print("\n" + "="*50)
            print("Radio Tools Loader")
            print("="*50)
            print("Available tools:")
            
            for i, module in enumerate(self.modules):
                marker = ">" if i == selected else " "
                print(f"  {marker} {module.name}")
                print(f"     {module.description}")
            
            print("\n  ↑↓ navigate, Enter select, 'q' quit")
            print("="*50)
            
            try:
                key = self.getch()
                
                if key == 'q' or key == 'Q':
                    break
                elif key == 'up':
                    selected = (selected - 1) % len(self.modules)
                elif key == 'down':
                    selected = (selected + 1) % len(self.modules)
                elif key == '\r' or key == '\n':  # Enter
                    selected_module = self.modules[selected]
                    self.run_selected_module_text(selected_module)
                    
            except KeyboardInterrupt:
                print("\nExiting...")
                break
            except EOFError:
                print("\nExiting...")
                break

    def run_selected_module_text(self, module: ModuleInfo):
        """Run the selected module in text mode."""
        print(f"\nStarting {module.name}...")
        print(f"Description: {module.description}")
        print("Press Ctrl+C to stop\n")

        try:
            module.run_function()
        except KeyboardInterrupt:
            print(f"\n{module.name} stopped by user")
        except Exception as e:
            print(f"Error running {module.name}: {e}")
        finally:
            print(f"\nReturning to Radio Tools Loader")
            input("Press Enter to continue...")

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

    if not check_dependencies():
        sys.exit(1)

    if len(sys.argv) > 1 and sys.argv[1] == "--service":
        # Run as service
        from spectrum_service import SpectrumService
        service = SpectrumService()

        # Parse additional arguments
        port = 5000
        host = '0.0.0.0'

        i = 2
        while i < len(sys.argv):
            if sys.argv[i] == '--port' and i + 1 < len(sys.argv):
                try:
                    port = int(sys.argv[i + 1])
                    i += 2
                except ValueError:
                    print(f"Invalid port number: {sys.argv[i + 1]}")
                    sys.exit(1)
            elif sys.argv[i] == '--host' and i + 1 < len(sys.argv):
                host = sys.argv[i + 1]
                i += 2
            else:
                print(f"Unknown service argument: {sys.argv[i]}")
                print("Usage: python main.py --service [--port PORT] [--host HOST]")
                sys.exit(1)

        service.run(host=host, port=port)
        return

    # For UI mode, parse arguments
    import argparse

    parser = argparse.ArgumentParser(description="SpectrumSnek Radio Tools Loader")
    parser.add_argument('--service-url', default='http://127.0.0.1:5000',
                       help='URL of the SpectrumSnek service (default: http://127.0.0.1:5000)')

    args, unknown = parser.parse_known_args()

    loader = RadioToolsLoader(service_url=args.service_url)

    if len(sys.argv) > 1 and not sys.argv[1].startswith('-'):
        # Direct module execution (legacy)
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
        else:
            print(f"Unknown module: {module_name}")
            print("Available modules: rtl_scanner, adsb_tool, demo")
            sys.exit(1)
    else:
        # Interactive menu
        try:
            loader.run()
        except KeyboardInterrupt:
            print("\nRadio Tools Loader stopped by user")
        except Exception as e:
            print(f"\nError in interactive menu: {e}")
            print("Try running with a different terminal or check TERM variable")
            sys.exit(1)

if __name__ == "__main__":
    main()