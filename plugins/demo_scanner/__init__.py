"""
Demo Scanner Plugin - SpectrumSnek 🐍📻

Basic spectrum analysis demonstration without hardware.
"""

from typing import Dict, Any

# Module metadata
MODULE_INFO = {
    "name": "Spectrum Analyzer (Demo)",
    "description": "Basic spectrum analysis demonstration without hardware",
    "version": "1.0.0",
    "author": "SpectrumSnek",
    "features": [
        "Terminal-based spectrum visualization",
        "No hardware required",
        "Educational demonstration"
    ]
}

def get_module_info() -> Dict[str, Any]:
    """Return module information for the main loader."""
    return MODULE_INFO

def run():
    """Main entry point for the demo scanner."""
    try:
        import sys
        import os
        # Add current directory to path for demo_scanner import
        sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

        import demo_scanner
        # Run with default parameters
        sys.argv = ['demo_scanner', '--freq', '100', '--mode', 'spectrum', '--duration', '10']
        demo_scanner.main()
    except ImportError as e:
        print(f"Error importing demo scanner: {e}")
        print("Make sure demo_scanner.py is available.")
        return False
    except Exception as e:
        print(f"Error running demo scanner: {e}")
        return False

    return True