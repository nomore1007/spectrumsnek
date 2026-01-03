"""
Demo Scanner Module - SpectrumSnek 🐍📻
Basic spectrum analysis demonstration without hardware.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def get_module_info():
    """Get information about this module."""
    return {
        "name": "🎭 Demo Spectrum Analyzer",
        "description": "Basic spectrum analysis demonstration - no hardware required",
        "version": "1.0.0",
        "author": "SpectrumSnek"
    }

def run():
    """Run the demo scanner."""
    import demo_scanner
    demo_scanner.main()