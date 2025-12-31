"""
WiFi Selection Tool Module - SpectrumSnek 🐍📻

A tool for scanning and connecting to WiFi networks on Raspberry Pi.
"""

import os
from typing import Dict, Any

# Module metadata
MODULE_INFO = {
    "name": "📶 WiFi Network Selector",
    "description": "Scan and connect to available WiFi networks - Raspberry Pi WiFi management",
    "version": "1.0.0",
    "author": "SpectrumSnek",
    "features": [
        "Scan available WiFi networks",
        "Connect to selected network",
        "Display signal strength and security",
        "Curses-based interface"
    ]
}

def get_module_info() -> Dict[str, Any]:
    """Return module information for the main loader."""
    return MODULE_INFO

def run():
    """Main entry point for the WiFi selector."""
    try:
        from .wifi_selector import WiFiSelector

        selector = WiFiSelector()
        selector.run()

    except ImportError as e:
        print(f"Error importing WiFi selector module: {e}")
        print("Make sure nmcli is available on your system.")
        return False
    except Exception as e:
        print(f"Error running WiFi selector: {e}")
        return False

    return True