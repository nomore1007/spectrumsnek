"""
Traditional Radio Scanner Module - SpectrumSnek 🐍📻

A traditional radio scanner that scans through user-defined frequency lists.
Supports FM with CTCSS/DCS squelch and DMR frequencies.
"""

import os
from typing import Dict, Any

# Module metadata
MODULE_INFO = {
    "name": "📻 Traditional Radio Scanner",
    "description": "Scan through user-defined frequency lists with squelch support - classic radio monitoring",
    "version": "1.0.0",
    "author": "SpectrumSnek",
    "features": [
        "XML-based frequency banks",
        "FM with CTCSS/DCS squelch",
        "DMR frequency support",
        "Sequential scanning",
        "Priority channel monitoring"
    ]
}

def get_module_info() -> Dict[str, Any]:
    """Return module information for the main loader."""
    return MODULE_INFO

def run():
    """Main entry point for the traditional radio scanner."""
    try:
        from .scanner import TraditionalScanner

        scanner = TraditionalScanner()
        scanner.run()

    except ImportError as e:
        print(f"Error importing scanner module: {e}")
        print("Make sure all dependencies are installed.")
        return False
    except Exception as e:
        print(f"Error running radio scanner: {e}")
        return False

    return True