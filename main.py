#!/usr/bin/env python3
"""
SpectrumSnek 🐍📻
Main menu system for selecting and running various radio-related tools.

This module provides a curses-based interactive menu system that allows users
to select and launch different radio analysis tools including RTL-SDR spectrum
analysis, ADS-B aircraft tracking, WiFi scanning, and Bluetooth discovery.

Key Features:
- Interactive curses-based menu navigation
- Automatic tool discovery and loading
- Service mode for web interface access
- Comprehensive error handling and logging

Usage:
    python main.py                    # Interactive menu
    python main.py --service-url URL  # Connect to service
    python main.py --help            # Show help
"""

import sys
import os
import time
import curses
import importlib
from pathlib import Path
from typing import List, Dict, Any

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

class ModuleInfo:
    """
    Information container for a loadable SpectrumSnek module.

    This class holds metadata about available tools and their execution
    functions, enabling dynamic module loading and menu generation.

    Attributes:
        name (str): Display name of the module
        description (str): Brief description for menu display
        module_path (str): Filesystem path to the module
        run_function: Callable function to execute the module
    """
    def __init__(self, name: str, description: str, module_path: str, run_function):
        self.name = name
        self.description = description
        self.module_path = module_path
        self.run_function = run_function

class RadioToolsLoader:
    """Main loader with menu system for radio tools."""

    def __init__(self, service_url=None):
        self.service_url = service_url
        self.modules: List[ModuleInfo] = []
        self.selected_index = 0
        self.web_portal_enabled = True  # Global web portal toggle
        self.load_modules()

    def load_modules(self):
        """Load tools from an explicitly requested service, or discover local plugins."""
        self.modules = []
        if not self.service_url:
            self.load_local_modules()
            return

        try:
            import requests
            response = requests.get(f"{self.service_url.rstrip('/')}/api/tools", timeout=5)
            response.raise_for_status()
            data = response.json()
            for tool_name, tool_data in data.get("tools", {}).items():
                info = tool_data.get("info", {})
                self.modules.append(ModuleInfo(
                    self._get_short_name(info.get("name", tool_name)),
                    info.get("description", ""),
                    tool_name,
                    lambda name=tool_name: self.start_tool(name),
                ))
            if self.modules:
                return
            print("Service returned no tools; discovering local plugins instead.")
        except Exception as exc:
            print(f"Could not load tools from service ({exc}); discovering local plugins.")

        self.service_url = None
        self.load_local_modules()

    def load_local_modules(self):
        """Discover every importable plugin package under ./plugins automatically."""
        self.modules = []
        project_root = Path(__file__).resolve().parent
        plugins_dir = project_root / "plugins"
        if str(project_root) not in sys.path:
            sys.path.insert(0, str(project_root))

        if not plugins_dir.is_dir():
            print(f"Plugin directory not found: {plugins_dir}", file=sys.stderr)
        else:
            for plugin_path in sorted(plugins_dir.iterdir(), key=lambda path: path.name.lower()):
                if (not plugin_path.is_dir()
                        or plugin_path.name.startswith("_")
                        or plugin_path.name in {"system_tools", "__pycache__"}
                        or not (plugin_path / "__init__.py").is_file()):
                    continue
                try:
                    plugin_module = importlib.import_module(f"plugins.{plugin_path.name}")
                    info = plugin_module.get_module_info()
                    run_function = getattr(plugin_module, "run")
                    self.modules.append(ModuleInfo(
                        self._get_short_name(info.get("name", plugin_path.name)),
                        info.get("description", ""),
                        f"plugins.{plugin_path.name}",
                        lambda run_func=run_function: run_func(),
                    ))
                except Exception as exc:
                    print(f"Skipping plugin {plugin_path.name}: {exc}", file=sys.stderr)

        self.modules.append(ModuleInfo(
            "System Tools",
            "Wi-Fi, Bluetooth, audio, display, and system utilities",
            "system_tools",
            lambda: self.run_local_tool("system_tools"),
        ))

    def show_system_tools_submenu(self):
        """Show system tools as a submenu with arrow key navigation like main menu."""
        from plugins.system_tools.system_menu import SystemMenu

        # Create system tools menu
        system_menu = SystemMenu()

        # Add a "Back" option
        back_option = type('Tool', (), {
            'name': '⬅️ Back to Main Menu',
            'description': 'Return to the main SpectrumSnek menu',
            'action': lambda: None
        })()

        # Combine tools with back option
        all_options = system_menu.tools + [back_option]

        # Create a temporary menu interface
        class SubMenu:
            def __init__(self, parent, options):
                self.parent = parent
                self.options = options
                self.selected_index = 0

            def draw_menu(self, stdscr):
        """Draw the classic curses menu, including every discovered plugin."""
        stdscr.erase()
        height, width = stdscr.getmaxyx()
        if height < 5 or width < 24:
            try:
                stdscr.addnstr(0, 0, "Terminal too small. Enlarge it and try again.",
                               max(1, width - 1))
            except curses.error:
                pass
            stdscr.refresh()
            return

        title = "SpectrumSnek  🐍📻"
        subtitle = "Choose your radio adventure"
        try:
            stdscr.addnstr(0, max(0, (width - len(title)) // 2), title, width - 1)
            stdscr.addnstr(2, max(0, (width - len(subtitle)) // 2), subtitle, width - 1)
        except curses.error:
            pass

        list_start = 4
        list_rows = max(1, height - list_start - 2)
        top = max(0, min(self.selected_index, max(0, len(self.modules) - list_rows)))
        for row, index in enumerate(range(top, min(len(self.modules), top + list_rows))):
            module = self.modules[index]
            label = f"> {module.name}" if index == self.selected_index else f"  {module.name}"
            try:
                attr = curses.A_REVERSE | curses.A_BOLD if index == self.selected_index else curses.A_NORMAL
                stdscr.addnstr(list_start + row, 2, label, max(1, width - 4), attr)
            except curses.error:
                pass

        instructions = "↑↓ Navigate  Enter Run  Q Quit"
        try:
            stdscr.addnstr(height - 1, max(0, (width - len(instructions)) // 2),
                           instructions, width - 1, curses.A_DIM)
            stdscr.refresh()
        except curses.error:
            pass

    def run_curses_menu(self, stdscr):
        """Return the selected tool; the terminal is restored before it runs."""
        curses.curs_set(0)
        stdscr.keypad(True)
        stdscr.nodelay(False)
        while True:
            self.draw_menu(stdscr)
            key = stdscr.getch()
            if key in (ord("q"), ord("Q"), 27):
                return None
            if key == curses.KEY_UP:
                self.selected_index = (self.selected_index - 1) % max(1, len(self.modules))
            elif key == curses.KEY_DOWN:
                self.selected_index = (self.selected_index + 1) % max(1, len(self.modules))
            elif key in (10, 13, curses.KEY_ENTER):
                if self.modules:
                    return self.modules[self.selected_index]

    def run_selected_module(self, module: ModuleInfo):
        """Run a selected plugin outside curses, then return to the menu."""
        print(f"\nStarting {module.name}...")
        if module.description:
            print(f"Description: {module.description}")
        print("Press Ctrl+C to stop the tool.\n")
        try:
            module.run_function()
        except KeyboardInterrupt:
            print(f"\n{module.name} stopped by user.")
        except Exception as exc:
            print(f"Error running {module.name}: {exc}")
        finally:
            if sys.stdin.isatty():
                try:
                    input("\nPress Enter to return to the menu...")
                except (EOFError, KeyboardInterrupt):
                    pass

    def run(self):
        """Run the classic curses menu continuously until the user quits."""
        if not sys.stdin.isatty() or not sys.stdout.isatty():
            raise RuntimeError("The curses menu requires an interactive terminal.")
        while True:
            selected = curses.wrapper(self.run_curses_menu)
            if selected is None:
                return
            self.run_selected_module(selected)

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
    print("SpectrumSnek")
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

    parser = argparse.ArgumentParser(description="SpectrumSnek")
    parser.add_argument('--service-url', default=None,
                       help='Optional SpectrumSnek service URL; local plugin discovery is the default')

    args, unknown = parser.parse_known_args()

    # Explicit module names remain supported for scripts and service integrations.
    if unknown and not unknown[0].startswith("-"):
        module_name = unknown.pop(0)
        aliases = {"scanner": "rtl_scanner", "adsb": "adsb_tool"}
        module_name = aliases.get(module_name, module_name)
        try:
            module = importlib.import_module(f"plugins.{module_name}")
            module.run(*unknown)
        except (ImportError, AttributeError) as exc:
            print(f"Unknown or unavailable module '{module_name}': {exc}")
            sys.exit(1)
        return

    loader = RadioToolsLoader(service_url=args.service_url)
    try:
        loader.run()
    except KeyboardInterrupt:
        print("\\nSpectrumSnek stopped by user.")
    except (curses.error, RuntimeError) as exc:
        print(f"Could not start curses menu: {exc}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()