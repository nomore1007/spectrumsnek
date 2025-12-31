"""
Bluetooth Device Connector Module - SpectrumSnek 🐍📻

A tool for scanning and connecting to Bluetooth devices on Raspberry Pi.
"""

import os
from typing import Dict, Any

# Module metadata
MODULE_INFO = {
    "name": "🔵 Bluetooth Device Connector",
    "description": "Scan and connect to Bluetooth devices - Raspberry Pi Bluetooth management",
    "version": "1.0.0",
    "author": "SpectrumSnek",
    "features": [
        "Scan available Bluetooth devices",
        "Pair and connect to devices",
        "Display device info and signal strength",
        "Curses-based interface"
    ]
}

def get_module_info() -> Dict[str, Any]:
    """Return module information for the main loader."""
    return MODULE_INFO

def run():
    """Main entry point for the Bluetooth connector."""
    try:
        from .bluetooth_connector import BluetoothConnector

        connector = BluetoothConnector()
        connector.run()

    except ImportError as e:
        print(f"Error importing Bluetooth connector module: {e}")
        print("Make sure bluetooth libraries are available on your system.")
        return False
    except Exception as e:
        print(f"Error running Bluetooth connector: {e}")
        return False

    return True