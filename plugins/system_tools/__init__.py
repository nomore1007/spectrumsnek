"""
System Tools Module - SpectrumSnek 🐍📻

A collection of system utilities including connectivity and update tools.
"""

import os
from typing import Dict, Any

# Module metadata
MODULE_INFO = {
    "name": "🔧 System Tools",
    "description": "WiFi, Bluetooth, and update utilities - System management for Raspberry Pi",
    "version": "1.0.0",
    "author": "SpectrumSnek",
    "features": [
        "WiFi Network Selector",
        "Bluetooth Device Connector",
        "Audio Output Selector",
        "TTY Display Information",
        "Update from GitHub",
        "Curses-based submenu interface"
    ]
}

def get_module_info() -> Dict[str, Any]:
    """Return module information for the main loader."""
    return MODULE_INFO

def run():
    """Main entry point for the system tools submenu."""
    try:
        from .system_menu import SystemMenu

        menu = SystemMenu()
        menu.run()

    except ImportError as e:
        print(f"Error importing system menu module: {e}")
        return False
    except Exception as e:
        print(f"Error running system tools: {e}")
        return False

    return True